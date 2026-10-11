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


def window_rect(hwnd):
    rc = (ctypes.c_long * 4)()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), rc)
    return tuple(rc)


def grab(hwnd):
    """The window's own client picture as a PIL RGB image (PrintWindow: not brought to the front, nothing else captured)."""
    from PIL import Image
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
    return Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")


def post_key(hwnd, vk, scan):
    """Send a key press to the window without focusing it (GLFW reads it from the window's own message queue)."""
    down = 1 | (scan << 16)
    up = down | (1 << 30) | (1 << 31)
    user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0100, vk, down)
    time.sleep(0.08)
    user32.PostMessageW(ctypes.c_void_p(hwnd), 0x0101, vk, up)


VK_F1, SC_F1 = 0x70, 0x3B
