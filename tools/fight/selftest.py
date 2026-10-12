"""Live test of the Angel and the fight on a scratch copy of the server (nothing in the repo or the real server changes).

    python selftest.py [--keep]

Copies D:\\angel-attack\\server (without its world and logs) to a temp folder, sets server-port 25608 and rcon.port 25618,
copies the datapack in, starts it headless, drives it over RCON, and stops and deletes the copy at the end (--keep leaves it).
There is no game client: an armor stand tagged angel.giant stands in for the player (`function angel:fight/test/start`), and a
left click on the core is simulated by writing the `attack` data an interaction entity gets from a real click.
Run build_fight.py first.  Takes about six minutes.
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)
import rcon  # noqa: E402
from gen_fight import CFG  # noqa: E402  (the fight's numbers: this test follows them)
import model  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
JAVA = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Packages", "Microsoft.4297127D64EC6_8wekyb3d8bbwe", "LocalCache",
                    "Local", "runtime", "java-runtime-epsilon", "windows-x64", "java-runtime-epsilon", "bin", "java.exe")
RESULTS = []
R = None
LOG = None


def check(name, ok, detail=""):
    RESULTS.append((name, bool(ok), detail))
    print(("  ok    " if ok else "  FAIL  ") + name + (f"   [{detail}]" if detail else ""), flush=True)


def c(cmd):
    return R.cmd(cmd)


def wait(ticks):
    time.sleep(ticks / 20.0)


def score(name, obj="angel.fight"):
    m = re.search(r"has (-?\d+)", c(f"scoreboard players get {name} {obj}"))
    return int(m.group(1)) if m else None


def pos(sel):
    m = re.findall(r"(-?\d+\.\d+)d", c(f"data get entity {sel} Pos"))
    return [float(x) for x in m] if m else None


def count(sel):
    m = re.search(r"Count: (\d+)", c(f"execute if entity {sel}"))
    return int(m.group(1)) if m else 0


def tick_stats():
    m = re.search(r"Average time per tick: ([\d.]+)ms.*?P95: ([\d.]+)ms.*?P99: ([\d.]+)ms", c("tick query"), re.S)
    return tuple(float(x) for x in m.groups()) if m else (0, 0, 0)


def played():
    return re.findall(r'id: "([\d_]+)"', c("data get storage angel:fight played"))


ROOT_ = "@e[type=minecraft:marker,tag=angel.root,limit=1]"
GIANT = "@e[tag=angel.giant,limit=1]"


def setv(n, v):
    c('function angel:fight/test/set {name:"%s",value:%s}' % (n, v))


def hit():
    setv("hitcd", 0)                       # the core's guard (CFG hit_cd, 1.2 s) would swallow hits made in quick succession
    c("function angel:fight/test/hit_core")
    wait(10)


def giant_at(z, x=1160.0):
    c("function angel:fight/test/giant_at {x:%.1f,y:64.0,z:%.1f}" % (x, z))


def place_monster(z, x=1160.0):
    """Puts the monster's root (and so every part and both hit boxes) at x/z on the avenue, standing still."""
    c("function angel:angel/stop_walking")
    c("tp %s %.1f 64.0 %.1f" % (ROOT_, x, z))
    c("function angel:angel/sync")


def fresh_fight():
    c("scoreboard players set #talking angel.story 0")
    c("function angel:fight/stop")
    c("function angel:fight/test/start")
    wait(30)
    c("function angel:fight/begin_ai")
    setv("cd", 9999)


TALK = "scoreboard players set #talking angel.story %d"


def talk(v):
    """Somebody is speaking (v 1: the story's t_line counts #line_left down, so it is made very long) or not (0)."""
    c(TALK % v)
    c("scoreboard players set #line_left angel.story %d" % (99999 if v else 0))


def wait_until(fn, secs, step=0.05):
    t_end = time.time() + secs
    while time.time() < t_end:
        v = fn()
        if v:
            return v
        time.sleep(step)
    return fn()


CK_STATE = []


def to_wrap(talking=0, crack=True):
    """A fresh fight taken to the start of the wrap (phase 3, st 7: wrapped, the countdown held or running) through the crack (checkpoint set) or not.
    Giant 10 blocks in front of the monster, in reach.  `talking` is what #talking angel.story is when the wrap's bark is queued (1: someone is speaking)."""
    fresh_fight()
    place_monster(110.0)
    giant_at(120.0)
    wait(10)
    if crack:
        setv("ch", CFG["crack_at"] + 1)
        hit()
        wait(5)
        CK_STATE[:] = [pos(ROOT_), pos(GIANT)]           # where they stand when the core cracks: the checkpoint
    setv("ch", CFG["wrap_at"] + 1)
    c("data modify storage angel:fight q set value []")
    talk(talking)
    setv("hitcd", 0)
    c("function angel:fight/test/hit_core")
    return wait_until(lambda: score("#st") == 7, 10)


def run_hitter(offsets):
    """A scripted hitter in GAME time: one click at each tick offset after the countdown started (#wgo 1).  Returns the countdown (ticks left) read just before
    the last click it made."""
    wait_until(lambda: score("#wgo") == 1, 12)
    t0 = score("#tick")
    last = None
    for off in offsets:
        while score("#tick") - t0 < off:
            time.sleep(0.004)
        if score("#phase") != 3:
            break
        last = score("#wt")
        c("function angel:fight/test/hit_core")
    wait(4)
    return last


class StoryModel:
    """The story's polling of the fight (tools/story/scenes/s07.py), line for line: beat 70 while fighting, 81 from phase 5 until the fight runs again in phase
    0..3, and the music: phase 1 fight, 2..3 fight_final, 4 stop, 5 defeat, 0 after a defeat re-arms.  Fed the (phase, run) pairs the scratch server shows."""
    def __init__(self):
        self.beat, self.mus, self.log = 70, 0, ["start"]

    def poll(self, ph, run):
        if ph == 5:
            self.beat = 81
        if self.beat == 81 and run == 1 and 0 <= ph <= 3:
            self.beat = 70
        before = self.mus
        if ph == 1 and self.mus == 0:
            self.mus = 1; self.log.append("fight")
        if 2 <= ph <= 3 and self.mus in (0, 1):
            self.mus = 2; self.log.append("final")
        if ph == 4 and self.mus in (0, 1, 2):
            self.mus = 3; self.log.append("stop")
        if ph == 5 and self.mus in (0, 1, 2):
            self.mus = 3; self.log.append("defeat")
        if ph == 0 and self.mus == 3:
            self.mus = 0


