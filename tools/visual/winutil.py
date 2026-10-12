"""Windows helpers for the visual test: a job object that kills our children if we die, finding the game window,
copying its picture, sending it a key without focusing it."""
import ctypes
import ctypes.wintypes as wt
import subprocess
import time

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

for _f in (user32.GetDC, gdi32.CreateCompatibleDC, gdi32.CreateCompatibleBitmap, gdi32.SelectObject):
    _f.restype = ctypes.c_void_p
kernel32.OpenProcess.restype = ctypes.c_void_p
kernel32.CreateJobObjectW.restype = ctypes.c_void_p
user32.SetProcessDPIAware()

# ------------------------------------------------------------------ job object: every child dies with this process


class _BasicLimit(ctypes.Structure):
    _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wt.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wt.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wt.DWORD), ("SchedulingClass", wt.DWORD)]


class _IoCounters(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint64) for n in ("a", "b", "c", "d", "e", "f")]


class _ExtLimit(ctypes.Structure):
    _fields_ = [("Basic", _BasicLimit), ("Io", _IoCounters), ("ProcessMemoryLimit", ctypes.c_size_t),
                ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                ("PeakJobMemoryUsed", ctypes.c_size_t)]


_job = None


def job():
    global _job
    if _job is None:
        _job = kernel32.CreateJobObjectW(None, None)
        info = _ExtLimit()
        info.Basic.LimitFlags = 0x2000          # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        kernel32.SetInformationJobObject(ctypes.c_void_p(_job), 9, ctypes.byref(info), ctypes.sizeof(info))
    return _job


def adopt(proc):
    """Put a subprocess.Popen into the kill-on-close job."""
    h = kernel32.OpenProcess(0x1F0FFF, False, proc.pid)
    kernel32.AssignProcessToJobObject(ctypes.c_void_p(job()), ctypes.c_void_p(h))


def kill_tree(proc):
    """Kill a Popen and everything under it (only our own pid tree)."""
    if proc is None or proc.poll() is not None:
        return
    subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        proc.wait(timeout=15)
    except Exception:
        pass


# ------------------------------------------------------------------ the game window


def window_of_pid_tree(pids):
    """Visible top-level window whose title starts with 'Minecraft' and which belongs to one of pids."""
    found = []

    @ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)
    def each(hwnd, _):
        if not user32.IsWindowVisible(hwnd):
            return True
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        buf = ctypes.create_unicode_buffer(200)
        user32.GetWindowTextW(hwnd, buf, 200)
        if pid.value in pids and buf.value.startswith("Minecraft"):
            found.append(hwnd)
        return True

    user32.EnumWindows(each, 0)
    return found[0] if found else None


def client_size(hwnd):
    rc = (ctypes.c_long * 4)()
    user32.GetClientRect(ctypes.c_void_p(hwnd), rc)
    return rc[2], rc[3]


def move_window(hwnd, x, y):
    """Move only; no resize, no activation, no z-order change."""
    user32.SetWindowPos(ctypes.c_void_p(hwnd), None, x, y, 0, 0, 0x0001 | 0x0004 | 0x0010)


def keep_visible(hwnd):
    """With no second monitor the game window would sit under the user's other windows, and an occluded GL window is grabbed as black:
    put it at the bottom right of the primary screen, topmost, without taking the focus."""
    w, h = client_size(hwnd)
    sw, sh = user32.GetSystemMetrics(0), user32.GetSystemMetrics(1)
    x, y = max(0, sw - w - 20), max(0, sh - h - 80)
    user32.SetWindowPos(ctypes.c_void_p(hwnd), ctypes.c_void_p(-1), x, y, 0, 0, 0x0001 | 0x0010)     # NOSIZE | NOACTIVATE, HWND_TOPMOST


def window_rect(hwnd):
    rc = (ctypes.c_long * 4)()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), rc)
    return tuple(rc)


SHOT_DIR = None          # the game's own screenshots folder (set by the tools): used when the window cannot be copied
PW_BROKEN = False        # True once PrintWindow has returned black while the game's own screenshot showed a picture


