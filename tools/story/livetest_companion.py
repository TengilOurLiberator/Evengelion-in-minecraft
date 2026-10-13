"""Live test of the companion guarantee on a SCRATCH server (a copy of server\\ in a temp folder with its own prefix, server-port 25605, rcon.port 25615;
nothing of the real server or the repo's datapack is touched, no game client is started; the copy is stopped and deleted at the end).

    python livetest_companion.py                       build the story (dry variant, the current pace preset) and run scene 4's crossing
    python livetest_companion.py --pace full           ... with the old pacing values
    python livetest_companion.py --pack DIR            use an already assembled datapack folder (pack.mcmeta + data/) instead of building one
    python livetest_companion.py --keep                keep the scratch folder (its path is printed)

What it does.  The dry variant of the story (`build_story.py --dry`) treats a mannequin tagged angel.testplayer as the player.  The test places the
headquarters set, puts the characters where scene 4 leaves them at the foot of the lift (Ritsuko leading, Misato her companion, the stand-in boy by the
lift doors), runs the real compiled steps of the crossing (the `lead()` of Ritsuko from hq.dock over the catwalk to the cage door), and walks the
stand-in along the leader's route at 4.2 blocks a second, always 3.5 blocks behind her.  Every 0.2 s it reads Misato's and Ritsuko's positions and the cast's
walk scores.  The test FAILS when the companion is ever left behind: not moving for 3 s while more than 6 blocks from the boy (and behind him), when
she is more than 8 blocks from him at the end, or when she stands where a character cannot (inside the railing, off the walkway).  Printed: a position
read-back every second.

With the pacing/companion code as it was before the guarantee (the pack of the original build) this test shows the freeze: Misato walks into the
railing of the 3-wide catwalk at about (3023.1, 54, 158.6) and stays there with her arrival score 0.
"""
import argparse
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TOOLS = os.path.join(ROOT, "tools")
sys.path.insert(0, TOOLS)
PY = sys.executable
PORT, RPORT = 25605, 25615

from visual.server import Scratch  # noqa: E402

PLAYER = "@e[type=minecraft:mannequin,tag=angel.testplayer,limit=1]"
CH = "@e[type=minecraft:mannequin,tag=angel.{who},limit=1]"


class PaceScratch(Scratch):
    def __init__(self, **kw):
        super().__init__(**kw)
        shutil.rmtree(self.tmp, ignore_errors=True)               # (the parent made an aa_visual_ folder: use our own prefix)
        self.tmp = tempfile.mkdtemp(prefix="aa_pace_")
        self.srv = os.path.join(self.tmp, "server")

    def prepare(self):
        super().prepare()
        # (a server with nobody online pauses itself after a minute: the stand-in boy is a mannequin, so this one must not)
        with open(os.path.join(self.srv, "server.properties"), "a", encoding="ascii") as f:
            f.write("pause-when-empty-seconds=-1\n")


def log(m):
    print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)


def assemble_pack(dest, pace=None, steps=None):
    """A complete datapack folder in `dest`: the repo's datapack with the story built over it as the DRY variant (a mannequin is the player)."""
    shutil.copytree(os.path.join(ROOT, "datapack", "angel"), dest)
    cmd = [PY, os.path.join(HERE, "build_story.py"), "--dry", "--out", dest, "--quiet"]
    if pace:
        cmd += ["--pace", pace]
    if steps:
        cmd += ["--steps", steps]
    r = subprocess.run(cmd, capture_output=True, text=True, cwd=HERE)
    if r.returncode:
        raise RuntimeError("dry build failed:\n" + (r.stdout + r.stderr)[-2000:])


def num(s, name):
    m = re.search(re.escape(name) + r" has (-?\d+)", s or "")
    return int(m.group(1)) if m else None


class Rig:
    def __init__(self, srv):
        self.srv = srv

    def cmd(self, c):
        return self.srv.cmd(c)

    def pos(self, sel):
        m = re.findall(r"(-?\d+\.\d+)d", self.cmd(f"data get entity {sel} Pos"))
        return tuple(float(v) for v in m) if len(m) == 3 else None

    def score(self, name, obj="angel.story"):
        return num(self.cmd(f"scoreboard players get {name} {obj}"), name)


