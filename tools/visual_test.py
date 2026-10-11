"""See the project in the real game: a scratch server, a silent desktop client, a plan of shots, PNG screenshots.

    python tools\\visual_test.py --plan gallery                 (Python of D:\\voice-assistant: numpy, pillow)
    python tools\\visual_test.py --plan my_plan.json --out work\\shots\\try1
    python tools\\visual_test.py --plan gallery --only hq_face_lights_off,cast_misato_front
    python tools\\visual_test.py --list                         the plans that exist

What it does: copies D:\\angel-attack\\server to a temp folder (port 25604, rcon 25614, online-mode=false, fresh world; the
real server is not touched), copies the datapack in (without function/story and function/say unless --with-story, so
another author's half-written files cannot disturb the pictures), runs `function angel:world/place_all`, starts the
client (work\\testgame, offline name Tester, master volume 0, the resource pack pack\\angel-resources on, FOV 90,
render distance 24, clouds/vignette/bobbing off, GUI hidden with F1), runs the plan and saves each shot as PNG of the
game window only.  At the end (or on any failure) it kills client and server and deletes the scratch server.  Every child is
also in a Windows job object, so even a crash of this script closes them.  Plan format: tools\\visual\\plan.py.
"""
import argparse
import atexit
import ctypes
import json
import os
import socket
import sys
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import numpy as np  # noqa: E402
from visual import client as cl  # noqa: E402
from visual import hqdata, plan as planmod, winutil  # noqa: E402
from visual.server import Scratch  # noqa: E402

GAME = os.path.join(ROOT, "work", "testgame")
PIDFILE = os.path.join(ROOT, "work", "visual_pids.json")
T0 = time.time()


def log(*a):
    print("[%5.0fs]" % (time.time() - T0), *a, flush=True)


def port_free(p):
    s = socket.socket()
    try:
        s.bind(("127.0.0.1", p))
        return True
    except OSError:
        return False
    finally:
        s.close()


def kill_stale():
    """Processes a crashed earlier run of this tool left behind (pids it wrote down; only if still java)."""
    if not os.path.exists(PIDFILE):
        return
    import subprocess
    for pid in json.load(open(PIDFILE)):
        out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/FO", "CSV", "/NH"], capture_output=True, text=True).stdout
        if "java" in out.lower():
            log("killing stale java pid", pid)
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], capture_output=True)
    os.remove(PIDFILE)


def small(img):
    g = np.asarray(img.convert("L").resize((160, 90)), dtype=np.float32)
    return g


