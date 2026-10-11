"""Place the world on a live scratch server and check it: the pack loads, the chain completes, every biome is applied.

    python livecheck.py                      build the world pack into a temp folder, start a scratch server on ports
                                             25607/25617 (a copy of D:\\angel-attack\\server in a temp folder: the real server
                                             is never touched), place all four sets, probe the biomes, report, stop, delete
    python livecheck.py --pack DIR           use this datapack folder (holding pack.mcmeta) instead of building one
    python livecheck.py --keep               leave the scratch server folder (and print its path)
    python livecheck.py --extra "cmd" ...    run more server commands at the end and print their answers

Use the Python of the D:\\voice-assistant environment. Prints the time each set's placement took (with its biome stages).
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
for p in (TOOLS, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import layout  # noqa: E402
from visual.server import Scratch  # noqa: E402

PY = sys.executable
NOISE = re.compile(r"Perflib|SystemReport|oshi|Failed to get system info|OFFLINE/INSECURE|authenticate|online-mode|hackers|"
                   r"Win32Exception|Advapi32Util|knot//|^\s+at |jna|NullPointerException|EntityStorage|Serialization errors|Mannequin")


def build_pack(tmp):
    out = os.path.join(tmp, "pack", "angel")
    r = subprocess.run([PY, os.path.join(HERE, "build.py"), "--out", out], capture_output=True, text=True, cwd=HERE)
    if r.returncode:
        print(r.stdout[-3000:], r.stderr[-2000:])
        sys.exit("build failed")
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pack")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--extra", nargs="*", default=[])
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="aa_livecheck_")
    pack = a.pack or build_pack(tmp)
    srv = Scratch(port=25607, rcon_port=25617, keep=a.keep, datapack=pack)
    ok = True
    try:
        print("scratch server in", srv.tmp)
        srv.prepare()
        t0 = time.time()
        srv.start()
        print(f"server up in {time.time() - t0:.0f}s")
        mark = len(srv.log())
        print(srv.cmd("function angel:world/init"))
        t1 = time.time()
        srv.cmd("function angel:world/place_all")
        srv.wait_log(r"every set is placed", 900, since=mark)
        total = time.time() - t1
        log = srv.log()[mark:]
        print(f"place_all took {total:.1f}s")
        for ln in log.splitlines():
            if "[angel]" in ln:
                print("  " + ln.split("]: ", 1)[-1])
        # independent probes: load chunks round points, ask the server which biome is there
        print("\nbiome probes (by hand):")
        for name, (o, s) in layout.SETS.items():
            pts = [(o[0] + 1, o[1] + 10, o[2] + 1), (o[0] + s[0] // 2, o[1] + s[1] // 2, o[2] + s[2] // 2),
                   (o[0] + s[0] - 2, o[1] + s[1] - 2, o[2] + s[2] - 2), (o[0] - 50, o[1] + 5, o[2] + s[2] // 2),
                   (o[0] + s[0] + 50, o[1] + 5, o[2] + s[2] // 2), (o[0] - 120, o[1] + 5, o[2] + s[2] // 2),
                   (o[0] + s[0] // 2, o[1] + s[1] + 120, o[2] + s[2] // 2)]
            for x, y, z in pts:
                srv.cmd(f"forceload add {x} {z}")
            time.sleep(3)
            for x, y, z in pts:
                res = []
                for b in ("void", "outskirts", "city", "geofront", "hq"):
                    out = srv.cmd(f"execute in minecraft:overworld if biome {x} {y} {z} angel:{b}")
                    if "passed" in out.lower():
                        res.append(b)
                print(f"  {name:9s} ({x:5d},{y:4d},{z:5d}): {','.join(res) or 'none'}")
        for c in a.extra:
            print(f"> {c}\n{srv.cmd(c)}")
        text = srv.log()
        bad = [l for l in text.splitlines() if re.search(r"\[(WARN|ERROR)\]|Exception|Failed|rror", l) and not NOISE.search(l)]
        print(f"\nserver log: {len(bad)} suspicious lines")
        for l in bad[:25]:
            print("  " + l[:220])
        ok = not bad and "BIOME CHECK FAILED" not in text
    finally:
        srv.stop()
        shutil.rmtree(tmp, ignore_errors=True)
    print("OK" if ok else "PROBLEMS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