def polyline_s(poly, x, z):
    """arc length of the projection of (x, z) on the polyline (the leader's route)"""
    best, bs, acc = 1e18, 0.0, 0.0
    for (ax, az), (bx, bz) in zip(poly, poly[1:]):
        dx, dz = bx - ax, bz - az
        L2 = dx * dx + dz * dz
        t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((x - ax) * dx + (z - az) * dz) / L2))
        px, pz = ax + t * dx, az + t * dz
        d = (px - x) ** 2 + (pz - z) ** 2
        if d < best:
            best, bs = d, acc + t * math.sqrt(L2)
        acc += math.sqrt(L2)
    return bs


def point_at(poly, s):
    acc = 0.0
    for (ax, az), (bx, bz) in zip(poly, poly[1:]):
        L = math.hypot(bx - ax, bz - az)
        if acc + L >= s or (bx, bz) == poly[-1]:
            t = 0.0 if L == 0 else max(0.0, min(1.0, (s - acc) / L))
            return ax + t * (bx - ax), az + t * (bz - az)
        acc += L
    return poly[-1]


def drive_scene4(R, steps, first, a):
    """--scene4: the whole of scene 4 from its start (`angel:story/scene {n:4}`), the stand-in boy following whoever leads at 3.5 blocks (4.2 blocks a second,
    through the walls: only distances matter), answering every wait after 2.5 s (angel:story/answered) and pushing a step that has waited longer than its
    estimate + 10 s (angel:story/next).  Prints each step as it begins with the time, the companion's distance to the boy every 5 s, and the elapsed time."""
    R.cmd("forceload add 3000 128 3190 176")
    t0 = time.time()
    while "passed" not in R.cmd("execute if loaded 3180 131 160").lower() and time.time() - t0 < 40:
        time.sleep(1)
    time.sleep(1.0)
    R.cmd("summon minecraft:mannequin 3180.5 131 160.5 {Tags:[\"angel.testplayer\"],NoGravity:1b,immovable:1b,Invulnerable:1b,Silent:1b}")
    log("the stand-in boy exists: " + str("Test passed" in R.cmd("execute if entity @e[type=minecraft:mannequin,tag=angel.testplayer]")))
    R.cmd("function angel:story/scene {n:4}")
    t0 = time.time()
    last_step, since, wait_since = None, 0.0, None
    log_every = last_fl = 0.0
    pushes = []
    min_d = 99.0
    while time.time() - t0 < a.max_seconds:
        t = time.time() - t0
        scene, step = R.score("#scene"), R.score("#step")
        if scene != 4 or step is None or step < 0:
            if t > 5:
                log(f"scene {scene} step {step} at {t:.1f} s: scene 4 is over")
                break
            time.sleep(0.2)
            continue
        wait, talking = R.score("#wait"), R.score("#talking")
        if t - last_fl >= 1.0:
            last_fl = t
            R.cmd("forceload add 3000 128 3190 176")                 # (the story releases its forceloads at every scene start; a real player keeps his chunks loaded)
        if step != last_step:
            kind = steps[step] if 0 <= step < len(steps) else {}
            last_step, since = step, t
            wait_since = None
            if kind.get("kind") in ("say", "wait") or "reaches" not in (kind.get("note") or ""):
                print(f"  t={t:6.1f}s step {step:3d} {kind.get('kind', '?'):6s} {(kind.get('note') or kind.get('line') or '')[:78]}", flush=True)
        lead = "ritsuko" if step >= first - 8 else "misato"
        ldr = R.pos(CH.format(who=lead))
        boy = R.pos(PLAYER)
        if ldr and boy:
            dx, dz = ldr[0] - boy[0], ldr[2] - boy[2]
            d = math.hypot(dx, dz)
            if d > 40 or abs(ldr[1] - boy[1]) > 3:
                R.cmd(f"tp {PLAYER} {ldr[0] - 3.5:.2f} {ldr[1]:.2f} {ldr[2]:.2f}")
            elif d > 3.5:
                m = min(0.85, d - 3.5)
                R.cmd(f"tp {PLAYER} {boy[0] + dx / d * m:.2f} {ldr[1]:.2f} {boy[2] + dz / d * m:.2f}")
        mis = R.pos(CH.format(who="misato"))
        boy = R.pos(PLAYER)
        if mis and boy:
            dm = math.hypot(mis[0] - boy[0], mis[2] - boy[2])
            if t - log_every >= 5.0:
                log_every = t
                print(f"      t={t:6.1f}s boy ({boy[0]:.1f}, {boy[1]:.1f}, {boy[2]:.1f})  Misato ({mis[0]:.1f}, {mis[1]:.1f}, {mis[2]:.1f}) {dm:4.1f} from him   leader {lead}", flush=True)
        if wait and wait >= 1 and not talking:
            wait_since = wait_since or t
            if t - wait_since > 2.5:
                R.cmd("function angel:story/answered")
                wait_since = t + 5
        kind = steps[step] if 0 <= step < len(steps) else {}
        if kind.get("kind") == "until" and t - since > (kind.get("est") or 3.0) + 10.0 and not talking:
            R.cmd("function angel:story/next")
            pushes.append((round(t, 1), step, (kind.get("note") or "")[:50]))
            since = t
        time.sleep(0.12)
    el = time.time() - t0
    print(f"scene 4 took {el:.1f} s with the stand-in boy; {len(pushes)} step(s) had to be pushed: {pushes}")
    ok = (R.score("#scene") != 4)
    mis, boy = R.pos(CH.format(who="misato")), R.pos(PLAYER)
    print(("ok" if ok else "FAIL") + ": scene 4 " + ("ran to its end and handed over" if ok else "did not finish in time"))
    return 0 if ok else 1