class Session:
    def __init__(self, a):
        self.a = a
        self.srv = None
        self.client = None
        self.hwnd = None
        self.manifest = []

    # ---------------------------------------------------------------- picture taking
    def frame(self):
        if self.client.poll() is not None:
            raise RuntimeError("the game client closed; see work\\testgame\\client.log")
        if not self.hwnd or not winutil.user32.IsWindow(self.hwnd):
            self.hwnd = winutil.window_of_pid_tree({self.client.pid})
        return winutil.grab(self.hwnd) if self.hwnd else None

    def settle(self, minimum, maximum):
        """Wait the minimum, then until two pictures 0.6 s apart are the same (chunks and lighting finished)."""
        time.sleep(minimum)
        t0 = time.time()
        prev, quiet = None, 0
        img = None
        while True:
            img = self.frame()
            if img is not None:
                cur = small(img)
                if prev is not None:
                    d = float(np.abs(cur - prev).mean())
                    quiet = quiet + 1 if d < 0.8 else 0
                    if quiet >= 3:
                        return img, round(time.time() - t0 + minimum, 1), True
                prev = cur
            if time.time() - t0 > maximum:
                return img, round(time.time() - t0 + minimum, 1), False
            time.sleep(0.6)

    def shoot(self, name, out, minimum, maximum):
        img, waited, stable = self.settle(minimum, maximum)
        if img is None:
            raise RuntimeError("no picture of the game window")
        path = os.path.join(out, name + ".png")
        img.save(path)
        flat = float(np.asarray(img.convert("L"), dtype=np.float32).std())
        log(f"shot {name}  ({img.width}x{img.height}, waited {waited}s{'' if stable else ', NOT STABLE'}, contrast {flat:.0f})")
        return dict(name=name, file=path, waited=waited, stable=stable, contrast=round(flat, 1))

    # ---------------------------------------------------------------- the run
    def run(self):
        a = self.a
        p = planmod.load(a.plan)
        out = os.path.abspath(a.out or os.path.join(ROOT, "work", "shots", p.get("name", "plan")))
        os.makedirs(out, exist_ok=True)
        fov = a.fov or p.get("fov", 90)
        render = a.render or p.get("render", 24)
        width, height = a.width or p.get("width", 1600), a.height or p.get("height", 900)
        shots = p["shots"]
        if a.only:
            wanted = set(a.only.split(","))
            shots = [s for s in shots if s["name"] in wanted]
            if not shots:
                sys.exit("--only matches no shot of the plan")
        for pt in (25604, 25614):
            if not port_free(pt):
                sys.exit(f"port {pt} is busy (another visual test running?)")

        log("scratch server")
        self.srv = Scratch(exclude_dirs=() if a.with_story else ("story", "say"), keep=a.keep_server, datapack=a.datapack)
        self.srv.prepare()
        if a.world_build:
            self.build_world()
        for path, lines in hqdata.functions().items():
            self.srv.add_function(path, lines)
        self.srv.start()
        json.dump([self.srv.proc.pid], open(PIDFILE, "w"))
        run = planmod.Runner(self.srv, log)
        mark = len(self.srv.log())
        self.srv.cmd("function angel:world/place_all")
        log("placing the four sets ...")
        self.srv.wait_log(r"every set is placed", 1500, since=mark)
        log(f"placed ({self.srv.log()[mark:].count('placed')} messages)")

        log("client")
        cl.prepare(GAME, os.path.join(ROOT, "pack", "angel-resources"), fov, render, a.gamma)
        self.client = cl.launch(GAME, self.srv.port, width, height)
        json.dump([self.srv.proc.pid, self.client.pid], open(PIDFILE, "w"))
        t0 = time.time()
        while cl.NAME not in self.srv.cmd("list"):
            if time.time() - t0 > 300 or self.client.poll() is not None:
                raise RuntimeError("the test client did not join; see work\\testgame\\client.log")
            time.sleep(2)
        log("joined")
        run.cmd(f"gamemode spectator {cl.NAME}")
        run.run({"tp": [37.5, 80, 128.5], "yaw": -90, "pitch": 0})
        time.sleep(8)
        self.hwnd = winutil.window_of_pid_tree({self.client.pid})
        if not self.hwnd:
            raise RuntimeError("no game window")
        if a.monitor == "left":
            vleft = winutil.user32.GetSystemMetrics(76)
            if vleft < 0:
                winutil.move_window(self.hwnd, vleft + 10, 10)
        if not a.gui:
            winutil.post_key(self.hwnd, winutil.VK_F1, winutil.SC_F1)
        time.sleep(2)

        for s in p.get("setup", []):
            run.run(s, "setup")
        log(f"{len(shots)} shots -> {out}")
        for i, shot in enumerate(shots):
            name = shot["name"]
            where = name
            t1 = time.time()
            try:
                for s in shot.get("steps", []):
                    run.run(s, where)
                rec = self.shoot(name, out, shot.get("settle", 4), shot.get("max", 25))
                rec["steps"] = shot.get("steps", [])
                self.manifest.append(rec)
            except Exception as e:
                if isinstance(e, (RuntimeError, ConnectionError)) and self.client.poll() is not None:
                    raise
                log(f"shot {name} FAILED: {e}")
                self.manifest.append(dict(name=name, error=str(e)))
            if time.time() - T0 > a.max_minutes * 60:
                log("global time limit reached; stopping")
                break
        json.dump(dict(plan=p.get("name"), shots=self.manifest,
                       warnings=[dict(shot=w, cmd=c, out=o) for w, c, o in run.warnings],
                       queries=[dict(shot=w, cmd=c, out=o) for w, c, o in run.queries]),
                  open(os.path.join(out, "manifest.json"), "w"), indent=1)
        self.save_logs(out)
        log(f"done: {sum('file' in m for m in self.manifest)} pictures, {len(run.warnings)} command warnings")

    def build_world(self):
        """Build the world pack (tools\\world\\build.py --out <temp>) fresh from the sets as they are now and lay it over the
        scratch datapack, so pictures show the current worldgen without touching datapack\\angel; its anchors are used too."""
        import shutil
        import subprocess
        import tempfile
        tmp = tempfile.mkdtemp(prefix="aa_world_")
        out = os.path.join(tmp, "pack", "angel")
        log("building the world pack ...")
        r = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "world", "build.py"), "--out", out],
                           capture_output=True, text=True, cwd=os.path.join(ROOT, "tools", "world"))
        if r.returncode:
            raise RuntimeError("world build failed:\n" + r.stdout[-2500:] + r.stderr[-1500:])
        shutil.copytree(out, self.srv.dp, dirs_exist_ok=True)
        planmod.ANCHORS = os.path.join(tmp, "pack", "anchors.json")
        log("world pack laid over the scratch datapack")

    def save_logs(self, out):
        """Keep the scratch server's log and the client's log next to the pictures (the scratch folder is deleted)."""
        import re
        import shutil
        try:
            text = self.srv.log()
            open(os.path.join(out, "server.log"), "w", encoding="utf-8").write(text)
            bad = [l for l in text.splitlines() if re.search(r"\[(WARN|ERROR)\]|Exception|Failed", l)]
            open(os.path.join(out, "server_problems.log"), "w", encoding="utf-8").write("\n".join(bad) + "\n")
            log(f"server log: {len(bad)} WARN/ERROR lines (server_problems.log)")
        except Exception as e:
            log("could not save the server log:", e)
        try:
            shutil.copy(os.path.join(GAME, "client.log"), os.path.join(out, "client.log"))
        except OSError:
            pass

    def close(self):
        winutil.kill_tree(self.client)
        if self.srv:
            self.srv.stop()
        try:
            os.remove(PIDFILE)
        except OSError:
            pass


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--plan", help="plan file, or the name of a plan in tools\\visual\\plans")
    ap.add_argument("--out", help="output folder (default work\\shots\\<plan name>)")
    ap.add_argument("--only", help="comma-separated shot names to take")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--fov", type=int, help="vertical field of view in degrees (default 90)")
    ap.add_argument("--render", type=int, help="render distance in chunks (default 24)")
    ap.add_argument("--width", type=int)
    ap.add_argument("--height", type=int)
    ap.add_argument("--gamma", type=float, default=0.5, help="brightness option, 0.5 is the game's default (moody)")
    ap.add_argument("--gui", action="store_true", help="leave the GUI on (no F1)")
    ap.add_argument("--with-story", action="store_true", help="keep function/story and function/say in the scratch datapack")
    ap.add_argument("--keep-server", action="store_true", help="do not delete the scratch server folder at the end")
    ap.add_argument("--world-build", action="store_true", dest="world_build",
                    help="build the world pack from tools\\world now (build.py --out <temp>) and lay it over the scratch datapack")
    ap.add_argument("--datapack", help="use this datapack folder (the one holding pack.mcmeta) instead of datapack\\angel; "
                                       "for pictures of a test build that is not in the repo")
    ap.add_argument("--monitor", choices=["left", "primary"], default="left",
                    help="where the game window sits ('left': on a monitor left of the primary if there is one)")
    ap.add_argument("--max-minutes", type=float, default=60)
    a = ap.parse_args()
    if a.list:
        for f in sorted(os.listdir(planmod.PLANS)):
            print(f[:-5])
        return
    if not a.plan:
        ap.error("--plan is required")
    kill_stale()
    s = Session(a)
    atexit.register(s.close)
    try:
        s.run()
    except BaseException:
        traceback.print_exc()
        raise SystemExit(1)
    finally:
        s.close()
        atexit.unregister(s.close)


if __name__ == "__main__":
    main()
