"""A scratch copy of the Angel Attack server in a temp folder outside the repo (nothing of the real server changes)."""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

from . import winutil
from .client import JAVA

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
import rcon  # noqa: E402


class Scratch:
    def __init__(self, port=25604, rcon_port=25614, exclude_dirs=("story", "say"), keep=False, datapack=None):
        self.port, self.rcon_port, self.keep = port, rcon_port, keep
        self.datapack = datapack          # a datapack folder (holding pack.mcmeta) to use instead of datapack\angel
        self.exclude = exclude_dirs
        self.tmp = tempfile.mkdtemp(prefix="aa_visual_")
        self.srv = os.path.join(self.tmp, "server")
        self.proc = None
        self.r = None
        self.password = None

    # -------------------------------------------------------------------------------- build the copy
    def prepare(self):
        shutil.copytree(os.path.join(ROOT, "server"), self.srv,
                        ignore=shutil.ignore_patterns("angel-world", "logs", "crash-reports", "world", "*.log"))
        pf = os.path.join(self.srv, "server.properties")
        out = []
        want = {"server-port": str(self.port), "query.port": str(self.port), "rcon.port": str(self.rcon_port),
                "online-mode": "false", "enforce-secure-profile": "false", "level-name": "angel-world",
                "view-distance": "28", "simulation-distance": "12", "enable-rcon": "true", "motd": "angel visual test"}
        seen = set()
        for ln in open(pf, encoding="utf-8").read().splitlines():
            k = ln.split("=", 1)[0]
            if k in want:
                ln = f"{k}={want[k]}"
                seen.add(k)
            if k == "rcon.password":
                self.password = ln.split("=", 1)[1]
            out.append(ln)
        out += [f"{k}={v}" for k, v in want.items() if k not in seen]
        open(pf, "w", encoding="ascii").write("\n".join(out) + "\n")
        self.copy_datapack()

    def copy_datapack(self):
        dst = os.path.join(self.srv, "angel-world", "datapacks", "angel")
        os.makedirs(os.path.dirname(dst))
        src = os.path.abspath(self.datapack) if self.datapack else os.path.join(ROOT, "datapack", "angel")
        skip = {os.path.normcase(os.path.join(src, "data", "angel", "function", d)) for d in self.exclude}
        shutil.copytree(src, dst, ignore=lambda d, names: [n for n in names if os.path.normcase(os.path.join(d, n)) in skip])
        self.dp = dst

    def add_function(self, path, lines):
        """Write a helper function into the scratch datapack only (e.g. visual/hand_raised). Needs /reload to be seen."""
        f = os.path.join(self.dp, "data", "angel", "function", *path.split("/")) + ".mcfunction"
        os.makedirs(os.path.dirname(f), exist_ok=True)
        open(f, "w", encoding="utf-8", newline="\n").write("\n".join(lines) + "\n")

    # -------------------------------------------------------------------------------- run it
    def start(self, timeout=240, xmx="6G"):
        self.proc = subprocess.Popen([JAVA, "-Xms1G", f"-Xmx{xmx}", "-jar", "fabric-server-launch.jar", "nogui"], cwd=self.srv,
                                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                     creationflags=0x08000000)
        winutil.adopt(self.proc)
        rcon.SERVER = self.srv
        t0 = time.time()
        while True:
            try:
                self.r = rcon.Rcon(port=self.rcon_port, password=self.password, timeout=120)
                return
            except Exception:
                if time.time() - t0 > timeout or self.proc.poll() is not None:
                    raise RuntimeError("the scratch server did not come up; see " + self.log_path())
                time.sleep(2)

    def log_path(self):
        return os.path.join(self.srv, "logs", "latest.log")

    def log(self):
        try:
            return open(self.log_path(), encoding="utf-8", errors="replace").read()
        except OSError:
            return ""

    def cmd(self, c, retries=2):
        for i in range(retries + 1):
            try:
                return self.r.cmd(c)
            except Exception:
                if i == retries:
                    raise
                time.sleep(1)
                try:
                    self.r = rcon.Rcon(port=self.rcon_port, password=self.password, timeout=120)
                except Exception:
                    pass

    def wait_log(self, pattern, timeout, since=0):
        t0 = time.time()
        while time.time() - t0 < timeout:
            m = re.search(pattern, self.log()[since:])
            if m:
                return m
            if self.proc.poll() is not None:
                raise RuntimeError("the scratch server died; see " + self.log_path())
            time.sleep(1.0)
        raise TimeoutError("timed out waiting for log line /%s/" % pattern)

    def stop(self):
        try:
            if self.r:
                self.r.cmd("stop")
        except Exception:
            pass
        if self.proc:
            try:
                self.proc.wait(timeout=90)
            except Exception:
                winutil.kill_tree(self.proc)
        if not self.keep:
            for i in range(5):
                try:
                    shutil.rmtree(self.tmp)
                    break
                except OSError:
                    time.sleep(2)