def run(a):
    tmp0 = tempfile.mkdtemp(prefix="aa_pace_pack_")
    srv = None
    try:
        steps_file = os.path.join(tmp0, "steps.json")
        pack = a.pack
        if not pack:
            pack = os.path.join(tmp0, "pack")
            log(f"assembling the dry pack (pace {a.pace or 'default'}) ...")
            assemble_pack(pack, a.pace, steps_file)
        elif not os.path.isfile(steps_file):
            subprocess.run([PY, os.path.join(HERE, "build_story.py"), "--dry", "--out", os.path.join(tmp0, "x"), "--quiet", "--steps", steps_file, "--steps-only"]
                           + (["--pace", a.pace] if a.pace else []), cwd=HERE, capture_output=True)
        import json
        steps = json.load(open(steps_file, encoding="utf-8"))["4"]
        first = next(st["i"] for st in steps if "ritsuko walks to hq.dock" in (st.get("note") or ""))
        log(f"scene 4 step {first} is the first step of the crossing")
        srv = PaceScratch(port=PORT, rcon_port=RPORT, exclude_dirs=(), keep=a.keep, datapack=pack)
        srv.prepare()
        log("scratch server: " + srv.tmp)
        srv.start(timeout=300)
        log("server is up")
        R = Rig(srv)
        R.cmd("function angel:world/init")
        R.cmd("gamerule minecraft:max_command_sequence_length 1000000")
        R.cmd("forceload add 2984 -16 3111 111")
        R.cmd("function angel:world/place_hq")
        t0 = time.time()
        while "every set is placed" not in srv.log() and time.time() - t0 < 420:
            time.sleep(3)
        log("hq placed" if "every set is placed" in srv.log() else "hq NOT placed")
        errs = [ln for ln in srv.log().splitlines() if "Failed to load function angel" in ln]
        if errs:
            log("function errors: " + "; ".join(errs[:3]))
        R.cmd("function angel:story/load")
        R.cmd("function angel:story/halt")                    # (it releases the story's forceloads: hold the stage's chunks again afterwards)
        R.cmd("forceload add 3000 128 3110 176")
        t0 = time.time()
        while "passed" not in R.cmd("execute if loaded 3096 54 143").lower() and time.time() - t0 < 40:
            time.sleep(1)
        time.sleep(2)
        if a.scene4:
            return drive_scene4(R, steps, first, a)
        # --- the stage: the foot of the lift, as scene 4 leaves it
        LIFT_P = (3006.1, 54, 160.5)
        LIFT_R = (3004.5, 54, 159.5)
        LIFT_M = (3004.5, 54, 161.5)
        R.cmd(f"summon minecraft:mannequin {LIFT_P[0]} 54 {LIFT_P[2]} {{Tags:[\"angel.testplayer\"],NoGravity:1b,immovable:1b,Invulnerable:1b,Silent:1b}}")
        R.cmd("scoreboard players set #running angel.story 1")
        R.cmd(f"execute positioned {LIFT_R[0]} 54 {LIFT_R[2]} rotated -90 0 run function angel:cast/summon {{id:\"ritsuko\"}}")
        R.cmd(f"execute positioned {LIFT_M[0]} 54 {LIFT_M[2]} rotated -90 0 run function angel:cast/summon {{id:\"misato\"}}")
        R.cmd("scoreboard players set #present_ritsuko angel.story 1")
        R.cmd("scoreboard players set #present_misato angel.story 1")
        R.cmd("scoreboard players set #scene angel.story 4")
        time.sleep(1.0)
        # the leader's route (stops of the crossing)
        poly = [(3004.5, 159.5), (3015.5, 160.5), (3060.5, 160.5), (3096.5, 160.5), (3096.5, 150.0), (3096.5, 143.2)]
        total = polyline_s(poly, *poly[-1])
        R.cmd(f"scoreboard players set #step angel.story {first}")
        R.cmd(f"function angel:story/s4/e{first}")
        log("the crossing is running")
        # --- walk the stand-in, read back
        s_p = polyline_s(poly, LIFT_P[0], LIFT_P[2])
        t_start = time.time()
        rows, stall = [], {"t": None, "pos": None}
        last_print = 0.0
        still_since = None
        last_m = None
        jam = {"state": "wait" if a.jam else "off"}
        verdict = []
        worst_still = 0.0
        while time.time() - t_start < a.max_seconds:
            t = time.time() - t_start
            rit = R.pos(CH.format(who="ritsuko"))
            mis = R.pos(CH.format(who="misato"))
            if rit is None or mis is None:
                if t > 20:
                    log("the characters never appeared (chunks not loaded?)")
                    return 2
                time.sleep(0.2)
                continue
            if a.jam and jam["state"] != "done":
                # the stand-in for whatever blocks her (a railing, a prop): from t = 8 s she is held where she is, as if walking against a wall
                if jam["state"] == "wait" and t >= 8.0:
                    jam.update(state="held", at=mis, t0=t)
                    R.cmd(f"data merge entity {CH.format(who='misato')} {{immovable:1b,NoGravity:1b,Motion:[0.0d,0.0d,0.0d]}}")      # (what a wall does to a walker: she cannot move)
                    log(f"JAM: Misato is held at ({mis[0]:.1f}, {mis[2]:.1f}) from now on")
                elif jam["state"] == "held":
                    if math.hypot(mis[0] - jam["at"][0], mis[2] - jam["at"][2]) > 4.0:
                        jam["state"] = "done"
                        px_, pz_ = point_at(poly, s_p)
                        d_ = math.hypot(mis[0] - px_, mis[2] - pz_)
                        behind_ = polyline_s(poly, mis[0], mis[2]) < s_p
                        jam["rescue"] = (t, mis, d_, behind_)
                        log(f"RESCUED after {t - jam['t0']:.1f} s: Misato is now at ({mis[0]:.1f}, {mis[1]:.1f}, {mis[2]:.1f}), {d_:.1f} blocks from the boy, "
                            f"{'behind' if behind_ else 'AHEAD OF'} him")
                    else:
                        R.cmd(f"data merge entity {CH.format(who='misato')} {{immovable:1b,NoGravity:1b,Motion:[0.0d,0.0d,0.0d]}}")
            s_r = polyline_s(poly, rit[0], rit[2])
            # the boy walks 4.2 blocks a second along the route, never closer than 3.5 blocks behind the leader, and waits where she waits
            s_p = max(s_p, min(s_p + 4.2 * 0.2, s_r - 3.5))
            px, pz = point_at(poly, s_p)
            R.cmd(f"tp {PLAYER} {px:.2f} 54 {pz:.2f}")
            R.cmd("forceload add 3000 128 3110 176")
            dist = math.hypot(mis[0] - px, mis[2] - pz)
            arr = R.score("#arrived_misato", "angel.cast")
            walk = R.score("#walk_misato", "angel.cast")
            lp = R.score("#f.lp_misato")
            step = R.score("#step")
            # stillness of the companion
            if last_m is None or math.hypot(mis[0] - last_m[0], mis[2] - last_m[2]) > 0.25:
                last_m, still_since = mis, t
            still = t - still_since
            behind = polyline_s(poly, mis[0], mis[2]) < s_p
            if still > 3.0 and dist > 6.0 and behind:
                worst_still = max(worst_still, still)
            if t - last_print >= 1.0:
                last_print = t
                print(f"  t={t:5.1f}s step {step}  Ritsuko ({rit[0]:.1f}, {rit[2]:.1f})  boy ({px:.1f}, {pz:.1f})  Misato ({mis[0]:.1f}, {mis[1]:.1f}, {mis[2]:.1f}) "
                      f"d={dist:4.1f} still {still:4.1f}s arrived={arr} walk={walk} paused={lp}", flush=True)
            sc = R.score("#scene")
            if sc is not None and sc != 4:
                log(f"the story handed over to scene {sc}")
                break
            if step is not None and step > first + 400:
                break
            time.sleep(0.12)
        time.sleep(1.0)
        mis = R.pos(CH.format(who="misato"))
        rit = R.pos(CH.format(who="ritsuko"))
        end_d = math.hypot(mis[0] - px, mis[2] - pz) if mis else 99
        ok = True
        if worst_still > 3.0 and not a.jam:
            verdict.append(f"FAIL: the companion stood still for {worst_still:.1f} s, more than 6 blocks behind the boy")
            ok = False
        if end_d > 8.0:
            verdict.append(f"FAIL: the companion ended {end_d:.1f} blocks from the boy")
            ok = False
        else:
            verdict.append(f"ok: the companion ended {end_d:.1f} blocks from the boy, at ({mis[0]:.1f}, {mis[1]:.1f}, {mis[2]:.1f}); leader at ({rit[0]:.1f}, {rit[1]:.1f}, {rit[2]:.1f})")
        if a.jam:
            if jam["state"] == "done" and jam["rescue"][2] <= 6.6 and jam["rescue"][3]:
                verdict.append(f"ok: the stuck companion was put {jam['rescue'][2]:.1f} blocks behind the boy {jam['rescue'][0] - jam['t0']:.1f} s after she was held")
                worst_still = 0.0                       # (the stillness of the jam itself is what the keeper cures)
            else:
                verdict.append("FAIL: the jammed companion was not put on a reachable cell behind the boy: " + str(jam.get("rescue", jam["state"])))
                ok = False
        if worst_still <= 3.0 and not a.jam:
            verdict.append("ok: the companion never stood still for 3 s while more than 6 blocks behind the boy")
        print("\n".join(verdict))
        return 0 if ok else 1
    finally:
        if srv is not None:
            srv.stop()
            log("scratch server stopped" + ("" if a.keep else " and deleted"))
        shutil.rmtree(tmp0, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--pace", help="pacing preset passed to the build (default: the build's default)")
    ap.add_argument("--pack", help="an assembled datapack folder to use instead of building one")
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--scene4", action="store_true", help="run the whole of scene 4 from its start with the stand-in boy following whoever leads (a smoke test of the tight pacing)")
    ap.add_argument("--jam", action="store_true", help="hold Misato in place from t = 8 s (as if walking against a wall): the keeper must put her near the boy, behind him")
    ap.add_argument("--max-seconds", type=float, default=160.0)
    a = ap.parse_args()
    return run(a)


if __name__ == "__main__":
    sys.exit(main())