def lose_and_watch(max_s=60):
    """After a loss (phase 5): keeps the story quiet so that the defeat lines end, and records the (phase, run) sequence until the fight is running again (or the
    time is up).  Returns (phases seen in order, StoryModel, #attempt)."""
    story = StoryModel()
    story.played = set()
    seq = []
    a0 = score("#attempt")
    t_end = time.time() + max_s
    n = 0
    while time.time() < t_end:
        ph, run = score("#phase"), score("#run")
        if not seq or seq[-1] != ph:
            seq.append(ph)
        story.poll(ph, run)
        n += 1
        if n % 3 == 0:
            talk(0)
        if n % 8 == 0:
            story.played |= set(played())
        if score("#attempt") == a0 + 1 and run == 1:
            break
        time.sleep(0.05)
    # a few more polls, as the story would
    for _ in range(10):
        story.poll(score("#phase"), score("#run"))
        time.sleep(0.05)
    return seq, story, score("#attempt")


def main():
    global R
    keep = "--keep" in sys.argv
    tmp = tempfile.mkdtemp(prefix="aa_fight_scratch_")
    srv = os.path.join(tmp, "server")
    print("scratch copy:", tmp)
    proc = None
    try:
        shutil.copytree(os.path.join(ROOT, "server"), srv, ignore=shutil.ignore_patterns("angel-world", "logs", "crash-reports"))
        props = open(os.path.join(srv, "server.properties"), encoding="utf-8").read().splitlines()
        out = []
        for ln in props:
            for k, v in (("server-port", "25608"), ("rcon.port", "25618"), ("query.port", "25608"), ("online-mode", "false")):
                if ln.startswith(k + "="):
                    ln = f"{k}={v}"
            out.append(ln)
        open(os.path.join(srv, "server.properties"), "w", encoding="ascii").write("\n".join(out) + "\n")
        dp = os.path.join(srv, "angel-world", "datapacks")
        os.makedirs(dp)
        shutil.copytree(os.path.join(ROOT, "datapack", "angel"), os.path.join(dp, "angel"))
        rcon.SERVER = srv
        proc = subprocess.Popen([JAVA, "-Xms1G", "-Xmx4G", "-jar", "fabric-server-launch.jar", "nogui"], cwd=srv,
                                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        t0 = time.time()
        while True:
            try:
                R = rcon.Rcon(port=25618)
                break
            except Exception:
                if time.time() - t0 > 180 or proc.poll() is not None:
                    raise RuntimeError("server did not come up")
                time.sleep(2)
        logp = os.path.join(srv, "logs", "latest.log")
        log = lambda: open(logp, encoding="utf-8", errors="replace").read()
        run_tests(log)
    finally:
        try:
            R.cmd("stop")
        except Exception:
            pass
        if proc:
            try:
                proc.wait(timeout=60)
            except Exception:
                proc.kill()
        if not keep:
            shutil.rmtree(tmp, ignore_errors=True)
            print("scratch copy deleted:", not os.path.exists(tmp))
    bad = [r for r in RESULTS if not r[1]]
    print(f"\n{len(RESULTS) - len(bad)} of {len(RESULTS)} checks passed")
    return 1 if bad else 0


def run_tests(log):
    print("== pack load")
    errs = [ln for ln in log().splitlines() if ("ERROR" in ln and "angel" in ln.lower()) or "Failed to load function angel" in ln]
    check("datapack loads with no function errors", not errs, "; ".join(errs[:2]))
    c("function angel:world/init")
    c("function angel:fight/load")
    c("forceload add 1100 0 1230 330")
    c("function angel:world/place_city")
    t0 = time.time()
    while "placed city" not in log() and time.time() - t0 < 180:
        time.sleep(2)
    check("city placed", "placed city" in log())
    c("forceload add 1100 0 1230 330")
    wait(40)
    errs = [ln for ln in log().splitlines() if "Failed to load function angel" in ln]
    check("no function failed to load after the city is placed", not errs)

    # every sound the fight and the monster play exists (ours in sounds.json, vanilla ones in the installed client's list), and the fight
    # uses the library's events where there is one
    import build_fight  # noqa: E402
    fn_root = os.path.join(ROOT, "datapack", "angel", "data", "angel", "function")
    allf = {}
    for sub in ("fight", "angel"):
        for dp_, _, fs in os.walk(os.path.join(fn_root, sub)):
            for f in fs:
                if f.endswith(".mcfunction"):
                    allf[os.path.join(dp_, f)] = open(os.path.join(dp_, f), encoding="utf-8").read().splitlines()
    bad_snd = build_fight.check_sounds(allf)
    used = {m for ls in allf.values() for ln in ls for m in re.findall(r"playsound ([a-z0-9_.:]+)", ln)}
    check("every sound the fight plays exists (%d ids; ours in sounds.json, vanilla ones in the 26.3 client's list)" % len(used), not bad_snd and len(used) > 10, str(bad_snd[:3]))
    lib = {"barrier", "core_crack", "beam_charge", "beam_fire", "giant_hit", "giant_punch", "cross", "footfall_giant"}
    check("the library's fight events are used: " + ", ".join(sorted(lib)) + ", heartbeat",
          lib <= {u.split(".", 1)[1] for u in used if u.startswith("angel:sfx.")} and any("angel:sfx.heartbeat" in ln for ls in allf.values() for ln in ls))

    print("== geometry: how close the monster's display model comes to the giant's eyes (%.1f up), from the pose key frames" % model.EYE_H)
    rows = model.eye_clearance_table()
    groups = [("idle", ("idle_a", "idle_b")), ("walk", ("walk_l", "walk_r")), ("windup", ("windup",)), ("stagger and the back-off recoil", ("stagger", "idle_a -> stagger", "idle_b -> stagger", "windup -> stagger", "walk_l -> stagger", "walk_r -> stagger")),
              ("regenerating (the crack's pause)", ("regen_", "idle_a -> regen_0")), ("thrust (it strikes the chest)", ("thrust", "windup -> thrust")), ("charging (d 24+)", ("charge",)),
              ("wrapping (arms round the sides)", ("wrap_",))]
    for gname, pre in groups:
        sel = [r for r in rows if any(r[0].startswith(p) for p in pre)]
        worst = min(sel, key=lambda r: r[1])
        check("eye clearance, %s: at least %.2f blocks over %d frames/ranges (closest %.2f: %s, eye %s blocks away)" % (gname, model.MIN_CLEAR, len(sel), worst[1], worst[2], worst[3]),
              all(r[1] >= r[4] for r in sel), "; ".join(f"{r[0]} {r[1]:.2f}" for r in sel if r[1] < r[4]))
    import gen_angel
    tp = [e for e in model.pose_boxes(model.poses()["thrust"]) if e["name"] == "palmR"][0]["centre"] * 0.3
    check("the arm thrust strikes the chest, not the head: the hand ends %.1f up at %.1f ahead (giant's chest about 18, eyes %.1f)" % (tp[1], tp[2], model.EYE_H), 14 <= tp[1] <= 21 and tp[2] >= 13, f"{tp}")

    print("== the monster")
    for H in (60, 30):
        c("function angel:angel/remove")
        c("execute positioned 1160.0 64.0 50.0 rotated 0 0 run function angel:angel/summon {height:%d}" % H)
        n_parts = count("@e[type=minecraft:block_display,tag=angel.part]")
        check(f"summon height {H}: parts + markers + 2 hit boxes", n_parts >= 100 and count("@e[tag=angel.mon]") == n_parts + 6,
              f"{n_parts} display parts, {count('@e[tag=angel.mon]')} entities")
        m = re.search(r"scale: \[([\d.\-e]+)f, ([\d.\-e]+)f, ([\d.\-e]+)f\]",
                      c("data get entity @e[type=minecraft:block_display,tag=angel.p0,limit=1] transformation"))
        check(f"height {H}: part scale is in blocks (pelvis width = 0.15 * {H})", m and abs(float(m.group(1)) - 0.15 * H) < 0.01, m.group(0) if m else "")
    c("function angel:angel/remove")
    c("execute positioned 1160.0 64.0 50.0 rotated 90 0 run function angel:angel/summon {height:30}")
    r = c("data get entity @e[type=minecraft:block_display,tag=angel.p5,limit=1] Rotation")
    check("summon takes the executor's rotation", "90.0f" in r, r[-30:])
    c("rotate %s 0 0" % ROOT_)             # (it was summoned turned 90 degrees; walk turns on the spot first when the target is off to the side)
    c("function angel:angel/sync")
    c("function angel:angel/walk {x:1160,y:64,z:100,speed:0.15}")
    p0 = pos(ROOT_)
    wait(60)
    p1 = pos(ROOT_)
    check("walk moves it at 0.15 blocks per tick", abs((p1[2] - p0[2]) - 9.0) < 1.5, f"{p1[2] - p0[2]:.1f} blocks in 3 s")
    check("walking sets the foot toggle", score("#foot", "angel.mon") in (0, 1))
    p2 = pos("@e[type=minecraft:block_display,tag=angel.p5,limit=1]")
    check("the parts follow the root", abs(p2[2] - p1[2]) < 1.0)
    c("function angel:angel/walk {x:1160,y:64,z:%d,speed:0.4}" % (int(p1[2]) + 3))
    wait(60)
    check("arrival sets #arrived angel.walk", score("#arrived", "angel.walk") == 1 and score("#walking", "angel.mon") == 0)
    for pose in ("idle", "regenerating", "charging", "windup", "thrust", "stagger", "wrap_open", "wrapping", "dying"):
        c('function angel:angel/pose {pose:"%s"}' % pose)
        wait(4)
    check("all poses ran", count("@e[tag=angel.mon]") > 100)
    wait(100)
    check("dying stage 3 reached (core dark)", "black_concrete" in c("data get entity @e[type=minecraft:block_display,tag=angel.corebody,limit=1] block_state"))
    check("dying puts the core glow out (strips dark, veil gone)",
          "black_concrete" in c("data get entity @e[type=minecraft:block_display,tag=angel.coreglow,limit=1] block_state")
          and "air" in c("data get entity @e[type=minecraft:block_display,tag=angel.veil,limit=1] block_state"))
    c('function angel:angel/pose {pose:"charging"}')
    wait(4)
    check("charging lights the eyes", "glowstone" in c("data get entity @e[type=minecraft:block_display,tag=angel.eye,limit=1] block_state"))

    def glow_scale():
        m = re.search(r"scale: \[([\d.\-e]+)f", c("data get entity @e[type=minecraft:block_display,tag=angel.eyeglow,limit=1] transformation"))
        return float(m.group(1)) if m else -1
    c('function angel:angel/pose {pose:"idle"}')
    wait(6)
    g0 = glow_scale()
    c('function angel:angel/pose {pose:"charging"}')
    wait(6)
    g1 = glow_scale()
    wait(40)
    g3 = glow_scale()
    check("the eye glow is hidden when idle and grows over the charge", 0 <= g0 < 0.05 and g1 > 0.5 and g3 > g1 * 1.5, f"idle {g0} stage1 {g1} end {g3}")
    c('function angel:angel/pose {pose:"idle"}')
    wait(6)
    check("going back to idle cancels the pending charge stages and hides the glow", glow_scale() < 0.05, f"{glow_scale()}")
    c('function angel:angel/pose {pose:"regenerating"}')
    seen = set()
    for _ in range(14):
        wait(6)
        seen.add(score("#lp", "angel.mon"))
    check("regenerating runs its 8-frame loop", len(seen) >= 6, f"frames seen {sorted(seen)}")
    c('function angel:angel/pose {pose:"idle"}')
    c("function angel:angel/remove")
    check("remove deletes every part", count("@e[tag=angel.mon]") == 0)

    print("== the fight")
    c("function angel:fight/stop")
    c("function angel:fight/test/start")
    wait(10)
    check("giant scale 16", "16.0" in c("attribute @e[tag=angel.test,limit=1] minecraft:scale get"))
    check("step height 2.6", "2.6" in c("attribute @e[tag=angel.test,limit=1] minecraft:step_height get"))
    check("fight entities exist and are tagged", count("@e[tag=angel.fight]") >= 2 and score("#run") == 1)
    wait(60)
    check("start barks 7.01 queued and played one at a time", played()[:1] == ["7_01"], str(played()))
    giant_at(130.0)
    wait(160)
    check("first steps bark 7.03 queued; AI starts after the intro", score("#phase") >= 1 and "7_03" in played() + re.findall(r'id: "([\d_]+)"', c("data get storage angel:fight q")))
    # barrier and core
    fresh_fight()
    giant_at(70.0)
    wait(10)
    c("function angel:fight/test/hit_core")
    wait(6)
    check("a hit from beyond arm's length stops on the wall of light", score("#ch") == CFG["core_hp"] and count("@e[tag=angel.flash]") >= 10)
    giant_at(60.0)
    wait(10)
    setv("hitcd", 0)                       # (the blocked hit above also armed the core's guard: this is a new attempt, 1.2 s later in play)
    c("function angel:fight/test/hit_core")
    wait(12)
    check("within arm's length it lands on the core", score("#ch") == CFG["core_hp"] - 1)
    c("function angel:fight/test/hit_body")
    wait(6)
    check("a hit on the body does nothing to the core", score("#ch") == CFG["core_hp"] - 1)
    # the core's guard: right after a landed hit the core cannot be hit again for hit_cd ticks (1.2 s); then it can
    setv("hitcd", 0)
    c("function angel:fight/test/hit_core")
    wait(6)
    c("function angel:fight/test/hit_core")
    wait(6)
    check("the core is guarded after a landed hit: two hits 0.3 s apart count once", score("#ch") == CFG["core_hp"] - 2, f"ch {score('#ch')}")
    wait(CFG["hit_cd"])
    c("function angel:fight/test/hit_core")
    wait(6)
    check("... and it takes the next hit once the guard (%.1f s) has run out" % (CFG["hit_cd"] / 20.0), score("#ch") == CFG["core_hp"] - 3, f"ch {score('#ch')}")
    # only a LANDED hit arms the guard; a hit inside the guard sparks and does nothing; blocked and body hits do not arm it
    print("== the core's guard")
    fresh_fight()
    place_monster(50.0)
    giant_at(70.0)                         # 20 blocks away: beyond arm's length
    wait(10)
    setv("hitcd", 0)
    c("function angel:fight/test/hit_core")
    wait(6)
    check("a blocked hit (beyond arm's length) does not arm the guard", score("#hitcd") == 0 and score("#ch") == CFG["core_hp"], f"hitcd {score('#hitcd')} ch {score('#ch')}")
    giant_at(60.0)
    wait(10)
    c("function angel:fight/test/hit_body")
    wait(6)
    check("a body hit does not arm the guard (and does nothing to the core)", score("#hitcd") == 0 and score("#ch") == CFG["core_hp"], f"hitcd {score('#hitcd')} ch {score('#ch')}")
    g0 = score("#guarded") or 0
    c("function angel:fight/test/hit_core")
    wait(3)
    h1 = score("#hitcd")
    check("a landed hit arms the guard for hit_cd ticks and counts toward the back-off",
          score("#ch") == CFG["core_hp"] - 1 and h1 is not None and CFG["hit_cd"] - 8 <= h1 <= CFG["hit_cd"] and score("#bo") == 1, f"ch {score('#ch')} hitcd {h1} bo {score('#bo')}")
    c("function angel:fight/test/hit_core")
    wait(3)
    h2 = score("#hitcd")
    check("a hit inside the guard sparks (guarded branch ran once), reduces nothing, counts for nothing",
          score("#guarded") == g0 + 1 and score("#ch") == CFG["core_hp"] - 1 and score("#bo") == 1, f"guarded {score('#guarded')} ch {score('#ch')} bo {score('#bo')}")
    check("... and does not extend the guard (the timer keeps running down)", h2 is not None and 0 < h2 < h1, f"hitcd {h1} -> {h2}")
    giant_at(70.0)                         # out of reach again, still inside the guard
    setv("blockcd", 0)
    wait(3)
    c("function angel:fight/test/hit_core")
    wait(3)
    h3 = score("#hitcd")
    check("a blocked hit inside the guard shows the barrier (blocked branch ran) and does not re-arm it",
          (score("#blockcd") or 0) >= 1 and count("@e[tag=angel.flash]") >= 10 and h3 is not None and 0 < h3 < h2 and score("#ch") == CFG["core_hp"] - 1,
          f"blockcd {score('#blockcd')} flash {count('@e[tag=angel.flash]')} hitcd {h2} -> {h3}")
    giant_at(60.0)
    wait(3)
    c("function angel:fight/test/hit_body")
    wait(3)
    h4 = score("#hitcd")
    check("a body hit inside the guard does not re-arm it either", h4 is not None and 0 <= h4 < h3, f"hitcd {h3} -> {h4}")

    # low health: the heartbeat plays, and is cut when health comes back
    setv("hb", 0)
    setv("gh", 20)
    wait(30)
    check("health at 25 or less starts the heartbeat loop", (score("#hb") or 0) >= 1, f"hb {score('#hb')}")
    setv("gh", CFG["giant_hp"])
    wait(30)
    check("health back above 25 stops it", score("#hb") == 0, f"hb {score('#hb')}")

    # beam: open line of sight hurts, a wall of blocks saves
    fresh_fight()
    giant_at(130.0)
    setv("cd", 0)
    wait(80)
    check("eye beam with a clear line hurts the giant", score("#gh") <= 75, f"gh {score('#gh')}")
    c("execute positioned 1160.0 80.0 100.0 run function angel:fight/cross_flash")
    check("the cross-shaped flash is three bars of light", count("@e[tag=angel.flash]") >= 3)
    fresh_fight()
    c("fill 1140 64 100 1180 110 101 minecraft:stone")
    giant_at(140.0)
    setv("cd", 0)
    wait(70)
    check("a wall of blocks between them saves the giant", score("#gh") == 100, f"gh {score('#gh')}")
    check("beam damage to the city is small and never at street level", "Test passed" in c("execute if block 1160 66 100 minecraft:stone"))
    c("fill 1140 64 100 1180 110 101 minecraft:air")
    # thrust
    fresh_fight()
    wait(5)
    giant_at(pos(ROOT_)[2] + 30)
    c("function angel:fight/begin_thrust")
    wait(70)
    check("backing away from the arm thrust avoids it", score("#gh") == 100)
    setv("st", 0)
    giant_at(pos(ROOT_)[2] + 14)
    wait(5)
    c("function angel:fight/begin_thrust")
    wait(70)
    check("standing in the arm thrust costs 15", score("#gh") == 85, f"gh {score('#gh')}")
    setv("st", 0)
    setv("hitcd", 0)
    giant_at(pos(ROOT_)[2] + 9)
    wait(5)
    c("function angel:fight/begin_thrust")
    wait(14)
    c("function angel:fight/test/hit_core")
    wait(8)
    check("a core hit during the windup staggers it", score("#st") == 5)
    # ---- back-off: every backoff_hits landed hits it staggers, retreats ~backoff_dist along the avenue, barrier up, then its normal cycle
    print("== back-off")
    N = CFG["backoff_hits"]
    D = CFG["backoff_dist"]
    fresh_fight()
    place_monster(110.0)
    giant_at(120.0)                        # 10 blocks from the monster, within arm's length
    wait(10)
    gz = pos(GIANT)[2]
    for i in range(N - 1):
        hit()
    z_before = pos(ROOT_)[2]
    check("%d landed hits are counted and the monster has not backed off yet" % (N - 1),
          score("#bo") == N - 1 and score("#bar") == 0 and score("#st") == 0, f"bo {score('#bo')} bar {score('#bar')} st {score('#st')}")
    x_before = pos(ROOT_)[0]
    setv("hitcd", 0)
    c("function angel:fight/test/hit_core")
    wait(3)
    z_3 = pos(ROOT_)[2]
    wait(9)
    z_12 = pos(ROOT_)[2]
    sh = CFG["shove"] * CFG["shove_ticks"]
    check("back-off: it is thrown straight back %.1f blocks along the avenue in the first %d ticks (interpolated), away from the giant" % (sh, CFG["shove_ticks"]),
          0.3 < z_before - z_3 < sh - 0.6 and sh - 0.8 <= z_before - z_12 <= sh + 1.2 and abs(pos(ROOT_)[0] - x_before) < 0.5 and gz > z_before,
          f"z {z_before:.1f} -> {z_3:.1f} (3 ticks) -> {z_12:.1f} (12 ticks), x {x_before:.1f} -> {pos(ROOT_)[0]:.1f}")
    check("the %dth landed hit makes it disengage: stagger, barrier up, counter reset" % N,
          score("#st") == 9 and score("#bar") == 1 and score("#bo") == 0 and score("#ch") == CFG["core_hp"] - N and score("#phase") == 1,
          f"st {score('#st')} bar {score('#bar')} bo {score('#bo')} ch {score('#ch')}")
    ch0 = score("#ch")
    setv("hitcd", 0)
    setv("blockcd", 0)
    c("function angel:fight/test/hit_core")
    wait(2)
    check("with the barrier up even a click in reach is stopped (blocked branch, no damage, guard not armed)",
          score("#ch") == ch0 and (score("#blockcd") or 0) >= 1 and score("#hitcd") == 0, f"ch {score('#ch')} blockcd {score('#blockcd')} hitcd {score('#hitcd')}")
    seen = set()
    t_end = time.time() + 20
    while time.time() < t_end and not (score("#hold") == 1 and score("#st") == 0):
        seen.add(score("#st"))
        wait(5)
    z_after = pos(ROOT_)[2]
    check("it turned its back and walked off (stagger 9, retreat 10)", {9, 10} <= seen, str(sorted(seen)))
    check("it ended about %d blocks further from the giant, along the avenue, and holds its ground" % D,
          abs((z_before - z_after) - D) < 2.5 and abs(pos(ROOT_)[0] - 1160.0) < 2 and score("#hold") == 1,
          f"z {z_before:.1f} -> {z_after:.1f}, giant at {gz:.1f}, x {pos(ROOT_)[0]:.1f}, hold {score('#hold')}")
    check("the barrier stays up while it holds (and the fight goes on: phase 1, giant alive)", score("#bar") == 1 and score("#phase") == 1 and score("#gh") > 0)
    z_hold = pos(ROOT_)[2]
    wait(10)
    check("holding: it does not advance on the giant", abs(pos(ROOT_)[2] - z_hold) < 1.0, f"{z_hold:.1f} -> {pos(ROOT_)[2]:.1f}")
    fired = False
    t_end = time.time() + 8
    while time.time() < t_end and not fired:
        fired = score("#st") in (1, 2)
        wait(2)
    check("its first move is the eye beam (the giant being far)", fired, f"st {score('#st')}")
    t_end = time.time() + 10
    while time.time() < t_end and score("#bar") == 1:
        wait(5)
    check("after that first attack the barrier comes down and it may advance again", score("#bar") == 0 and score("#hold") == 0, f"bar {score('#bar')} hold {score('#hold')}")
    setv("cd", 9999)
    c("function angel:fight/test/set {name:\"st\",value:0}")
    c("function angel:angel/stop_walking")
    giant_at(pos(ROOT_)[2] + 9)
    wait(10)
    ch1 = score("#ch")
    hit()
    check("once the barrier is down the fight goes on: a hit in reach lands again", score("#ch") == ch1 - 1 and score("#bo") == 1, f"ch {ch1} -> {score('#ch')} bo {score('#bo')}")
    # no room to retreat: it steps to the other side of the avenue instead, and never past the far end (z 50)
    for x0, side in ((1160.0, "west"), (1154.0, "east")):
        fresh_fight()
        place_monster(54.0, x0)
        giant_at(64.0, x0)
        wait(10)
        setv("bo", N - 1)
        hit()
        t_end = time.time() + 20
        zmin = 999.0
        while time.time() < t_end and not (score("#hold") == 1 and score("#st") == 0):
            zmin = min(zmin, pos(ROOT_)[2])
            wait(5)
        p = pos(ROOT_)
        ok_side = (p[0] <= 1156.0) if side == "west" else (p[0] >= 1164.0)
        check("no room (4 blocks of avenue left): it sidesteps to the %s side and stays at or beyond z 50" % side,
              ok_side and zmin >= 49.0 and p[2] >= 49.0 and score("#hold") == 1, f"from x {x0} z 54 to x {p[0]:.1f} z {p[2]:.1f} (lowest z {zmin:.1f})")
    # the wrap phase does not count
    fresh_fight()
    place_monster(110.0)
    giant_at(120.0)
    wait(10)
    setv("bo", N - 1)
    setv("phase", 3)
    hit()
    check("hits in the final wrap phase are not counted and never trigger a back-off", score("#bo") == N - 1 and score("#bar") == 0 and score("#st") != 9, f"bo {score('#bo')} bar {score('#bar')} st {score('#st')}")
    # the pause after the core cracks is the player's window: the back-off waits for the next hit after it
    fresh_fight()
    place_monster(110.0)
    giant_at(120.0)
    wait(10)
    setv("bo", N - 1)
    setv("ch", CFG["crack_at"] + 1)
    hit()
    check("the hit that cracks the core does not also trigger a back-off", score("#phase") == 2 and score("#bar") == 0 and score("#bo") == N, f"phase {score('#phase')} bar {score('#bar')} bo {score('#bo')}")
    wait(100)
    hit()
    check("... it follows on the next landed hit once the pause is over", score("#bar") == 1 and score("#bo") == 0, f"bar {score('#bar')} bo {score('#bo')}")

    # crack, wrap, win
    fresh_fight()
    giant_at(pos(ROOT_)[2] + 9)
    wait(5)
    setv("ch", CFG["crack_at"] + 1)
    hit()
    check("core cracks at %d hits left (magma texture, phase 2)" % CFG["crack_at"], score("#phase") == 2 and "magma" in c("data get entity @e[type=minecraft:block_display,tag=angel.corebody,limit=1] block_state"))
    setv("ch", CFG["wrap_at"] + 1)
    setv("hitcd", 0)
    giant_at(pos(ROOT_)[2] + 9)
    wait(100)
    hit()
    check("wrap starts at %d hits left with the countdown bar" % CFG["wrap_at"], score("#phase") == 3, f"phase {score('#phase')} st {score('#st')}")
    talk(0)
    check("monster wraps round the giant and the countdown runs", wait_until(lambda: score("#st") == 7 and score("#wgo") == 1 and score("#wt") < CFG["wrap_ticks"], 12),
          f"st {score('#st')} wgo {score('#wgo')} wt {score('#wt')}")
    check("wrap bar visible", "visible" in c("bossbar get angel:fight/wrap visible") and "hidden" not in c("bossbar get angel:fight/wrap visible"))
    for _ in range(CFG["wrap_at"]):
        hit()
    check("%d quick hits break it: phase 4" % CFG["wrap_at"], score("#phase") == 4, f"phase {score('#phase')}")
    wait(60)
    for _ in range(120):
        if score("#run") == 0:
            break
        wait(20)
    check("win: everything cleaned up, giant back to human scale", score("#run") == 0 and count("@e[tag=angel.fight]") == 0 and "1.0" in c("attribute @e[tag=angel.test,limit=1] minecraft:scale get"))
    check("win: all four victory lines (7.15-7.18) spoken in order", [x for x in played() if x in ("7_15", "7_16", "7_17", "7_18")] == ["7_15", "7_16", "7_17", "7_18"], str(played()))
    check("win: hand-off made (story/fight_done guarded)", "won" in c("data get storage angel:fight handoff") or os.path.isfile(os.path.join(ROOT, "datapack", "angel", "data", "angel", "function", "story", "fight_done.mcfunction")))

    # ---- the wrap's rules: the countdown waits for 7.14; a generous target; no guard; feedback; stages
    print("== the wrap: rules")
    to_wrap(talking=1)
    wait(40)
    check("the countdown does not run until the bark 7.14 has begun (someone else is speaking: bar full, held)",
          score("#st") == 7 and score("#wgo") == 0 and score("#wt") == CFG["wrap_ticks"] and "7_14" not in played(), f"wgo {score('#wgo')} wt {score('#wt')} played {played()}")
    check("... the bark is at the front of the queue", "7_14" in c("data get storage angel:fight q"))
    talk(0)
    check("... and the countdown starts once 7.14 has begun (the line is played, #wgo 1, the bar runs down)", wait_until(lambda: score("#wgo") == 1, 5) and "7_14" in played(),
          f"wgo {score('#wgo')} played {played()}")
    wait(12)
    check("... the bar is running", score("#wt") < CFG["wrap_ticks"], f"wt {score('#wt')}")
    to_wrap(talking=1)
    wait(CFG["wrap_wait"] + 15)
    check("... but it never waits more than wrap_wait (%d) ticks for the line" % CFG["wrap_wait"], score("#wgo") == 1 and score("#wt") < CFG["wrap_ticks"], f"wgo {score('#wgo')} wt {score('#wt')}")

    # the target: the body box is the big one while wrapped (and small again otherwise); a swing in roughly the monster's direction hits it
    def box_w():
        m = re.search(r"([\d.]+)f", c("data get entity @e[type=minecraft:interaction,tag=angel.body,limit=1] width"))
        return float(m.group(1)) if m else -1
    import gen_angel
    want = gen_angel.WRAP_BODY_W * 30
    check("while wrapped the body box is the big target (%.1f blocks wide, %.0f tall)" % (want, gen_angel.WRAP_BODY_H * 30), abs(box_w() - want) < 0.2, f"{box_w()}")
    # geometry: eye 25.9 up at the giant, the monster's root wrap_dist away; rays within 30 degrees sideways and from 60 below to 10 above the line to
    # its chest, reach 18 (entity_interaction_range): all enter the box (slab test on its axis-aligned box)
    import math
    k30 = 30 / 100.0
    half = gen_angel.WRAP_BODY_W * 30 / 2
    y0 = gen_angel.WRAP_BODY_Y * 30
    y1 = y0 + gen_angel.WRAP_BODY_H * 30
    dd = CFG["wrap_dist"]
    box = ((-half, y0, dd - half), (half, y1, dd + half))
    eye = (0.0, 25.9, 0.0)

    def ray_hits(yaw, pitch, reach=18.0):
        cy_, sy_, cp_, sp_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        dr = (sy_ * cp_, sp_, cy_ * cp_)
        t0, t1 = 0.0, reach
        for i in range(3):
            if abs(dr[i]) < 1e-9:
                if not box[0][i] <= eye[i] <= box[1][i]:
                    return False
                continue
            a, b = (box[0][i] - eye[i]) / dr[i], (box[1][i] - eye[i]) / dr[i]
            t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
        return t0 <= t1
    miss = [(yw, pt) for yw in range(-30, 31, 5) for pt in range(-60, 11, 5) if not ray_hits(yw, pt)]
    check("a swing within 30 degrees sideways and from 10 above to 60 below the direction of the wrapped monster hits the big box (reach 18)", not miss, f"misses {miss[:4]} of 13 x 15 rays")
    check("the eye is outside the box (it would be a hit from every direction otherwise)", not (box[0][0] <= eye[0] <= box[1][0] and box[0][2] <= eye[2] <= box[1][2]),
          f"box z from {dd - half:.1f}")

    # every hit counts: no guard, no barrier, core box and body box alike; stages of damage
    to_wrap(talking=0)
    wait_until(lambda: score("#wgo") == 1, 12)
    wait(30)                               # (the guard that the hit which started the wrap armed has run out by now: it must not come back)
    ch0, g0 = score("#ch"), (score("#guarded") or 0)
    for i in range(6):
        c("function angel:fight/test/hit_core" if i % 2 == 0 else "function angel:fight/test/hit_body")
        wait(2)
    check("wrap hits are never guarded and always count: 6 clicks 2 ticks apart (core box and body box) = 6 hits",
          ch0 - score("#ch") == 6 and (score("#guarded") or 0) == g0 and score("#hitcd") == 0, f"ch {ch0} -> {score('#ch')} guarded {score('#guarded')} hitcd {score('#hitcd')}")

    def cracks():
        return [("white_concrete" in c("data get entity @e[type=minecraft:block_display,tag=angel.crack%d,limit=1] block_state" % i)) for i in range(1, 5)]
    check("the core cracks in visible stages: at %d hits left 3 of the 4 cracks of light are open, the 4th is not yet" % score("#ch"), cracks() == [True, True, True, False], str(cracks()))
    setv("bar", 1)
    c("function angel:fight/test/hit_core")
    wait(3)
    check("the barrier being up changes nothing in the wrap (the hit counts)", ch0 - score("#ch") == 7, f"ch {score('#ch')}")
    setv("bar", 0)
    setv("wt", 100)
    c("function angel:fight/test/hit_core")
    wait(3)
    wt1 = score("#wt")
    check("each landed hit gives the countdown bar %d ticks back" % CFG["wrap_bonus"], 100 + CFG["wrap_bonus"] - 6 <= wt1 <= 100 + CFG["wrap_bonus"], f"wt 100 -> {wt1} after 3 ticks")
    check("... and the 4th crack opens with the 2nd-last hit", cracks() == [True, True, True, True] and score("#ch") == CFG["wrap_at"] - 8, f"{cracks()} ch {score('#ch')}")
    setv("wt", CFG["wrap_tight_at"] - 20)
    wait(14)
    check("in the last %d ticks the monster squeezes (pose wrap_tight, stage 1)" % CFG["wrap_tight_at"], score("#wstage") == 1, f"wstage {score('#wstage')}")
    setv("wt", 250)
    wait(14)
    check("... and loosens when a hit puts the time back (stage 0)", score("#wstage") == 0, f"wstage {score('#wstage')}")
    setv("wt", 300)
    wait(3)
    p_hi = score("#hbp")
    setv("wt", 40)
    wait(3)
    p_lo = score("#hbp")
    check("the heartbeat quickens as time runs down: %s ticks between beats at 15 s, %s at 2 s" % (p_hi, p_lo), p_hi is not None and p_lo is not None and p_hi >= 22 and p_lo <= 10, f"{p_hi} -> {p_lo}")
    c("function angel:fight/stop")

    # the pace: a hitter at one hit per 1.5 s wins with at least 5 s to spare; a 6 s pause in all loses
    print("== the wrap: pace")
    to_wrap(talking=0)
    last = run_hitter([30 * i for i in range(1, CFG["wrap_at"] + 1)])
    check("a hitter at one hit per 1.5 s wins the wrap with at least 5 s to spare", score("#phase") == 4 and last is not None and last >= 100,
          f"phase {score('#phase')}, {None if last is None else last / 20:.2f} s left when the last hit landed")
    c("function angel:fight/stop")
    to_wrap(talking=0)
    last = run_hitter([120 + 30 * i for i in range(1, CFG["wrap_at"] + 1)])
    check("the same hitter who stops swinging for 6 s in all loses it (self-destruct, phase 5, hits still left)", score("#phase") == 5 and score("#ch") >= 1,
          f"phase {score('#phase')} ch {score('#ch')}")
    seq, story, att = lose_and_watch(90)
    check("the loss after the core has cracked restarts at the crack, NOT at the launch: phases seen 5 (lost) -> 0 (about 3 s, run 0) -> 2 (cracked)", seq == [5, 0, 2], str(seq))
    mpos, gpos = pos(ROOT_) or [0, 0, 0], pos(GIANT) or [0, 0, 0]
    check("checkpoint state: phase 2, core at its crack health %d, giant healed (%d), the monster and the giant where they stood at the crack, the hunched pause (st 5)" % (CFG["crack_at"], CFG["giant_hp"]),
          score("#phase") == 2 and score("#ch") == CFG["crack_at"] and score("#gh") == CFG["giant_hp"] and score("#st") == 5 and score("#run") == 1
          and all(abs(a - b) < 0.35 for a, b in zip(mpos, CK_STATE[0])) and all(abs(a - b) < 0.35 for a, b in zip(gpos, CK_STATE[1])),
          f"phase {score('#phase')} ch {score('#ch')} gh {score('#gh')} st {score('#st')} monster {mpos} (was {CK_STATE[0]}) giant {gpos} (was {CK_STATE[1]})")
    check("checkpoint state: core cracked (magma, no wrap cracks), no barrier, countdown reset and hidden, giant at scale 16, attempt +1, intro lines not repeated",
          "magma" in c("data get entity @e[type=minecraft:block_display,tag=angel.corebody,limit=1] block_state") and cracks() == [False] * 4 and score("#bar") == 0
          and score("#wgo") == 0 and score("#wt") == CFG["wrap_ticks"] and "hidden" in c("bossbar get angel:fight/wrap visible")
          and "16.0" in c("attribute @e[tag=angel.test,limit=1] minecraft:scale get") and "7_01" not in played() and "7_02" not in played(),
          f"cracks {cracks()} bar {score('#bar')} wt {score('#wt')} played {played()}")
    check("hand-over: the story's polling (s07.py) sees beat 81 during the defeat and 70 again, music: defeat, then fight_final (not fight)", story.beat == 70 and story.log == ["start", "defeat", "final"],
          f"beat {story.beat} music log {story.log}")
    # a second loss in the cracked phase (health) goes back to the same checkpoint
    talk(0)
    setv("cd", 9999)
    c("function angel:fight/test/hurt {dmg:60}")
    setv("ginv", 0)
    c("function angel:fight/test/hurt {dmg:60}")
    check("a loss by health in the cracked phase is a loss too", score("#phase") == 5)
    seq, story, att = lose_and_watch(90)
    check("... and restarts at the same checkpoint: 5 -> 0 -> 2, core at %d, giant healed" % CFG["crack_at"], seq == [5, 0, 2] and score("#ch") == CFG["crack_at"] and score("#gh") == CFG["giant_hp"], f"{seq} ch {score('#ch')} gh {score('#gh')}")
    c("function angel:fight/stop")

    # a loss BEFORE the core has cracked restarts from the launch, as before (a countdown loss cannot come before the crack: the wrap follows it)
    fresh_fight()
    wait(5)
    talk(0)
    c("function angel:fight/test/hurt {dmg:60}")
    setv("ginv", 0)
    c("function angel:fight/test/hurt {dmg:60}")
    check("giant health 0 before the crack is a loss", score("#phase") == 5 and score("#ck") == 0, f"phase {score('#phase')} ck {score('#ck')}")
    a0 = score("#attempt")
    seq, story, att = lose_and_watch(90)
    check("a loss before the core cracked restarts from the launch: phases 5 -> 0 (the intro), monster rebuilt", att == a0 + 1 and {"7_19", "7_20"} <= story.played and seq == [5, 0] and score("#phase") == 0 and count("@e[tag=angel.mon]") > 100, f"{seq} attempt {a0} -> {att}")
    check("... the story model: beat 70 again, music re-armed (defeat, then nothing until phase 1)", story.beat == 70 and story.log == ["start", "defeat"], f"{story.beat} {story.log}")
    check("restart clears the barrier, the hold and the back-off counter", score("#bar") == 0 and score("#hold") == 0 and score("#bo") == 0)
    check("restart restores the giant: scale 16 again, health full", "16.0" in c("attribute @e[tag=angel.test,limit=1] minecraft:scale get") and score("#gh") == 100)
    # loss by health
    c("function angel:fight/begin_ai")
    setv("cd", 9999)
    c("function angel:fight/test/hurt {dmg:60}")
    setv("ginv", 0)
    c("function angel:fight/test/hurt {dmg:60}")
    check("giant health 0 is a loss", score("#phase") == 5)
    c("function angel:fight/stop")
    check("stop cleans everything and restores scale", count("@e[tag=angel.fight]") == 0 and score("#run") == 0)
    # tick cost
    fresh_fight()
    giant_at(150.0)
    setv("cd", 0)
    wait(40)
    samples = []
    for _ in range(25):
        wait(20)
        samples.append(tick_stats())
    avg = sum(s[0] for s in samples) / len(samples)
    p99 = max(s[2] for s in samples)
    check("tick cost in the fight (monster walking and attacking)", avg < 3.0, f"mean {avg:.2f} ms, worst p99 {p99:.1f} ms of 50")
    c("function angel:fight/stop")
    c("function angel:fight/test/off")
    wait(40)
    idle = [tick_stats() for _ in range(3)]
    check("no fight, nothing running: tick cost is the server's own", idle[-1][0] < 1.0, f"{idle[-1]}")


if __name__ == "__main__":
    sys.exit(main())