def _idle_ms():
    class LII(ctypes.Structure):
        _fields_ = [("cb", wt.UINT), ("t", wt.DWORD)]
    li = LII()
    li.cb = ctypes.sizeof(li)
    user32.GetLastInputInfo(ctypes.byref(li))
    return kernel32.GetTickCount() - li.t


def foreground(hwnd):
    """Bring the game window to the front (the ALT trick makes Windows allow it); never while the user is typing."""
    if user32.GetForegroundWindow() == hwnd:
        return True
    for _ in range(8):
        if _idle_ms() > 1500:
            break
        time.sleep(0.5)
    user32.keybd_event(0x12, 0, 0, 0)
    user32.SetForegroundWindow(ctypes.c_void_p(hwnd))
    user32.keybd_event(0x12, 0, 2, 0)
    time.sleep(0.4)
    return user32.GetForegroundWindow() == hwnd


def press(hwnd, vk, scan=0):
    """A real key press (SDL does not read posted messages), sent only while the game is the foreground window."""
    if not foreground(hwnd):
        return False
    user32.keybd_event(vk, scan, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, scan, 2, 0)
    return True


def game_screenshot(hwnd, timeout=5.0):
    """The game's own F2 screenshot as a PIL image (the window itself may paint black in the compositor: a GL window that cannot be copied)."""
    import glob
    import os
    from PIL import Image
    if not SHOT_DIR:
        return None
    before = set(glob.glob(os.path.join(SHOT_DIR, "*.png")))
    if not press(hwnd, 0x71, 0x3C):
        return None
    t0 = time.time()
    while time.time() - t0 < timeout:
        new = set(glob.glob(os.path.join(SHOT_DIR, "*.png"))) - before
        if new:
            f = sorted(new)[-1]
            for _ in range(10):
                try:
                    im = Image.open(f)
                    im.load()
                    im = im.convert("RGB")
                    break
                except Exception:
                    time.sleep(0.15)
            else:
                return None
            for g in new:
                try:
                    os.remove(g)
                except OSError:
                    pass
            return im
        time.sleep(0.08)
    return None


def _uniform(img):
    return all(lo == hi for lo, hi in img.getextrema())


def grab(hwnd):
    """The window's own client picture as a PIL RGB image: PrintWindow (not brought to the front, nothing else captured); if the window paints
    black in the compositor (it does on this machine since the second monitor went), the game's own screenshot (F2) instead."""
    global PW_BROKEN
    from PIL import Image
    if PW_BROKEN and SHOT_DIR:
        im = game_screenshot(hwnd)
        if im is not None:
            return im
    w, h = client_size(hwnd)
    if w < 16 or h < 16:
        return None
    hdc = user32.GetDC(ctypes.c_void_p(hwnd))
    mem = gdi32.CreateCompatibleDC(ctypes.c_void_p(hdc))
    bmp = gdi32.CreateCompatibleBitmap(ctypes.c_void_p(hdc), w, h)
    gdi32.SelectObject(ctypes.c_void_p(mem), ctypes.c_void_p(bmp))
    user32.PrintWindow(ctypes.c_void_p(hwnd), ctypes.c_void_p(mem), 3)     # client area, full content
    header = (ctypes.c_uint32 * 10)(40, w, ctypes.c_uint32(-h).value, 1 | (32 << 16), 0, 0, 0, 0, 0, 0)
    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(ctypes.c_void_p(mem), ctypes.c_void_p(bmp), 0, h, buf, header, 0)
    gdi32.DeleteObject(ctypes.c_void_p(bmp))
    gdi32.DeleteDC(ctypes.c_void_p(mem))
    user32.ReleaseDC(ctypes.c_void_p(hwnd), ctypes.c_void_p(hdc))
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    if SHOT_DIR and _uniform(img):
        alt = game_screenshot(hwnd)
        if alt is not None:
            if not _uniform(alt):
                PW_BROKEN = True
            return alt
    return img


def post_key(hwnd, vk, scan):
    """Send a key press to the window without focusing it (GLFW reads it from the window's own message queue)."""
    down = 1 | (scan << 16)
    up = down | (1 << 30) | (1 << 31)
    user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0100, vk, down)
    time.sleep(0.08)
    user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0101, vk, up)


VK_F1, SC_F1 = 0x70, 0x3B
