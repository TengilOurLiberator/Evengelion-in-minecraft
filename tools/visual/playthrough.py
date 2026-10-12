"""A driven playthrough: the whole story, played as a real client (Tester) joined to a scratch server, photographed at every cue.

    python tools\\visual\\playthrough.py                       the whole story from `angel:story/start`, then the variants
    python tools\\visual\\playthrough.py --no-variants         only the main run
    python tools\\visual\\playthrough.py --skip-main           only the variants (from scene 5: early yes, then lose the fight once)
    python tools\\visual\\playthrough.py --out work\\shots\\playthrough

Needs work\\steps.json (python tools\\story\\build_story.py --check --steps work\\steps.json).

What it does: boots like visual_test.py but with the story datapack, starts the story and then drives the player as a person would: it walks
him (short teleport hops of at most 1 block, about 4 blocks a second, along a route searched in the built voxel world, or in the footsteps of
the character who leads), never teleports him while he rides, turns his head to who is speaking, and answers every wait after 4 s
(`angel:story/answered`; the consent wait on the LATE path: `angel:story/skip` at the first, three nudges and then `angel:story/consented` at
the second).  A poll of the scoreboard (scene, step, beat, wait, talking, ride) every 0.2 s is written to timeline.log; pictures are named
s<scene>_<nn>_<what>.png.  The fight is played with the fight's own test helpers (angel:fight/test/hit_core) at a human pace.  Nothing here
edits the story; only the repo's datapack is copied to the scratch server.
"""
import argparse
import atexit
import heapq
import json
import math
import os
import re
import sys
import threading
import time
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, TOOLS)
sys.path.insert(0, os.path.join(TOOLS, "story"))
sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)

import numpy as np  # noqa: E402
from visual import client as cl  # noqa: E402
from visual import plan as planmod, winutil  # noqa: E402
from visual.server import Scratch  # noqa: E402
import visual_test as vt  # noqa: E402

NAME = cl.NAME
SPEAKERS = {1: "misato", 2: "ritsuko", 3: "gendo", 4: "rei"}


def num(s):
    return re.findall(r"-?\d+\.?\d*(?:[eE]-?\d+)?", s)


def slug(text, n=6):
    w = re.findall(r"[a-z0-9]+", text.lower())
    return "_".join(w[:n])[:44] or "x"


def left_of(yaw):
    a = math.radians(yaw)
    return math.cos(a), math.sin(a)


def angles(frm, to):
    dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
    return math.degrees(math.atan2(-dx, dz)), -math.degrees(math.atan2(dy, math.hypot(dx, dz)))


def angdiff(a, b):
    return (b - a + 180.0) % 360.0 - 180.0


# ------------------------------------------------------------------------------------------------ walking: A* over the built voxel world
class Nav:
    """Search a walkable route over the set's voxel world (tools/story/world_probe.Probe); heights come from Probe.surface."""

    def __init__(self, set_name):
        import world_probe
        self.p = world_probe.Probe(set_name)

    def ok(self, x, y, z):
        p = self.p
        return not p.solid(x, y + 0.5, z) and not p.solid(x, y + 1.5, z)

    def route(self, a, b, window=60):
        p = self.p
        sx, sz = int(math.floor(a[0])), int(math.floor(a[2]))
        gx, gz = int(math.floor(b[0])), int(math.floor(b[2]))
        sy = p.surface(sx + 0.5, sz + 0.5, a[1]) or a[1]
        start = (sx, sz)
        h = {start: sy}
        g = {start: 0.0}
        prev = {}
        openq = [(math.hypot(gx - sx, gz - sz), 0.0, start)]
        done = set()
        best = None
        while openq:
            f, gc, cur = heapq.heappop(openq)
            if cur in done:
                continue
            done.add(cur)
            cx, cz = cur
            cy = h[cur]
            if cx == gx and cz == gz:
                best = cur
                break
            if len(done) > 40000:
                break
            for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
                nx, nz = cx + dx, cz + dz
                if abs(nx - sx) > window + abs(gx - sx) or abs(nz - sz) > window + abs(gz - sz):
                    continue
                if (nx, nz) in done:
                    continue
                s = p.surface(nx + 0.5, nz + 0.5, cy, up=1.05, down=3)
                if s is None or s > cy + 1.01 or not self.ok(nx + 0.5, s, nz + 0.5):
                    continue
                if dx and dz:
                    if not self.ok(cx + dx + 0.5, max(cy, s), cz + 0.5) or not self.ok(cx + 0.5, max(cy, s), cz + dz + 0.5):
                        continue
                ng = gc + (1.4142 if dx and dz else 1.0) + 0.25 * abs(s - cy)
                if (nx, nz) not in g or ng < g[(nx, nz)]:
                    g[(nx, nz)] = ng
                    h[(nx, nz)] = s
                    prev[(nx, nz)] = cur
                    heapq.heappush(openq, (ng + math.hypot(gx - nx, gz - nz), ng, (nx, nz)))
        if best is None:
            return None
        out = [best]
        while out[-1] in prev:
            out.append(prev[out[-1]])
        out.reverse()
        pts = [(c[0] + 0.5, h[c], c[1] + 0.5) for c in out]
        pts[-1] = (b[0], h[out[-1]], b[2])
        return pts


# ------------------------------------------------------------------------------------------------ the driver
class PT(vt.Session):
    def __init__(self, a):
        super().__init__(a)
        self.out = os.path.abspath(a.out)
        os.makedirs(self.out, exist_ok=True)
        self.steps = json.load(open(os.path.join(ROOT, "work", "steps.json")))
        self.tab = build_tables(self.steps)
        T = self.tab["T"]
        self.fight_step = T.find(7, "the fight (its own timeline)")
        self.end7 = max(T.all(7, "the black lifts"))
        self.first_consent = T.find(5, "WAIT (a yes here")
        self.t3_end = T.find(3, "the wagon stops at the terminal")
        self.card_steps = []
        self.tl = open(os.path.join(self.out, "timeline.log"), "a", encoding="utf-8", buffering=1)
        self.events = []
        self.snaps = []
        self.t0 = time.time()
        self.cnt = {}
        self.base = a.snap_base
        self.sched = []                     # [(due, what, forced)]
        self.last_snap = 0.0
        self.last_auto = 0.0
        self.st = dict(scene=0, step=-1, beat=0, wait=0, talking=0, ride=0, speaker=0, tick=0)
        self.step_since = time.time()
        self.scene_since = time.time()
        self.wait_quiet_since = None
        self.nudge_edges = 0
        self.navs = {}
        self.path = []
        self.goal = None
        self.trail = []
        self.trail_who = None
        self.early_yes = a.early_yes
        self.fight = None
        self.fight_plan = "win"
        self.stalls = []
        self.scene_log = {}
        self.pos = None
        self.rot = (0.0, 0.0)
        self.last_poslog = 0.0

    # ------------------------------------------------------------ logging
    def wall(self):
        return time.time() - self.t0

    def log_tl(self, text):
        s = (f"{self.wall():8.1f}s t{self.st.get('tick', 0):7d} S{self.st['scene']} st{self.st['step']:3d} b{self.st['beat']:<3d} "
             f"w{self.st['wait']} T{self.st['talking']} R{self.st['ride']} | {text}")
        self.tl.write(s + "\n")
        print(s, flush=True)

    def ev(self, kind, text, **kw):
        self.events.append(dict(t=round(self.wall(), 1), scene=self.st["scene"], step=self.st["step"], kind=kind, text=text, **kw))
        self.log_tl(f"[{kind}] {text}")

    # ------------------------------------------------------------ server helpers
    def c(self, command):
        try:
            return self.srv.cmd(command)
        except Exception as e:
            self.ev("rcon-error", f"{command[:80]} -> {e}")
            return ""

    def score(self, name, obj="angel.story"):
        m = re.search(r"has (-?\d+)", self.c(f"scoreboard players get {name} {obj}"))
        return int(m.group(1)) if m else None

    def count(self, selector):
        self.c(f"execute store result score #vt.n vt if entity {selector}")
        m = re.search(r"has (-?\d+)", self.c("scoreboard players get #vt.n vt"))
        return int(m.group(1)) if m else -1

    def epos(self, selector):
        out = self.c(f"data get entity {selector} Pos")
        if "following entity data" not in out:
            return None
        v = [float(x) for x in num(out.split("data:")[-1])]
        return tuple(v[:3]) if len(v) >= 3 else None

    def player_pos(self):
        return self.epos(NAME)

    def player_rot(self):
        out = self.c(f"data get entity {NAME} Rotation")
        v = [float(x) for x in num(out.split("data:")[-1])] if "data" in out else []
        return (v[0], v[1]) if len(v) >= 2 else self.rot

    def tp(self, x, y, z):
        self.c(f"execute in minecraft:overworld run tp {NAME} {x:.3f} {y:.3f} {z:.3f}")
        self.pos = (x, y, z)

    def rotate(self, yaw, pitch):
        self.c(f"rotate {NAME} {yaw:.2f} {pitch:.2f}")
        self.rot = (yaw, pitch)

    # ------------------------------------------------------------ the state poll, the timeline
    def read_state(self):
        s = {}
        for k, name in (("scene", "#scene"), ("step", "#step"), ("beat", "#beat"), ("wait", "#wait"), ("talking", "#talking"),
                        ("ride", "#ride"), ("speaker", "#speaker")):
            v = self.score(name)
            s[k] = 0 if v is None else v
        m = re.search(r"is (\d+)", self.c("time query gametime"))
        s["tick"] = int(m.group(1)) if m else self.st.get("tick", 0)
        return s

    def desc(self, sc, i):
        try:
            e = self.steps[str(sc)][i]
        except (KeyError, IndexError):
            return "?", "?", ""
        note = (e.get("note") or "").strip()
        if e["kind"] == "say":
            return e["kind"], f"say {e['line']}", e["line"]
        if not note or note == "gap":
            for j in (i - 1, i - 2, i - 3):
                if j >= 0:
                    p = self.steps[str(sc)][j]
                    if p["kind"] in ("do", "after") and (p.get("note") or "").strip():
                        return e["kind"], f"({e['kind']}) after: {p['note'].strip()}", ""
        return e["kind"], f"({e['kind']}) {note}", ""

    def observe(self):
        """Poll, log changes, run the picture rules.  Returns the state."""
        old = self.st
        st = self.read_state()
        self.st = st
        t = time.time()
        if st["scene"] != old["scene"]:
            self.on_scene(old["scene"], st["scene"])
        if st["step"] != old["step"] or st["scene"] != old["scene"]:
            self.step_since = t
            kind, text, line = self.desc(st["scene"], st["step"])
            if st["scene"] == old["scene"] and st["step"] > old["step"] + 1:
                for j in range(old["step"] + 1, st["step"]):          # steps that ran between two polls: their cues count
                    k2, t2, l2 = self.desc(st["scene"], j)
                    self.log_tl(f"(passed) {t2}")
                    for delay, what in self.tab["force"].get((st["scene"], j), []):
                        self.later(delay, what, True)
            self.log_tl(text)
            self.on_step(kind, text, line)
        if st["wait"] != old["wait"]:
            self.log_tl(f"wait {old['wait']} -> {st['wait']} (speaker {SPEAKERS.get(st['speaker'], st['speaker'])})")
            self.wait_quiet_since = None
            self.nudge_edges = 0
        if st["talking"] != old["talking"]:
            if st["talking"] == 1:
                if st["wait"]:
                    self.nudge_edges += 1
                self.log_tl(f"line begins (speaker {SPEAKERS.get(st['speaker'], st['speaker'])})")
            else:
                self.log_tl("line ends")
        if st["beat"] != old["beat"]:
            self.log_tl(f"beat {old['beat']} -> {st['beat']}")
        near_handover = (st["scene"] == 3 and st["step"] >= self.t3_end) or (st["scene"] == 4 and st["step"] <= 12)
        if t - self.last_poslog >= (1.0 if near_handover else 6.0):
            self.last_poslog = t
            p = self.player_pos()
            if p:
                self.pos = p
            self.log_tl(f"pos {tuple(round(v, 1) for v in p) if p else None} rot {tuple(round(v) for v in self.rot)}")
        self.run_sched()
        if self.auto_active(st) and t - max(self.last_snap, self.last_auto) >= self.auto_interval(st):
            self.last_auto = t
            self.snap("auto")
        return st

    # ------------------------------------------------------------ pictures
    def snap(self, what):
        sc = self.st["scene"]
        self.cnt[sc] = self.cnt.get(sc, 0) + 1
        n = self.cnt[sc] + self.base
        name = f"s{sc}_{n:02d}_{slug(what, 7)}"
        try:
            img = self.frame()
            if img is None:
                raise RuntimeError("no picture")
            img.save(os.path.join(self.out, name + ".png"), compress_level=3)
            g = np.asarray(img.convert("L"), dtype=np.float32)
            self.snaps.append(dict(name=name, scene=sc, step=self.st["step"], wall=round(self.wall(), 1), tick=self.st["tick"], what=what,
                                   contrast=round(float(g.std()), 1), mean=round(float(g.mean()), 1), pos=self.pos))
            self.last_snap = time.time()
            self.log_tl(f"snap {name}  (mean {g.mean():.0f}, contrast {g.std():.0f})")
        except Exception as e:
            self.ev("snap-error", f"{name}: {e}")

    def later(self, delay, what, forced=False):
        self.sched.append((time.time() + delay, what, forced))

    def run_sched(self):
        t = time.time()
        due = [x for x in self.sched if x[0] <= t]
        self.sched = [x for x in self.sched if x[0] > t]
        for _, what, forced in sorted(due):
            if forced or t - self.last_snap >= self.a.spacing:
                self.snap(what)

    def auto_active(self, st):
        sc, i = st["scene"], st["step"]
        if st["ride"] == 1:
            return True
        return any(s == sc and lo <= i <= hi for s, lo, hi, iv in self.tab["auto"])

    def auto_interval(self, st):
        sc, i = st["scene"], st["step"]
        for s, lo, hi, iv in self.tab["auto"]:
            if s == sc and lo <= i <= hi:
                return iv
        return 5.0

    def on_scene(self, a, b):
        t = self.wall()
        if a in self.scene_log:
            self.scene_log[a][1] = t
        self.scene_log.setdefault(b, [t, t])
        self.scene_since = time.time()
        self.ev("scene", f"scene {a} -> {b}")
        counts = {tag: self.count(f"@e[tag={tag}]") for tag in ("angel.story", "angel.cast", "angel.mon", "angel.part", "angel.rpart", "angel.prompt",
                                                              "angel.card", "angel.gate", "angel.seat_passenger", "angel.seat_driver",
                                                              "angel.gaze", "angel.look_target", "angel.ia_car", "angel.ia_phone", "angel.ia_push",
                                                              "angel.fight", "angel.gurney")}
        self.ev("entities", "at scene change: " + ", ".join(f"{k}={v}" for k, v in counts.items()))

    def on_step(self, kind, text, line):
        sc, i = self.st["scene"], self.st["step"]
        for delay, what in self.tab["force"].get((sc, i), []):
            self.later(delay, what, True)
        if kind == "say":
            self.later(0.8, f"say {line}")
        elif kind == "wait":
            self.later(2.0, "prompt")
        elif kind in ("sleep", "until") and "gap" not in text:
            self.later(0.5, text.replace("(sleep)", "").replace("(until)", ""))

    # ------------------------------------------------------------ boot
    def boot(self):
        a = self.a
        for pt in (25604, 25614):
            if not vt.port_free(pt):
                sys.exit(f"port {pt} is busy")
        vt.log("scratch server (with the story)")
        self.srv = Scratch(exclude_dirs=(), keep=a.keep_server, datapack=None)
        self.srv.prepare()
        self.srv.start()
        json.dump([self.srv.proc.pid], open(vt.PIDFILE, "w"))
        mark = len(self.srv.log())
        self.srv.cmd("function angel:world/place_all")
        self.srv.cmd("scoreboard objectives add vt dummy")
        self.srv.wait_log(r"every set is placed", 1500, since=mark)
        vt.log("sets placed; client")
        cl.prepare(vt.GAME, os.path.join(ROOT, "pack", "angel-resources"), a.fov, a.render, 0.5)
        self.client = cl.launch(vt.GAME, self.srv.port, 1600, 900)
        json.dump([self.srv.proc.pid, self.client.pid], open(vt.PIDFILE, "w"))
        t0 = time.time()
        while NAME not in self.srv.cmd("list"):
            if time.time() - t0 > 300 or self.client.poll() is not None:
                raise RuntimeError("the client did not join")
            time.sleep(2)
        vt.log("joined")
        self.srv.cmd(f"gamemode spectator {NAME}")          # the world spawn is over the void: stand him in the outskirts first
        self.srv.cmd(f"execute in minecraft:overworld run tp {NAME} 37.5 80 128.5 -90 0")
        time.sleep(8)
        self.hwnd = winutil.window_of_pid_tree({self.client.pid})
        if not self.hwnd:
            raise RuntimeError("no game window")
        vleft = winutil.user32.GetSystemMetrics(76)
        if vleft < 0:
            winutil.move_window(self.hwnd, vleft + 10, 10)
        else:
            winutil.keep_visible(self.hwnd)
        winutil.SHOT_DIR = os.path.join(vt.GAME, "screenshots")
        winutil.press(self.hwnd, winutil.VK_F1, winutil.SC_F1)
        time.sleep(2)

    def nav(self, set_name):
        if set_name not in self.navs:
            t = time.time()
            self.navs[set_name] = Nav(set_name)
            vt.log(f"nav {set_name} built in {time.time() - t:.0f}s")
        return self.navs[set_name]

    # ------------------------------------------------------------ moving the player
    def set_goal(self, key, target, set_name):
        if self.goal and self.goal[0] == key:
            return
        pos = self.pos or self.player_pos()
        route = None
        try:
            route = self.nav(set_name).route(pos, target)
        except Exception as e:
            self.ev("nav-error", f"{key}: {e}")
        if not route:
            self.ev("nav", f"no route found to {key} {tuple(round(v, 1) for v in target)}: walking straight")
            route = [target]
        else:
            self.ev("nav", f"route to {key}: {len(route)} cells, {sum(math.dist(route[k], route[k + 1]) for k in range(len(route) - 1)):.0f} blocks")
        self.goal = (key, target)
        self.path = list(route)

    def clear_goal(self):
        self.goal = None
        self.path = []

    def walk_step(self, dt, speed=4.2):
        """Advance along the path by speed*dt (at most one block)."""
        if not self.path:
            return False
        pos = self.pos or self.player_pos()
        if pos is None:
            return False
        d = min(1.0, speed * dt)
        x, y, z = pos
        moved = False
        while d > 1e-3 and self.path:
            tx, ty, tz = self.path[0]
            dist = math.dist((x, z), (tx, tz))
            if dist < 1e-3:
                self.path.pop(0)
                continue
            if dist <= d:
                x, y, z = tx, ty, tz
                d -= dist
                self.path.pop(0)
            else:
                f = d / dist
                x, z = x + (tx - x) * f, z + (tz - z) * f
                y = y + (ty - y) * f
                d = 0
            moved = True
        if moved:
            self.tp(x, y, z)
            if self.path:
                yaw, _ = angles((x, 0, z), (self.path[0][0], 0, self.path[0][2]))
                self.turn_to(yaw, 0.0, dt, rate=360.0)
        return moved

    def turn_to(self, yaw, pitch, dt, rate=200.0):
        cy, cp = self.rot
        dy = angdiff(cy, yaw)
        step = rate * dt
        ny = cy + max(-step, min(step, dy))
        np_ = cp + max(-step * 0.5, min(step * 0.5, pitch - cp))
        if abs(dy) > 0.3 or abs(np_ - cp) > 0.3:
            self.rotate(ny, np_)

    def follow(self, who, dt, gap=3.0, speed=4.2):
        """Walk in the footsteps of a character, `gap` blocks behind it."""
        lp = self.epos(f"@e[tag=angel.{who},tag=angel.char,limit=1]")
        if lp is None:
            return
        if self.trail_who != who:
            self.trail, self.trail_who = [], who
        if not self.trail or math.dist(self.trail[-1], lp) >= 0.5:
            self.trail.append(lp)
        pos = self.pos or self.player_pos()
        if pos is None:
            return
        if math.dist((pos[0], pos[2]), (lp[0], lp[2])) <= gap + 0.4 and abs(pos[1] - lp[1]) < 4:
            _, p = angles((pos[0], pos[1] + 1.62, pos[2]), (lp[0], lp[1] + 1.5, lp[2]))
            y, _ = angles(pos, lp)
            self.turn_to(y, p, dt)
            return
        while len(self.trail) > 1 and math.dist((pos[0], pos[2]), (self.trail[0][0], self.trail[0][2])) < 0.8:
            self.trail.pop(0)
        if math.dist((pos[0], pos[2]), (self.trail[0][0], self.trail[0][2])) > 14 or abs(pos[1] - self.trail[0][1]) > 6:
            self.trail = [lp]
        self.path = [self.trail[0]] if self.trail else []
        self.walk_step(dt, speed)

    # ------------------------------------------------------------ the rules of the walk: what the player does at which step
    def drive_player(self, st, dt):
        sc, i = st["scene"], st["step"]
        if self.fight is not None:
            self.clear_goal()
            return
        if st["ride"] == 1:
            self.clear_goal()
            self.look(st, dt)
            return
        p = self.player_pos()              # the story moves him too (jumps, lifts): never walk from a remembered place
        if p:
            self.pos = p
        want = None
        for s, lo, hi, kind, arg in self.tab["walk"]:
            if s == sc and lo <= i <= hi:
                want = (kind, arg, (s, lo, hi))
                break
        if want is None:
            self.clear_goal()
            self.look(st, dt)
            return
        kind, arg, key = want
        if kind == "follow":
            self.follow(arg, dt)
            return
        target = arg(self) if callable(arg) else arg
        if target is None:
            return
        pos = self.pos or self.player_pos()
        if pos and math.dist((pos[0], pos[2]), (target[0], target[2])) < 0.5:
            self.clear_goal()
            self.look(st, dt)
            return
        self.set_goal(key, target, SETOF[sc])
        self.walk_step(dt)

    def look(self, st, dt):
        """Where a person would be looking: the scripted look of the step, else at who is speaking, else (riding) ahead."""
        sc, i = st["scene"], st["step"]
        pos = self.pos or self.player_pos()
        if pos is None:
            return
        eye = (pos[0], pos[1] + 1.62, pos[2])
        for s, lo, hi, fn in self.tab["looks"]:
            if s == sc and lo <= i <= hi:
                r = fn(self, st)
                if r is not None:
                    yaw, pitch = angles(eye, r) if len(r) == 3 else r
                    self.turn_to(yaw, pitch, dt)
                    return
        if self.look_at_speaker(st, dt):
            return
        if st["ride"] == 1:
            out = self.c("data get entity @e[tag=angel.seat_passenger,limit=1] Rotation")
            v = [float(x) for x in num(out.split("data:")[-1])] if "data" in out else []
            if v:
                self.turn_to(v[0], -4.0, dt, rate=120.0)

    def look_at_speaker(self, st, dt):
        if st["talking"] != 1:
            return False
        who = SPEAKERS.get(st["speaker"])
        if not who:
            return False
        tp_ = self.epos(f"@e[tag=angel.{who},tag=angel.char,limit=1]")
        pos = self.pos or self.player_pos()
        if tp_ is None or pos is None or math.dist(tp_, pos) > 30:
            return False
        yaw, pitch = angles((pos[0], pos[1] + 1.62, pos[2]), (tp_[0], tp_[1] + 1.5, tp_[2]))
        self.turn_to(yaw, pitch, dt)
        return True

    # ------------------------------------------------------------ waits
    def handle_wait(self, st):
        """Every wait: a realistic 4 s after the prompt appears, then answer; the consent waits follow the path chosen."""
        w, t = st["wait"], time.time()
        if not w:
            self.wait_quiet_since = None
            return
        if st["talking"] == 1:
            self.wait_quiet_since = None
            return
        if self.wait_quiet_since is None:
            self.wait_quiet_since = t
            return
        quiet = t - self.wait_quiet_since
        if w == 1:
            if quiet >= 4.0:
                self.ev("answer", f"4 s after the prompt: angel:story/answered (speaker {SPEAKERS.get(st['speaker'])})")
                self.snap("prompt_before_answer")
                self.c("function angel:story/answered")
                self.wait_quiet_since = None
        elif w == 2:
            if st["scene"] == 5 and st["step"] == self.first_consent:
                if quiet >= 4.0:
                    if self.early_yes:
                        self.ev("answer", "EARLY YES: angel:story/consented at the wait after 5.24")
                        self.snap("prompt_before_early_yes")
                        self.c("function angel:story/consented")
                    else:
                        self.ev("answer", "late path: a non-yes answer at the wait after 5.24 (angel:story/skip: resume without consent)")
                        self.snap("prompt_before_skip")
                        self.c("function angel:story/skip")
                    self.wait_quiet_since = None
            else:
                if self.nudge_edges >= 3 and quiet >= 0.0:
                    self.ev("answer", f"consent after {self.nudge_edges} nudges: angel:story/consented")
                    self.snap("prompt_before_consent")
                    self.c("function angel:story/consented")
                    self.wait_quiet_since = None
                elif quiet >= 70:
                    self.ev("answer", "consent wait still open after 70 s of quiet: angel:story/consented")
                    self.c("function angel:story/consented")
                    self.wait_quiet_since = None

    # ------------------------------------------------------------ stalls
    def check_stall(self, st):
        sc, i = st["scene"], st["step"]
        limit = self.tab["stall"].get((sc, i), 150.0)
        if sc == 7 and i == self.fight_step:
            return
        el = time.time() - self.step_since
        if el > limit and not st["wait"]:
            self.ev("STALL", f"scene {sc} step {i} unchanged for {el:.0f} s: {self.desc(sc, i)[1]}")
            self.snap("stall")
            self.ev("stall-diagnosis", self.diagnose())
            self.c("function angel:story/skip")
            self.step_since = time.time()
            self.stalls.append((sc, i, el))
            self.stall_count = getattr(self, "stall_count", 0) + 1
            if self.stall_count % 2 == 0:
                self.c("function angel:story/next")

    def diagnose(self):
        pos = self.player_pos()
        bits = [f"player {pos}", f"ride {self.score('#ride')}"]
        for who in ("misato", "ritsuko", "gendo", "rei"):
            p = self.epos(f"@e[tag=angel.{who},tag=angel.char,limit=1]")
            if p:
                bits.append(f"{who} {tuple(round(v, 1) for v in p)}")
        bits.append("mv " + self.c("scoreboard players get #mv.n angel.story") + " / " + self.c("scoreboard players get #mv.limit angel.story"))
        return "; ".join(bits)

    # ------------------------------------------------------------ the loop
    def tick_once(self, dt):
        st = self.observe()
        self.handle_wait(st)
        self.check_stall(st)
        if st["scene"] == 7 and st["step"] == self.fight_step and self.fight is None:
            self.fight = FightDriver(self)
        if self.fight is not None:
            self.fight.step(dt)
            if self.fight.finished:
                self.fight = None
        else:
            self.drive_player(st, dt)
        return st

    def run_until(self, cond, timeout, label):
        t_end = time.time() + timeout
        last = time.time()
        while time.time() < t_end:
            now = time.time()
            dt = max(0.05, min(1.5, now - last))
            last = now
            if self.client.poll() is not None:
                raise RuntimeError("the client closed")
            st = self.tick_once(dt)
            if cond(st):
                return True
            time.sleep(max(0.0, 0.2 - (time.time() - now)))
        self.ev("TIMEOUT", f"{label}: gave up after {timeout} s")
        return False

    # ------------------------------------------------------------ the whole run
    def main(self):
        a = self.a
        self.boot()
        threading.Thread(target=lambda: [self.nav(n) for n in ("outskirts", "hq")], daemon=True).start()
        self.rot = self.player_rot()
        if not a.skip_main:
            if a.start_scene > 1:
                self.c(f"gamemode adventure {NAME}")
                self.c("function angel:story/scene {n:%d}" % a.start_scene)
                self.ev("start", f"angel:story/scene {{n:{a.start_scene}}} (a jump: scenes before it were played in an earlier part of the run)")
                self.run_until(lambda st: st["scene"] == a.start_scene, 40, "the jump")
            else:
                self.c("function angel:story/start")
                self.ev("start", "angel:story/start")
                self.run_until(lambda st: st["scene"] == 1, 40, "scene 1 starts")
            self.run_until(lambda st: st["scene"] == 7 and st["step"] >= self.end7, a.max_minutes * 60, "the story to reach the end")
            self.run_until(lambda st: False, 12, "the cage after the ending")
            self.snap("end_state")
            self.final_report("main")
        if not a.no_variants:
            self.variant()
        self.final_report("final")

    def variant(self):
        a = self.a
        self.ev("variant", "VARIANT: angel:story/scene {n:5}, EARLY yes at the wait after 5.24, then lose the fight once and restart")
        self.early_yes = True
        self.fight_plan = "lose_first"
        self.cnt = {}
        self.base = self.a.snap_base + 300                  # the variant's pictures are numbered from base + 301 in each scene
        self.c("function angel:story/stop")
        time.sleep(3)
        self.c("function angel:story/scene {n:5}")
        self.run_until(lambda st: st["scene"] == 5, 30, "scene 5 jump")
        self.run_until(lambda st: st["scene"] == 7 and st["step"] >= self.end7, a.max_minutes * 60, "the variant to reach the end")
        self.run_until(lambda st: False, 10, "end")
        self.snap("variant_end_state")

    def final_report(self, tag):
        json.dump(dict(snaps=self.snaps, events=self.events, scene_log=self.scene_log, stalls=self.stalls),
                  open(os.path.join(self.out, f"run_{tag}.json"), "w"), indent=1)
        try:
            self.save_logs(self.out)
        except Exception as e:
            print("save_logs:", e)


SETOF = {1: "outskirts", 2: "outskirts", 3: "outskirts", 4: "hq", 5: "hq", 6: "hq", 7: "city"}


def A(name):
    return json.load(open(planmod.ANCHORS))[name]


def anc(name):
    def f(pt):
        a = A(name)
        return (a["x"], a["y"], a["z"])
    return f


def interaction_door(tag, yaw_fn):
    """The place the story calls 'the door': 2.3 blocks to the left of the car whose touch box is the entity `tag`."""
    def f(pt):
        p = pt.epos(f"@e[tag={tag},limit=1]")
        if p is None:
            return None
        lx, lz = left_of(yaw_fn(pt))
        return (p[0] + 2.3 * lx, p[1], p[2] + 2.3 * lz)
    return f


def push_spot(pt):
    p = pt.epos("@e[tag=angel.ia_push,limit=1]")
    if p is None:
        return None
    lx, lz = left_of(100.0)
    return (p[0] - 3.4 * lx, p[1], p[2] - 3.4 * lz)       # the roof of the car on its side (the touch box is centred 3.0 to the right of the car)


def girl_cycle(pt, st):
    """Keep looking down the street for 2.5 s after she is there, then turn away (she goes when he has looked away for 0.7 s)."""
    if time.time() - pt.step_since < 2.5:
        return (-90.0, 0.0)
    return (90.0, 0.0)


def monster_look(pt, st):
    p = pt.epos("@e[type=minecraft:marker,tag=angel.root,limit=1]")
    return (p[0], p[1] + 62.0, p[2]) if p else None


def window_look(pt, st):
    """On the wagon the boy's window (the LEFT side of the car) faces the cavern: look out of it."""
    out = pt.c("data get entity @e[tag=angel.seat_passenger,limit=1] Rotation")
    v = [float(x) for x in num(out.split("data:")[-1])] if "data" in out else []
    return (v[0] - 70.0, -6.0) if v else None


class Tables:
    """What the driver does at which step, found by the notes of the steps (steps.json) so that a rebuilt story does not shift it."""

    def __init__(self, steps):
        self.s = steps
        self.skipped = []

    def all(self, sc, text, start=0):
        out = []
        for e in self.s[str(sc)]:
            if e["i"] < start:
                continue
            if text.startswith("say "):
                hit = e["kind"] == "say" and e["line"] == text[4:]
            else:
                hit = text in (e.get("note") or "")
            if hit:
                out.append(e["i"])
        return out

    def find(self, sc, text, start=0, nth=0):
        m = self.all(sc, text, start)
        if len(m) <= nth:
            raise KeyError((sc, text, nth))
        return m[nth]

    def R(self, sc, a, b=None, nth=0):
        lo = self.find(sc, a, 0, nth)
        if b is None:
            return sc, lo, lo
        return sc, lo, self.find(sc, b, lo + 1) - 1


def build_tables(steps):
    T = Tables(steps)
    walk, looks, auto, force, stall = [], [], [], {}, {}
    skipped = []

    def safe(fn):
        try:
            fn()
        except KeyError as e:
            skipped.append(str(e))

    def W(a, b, kind, arg, sc, nth=0):
        safe(lambda: walk.append((*T.R(sc, a, b, nth), kind, arg)))

    def L(a, b, fn, sc):
        safe(lambda: looks.append((*T.R(sc, a, b), fn)))

    def AU(a, b, iv, sc):
        safe(lambda: auto.append((*T.R(sc, a, b), iv)))

    def F(sc, text, items, nth=0):
        def go():
            force.setdefault((sc, T.find(sc, text, 0, nth)), []).extend(items)
        safe(go)

    def ST(sc, text, limit):
        for i in T.all(sc, text):
            stall[(sc, i)] = limit

    # --- walking
    W("walk to the payphone", "he lifts the handset", "goto", lambda pt: (65.5, 64.5, 118.0), 1)
    W("walk out into the street", "he looks down the street", "goto", anc("outskirts.street"), 1)
    W("get in (door", "-> scene 2", "goto", interaction_door("angel.ia_car", lambda pt: A("outskirts.car_arrive")["yaw"]), 1)
    W("the boy pushes", "beat 22", "goto", push_spot, 2)
    W("get back in (walk", "the door shuts (sfx.car_door)", "goto", interaction_door("angel.ia_car", lambda pt: 100.0), 2)

    def w4():
        lo = T.find(4, "misato reaches the stop")
        walk.append((4, lo, T.find(4, "the player steps into the lift") - 1, "follow", "misato"))
        i = T.find(4, "the player steps into the lift")
        walk.append((4, i, i, "goto", anc("hq.elevator_in")))
        lo2 = T.find(4, "the doors are open on the dock") + 1
        walk.append((4, lo2, T.find(4, "the cage door opens onto darkness") - 1, "follow", "ritsuko"))
    safe(w4)

    def w5():
        lo = T.find(5, "ritsuko walks to through the cage door")
        hi = T.find(5, "the player reaches hq.face")
        walk.append((5, lo, hi - 1, "follow", "ritsuko"))
        walk.append((5, hi, hi, "goto", anc("hq.face")))
        j = T.find(5, "the player comes within 2 blocks of Rei")
        walk.append((5, j, j, "goto", lambda pt: (3096.0, 54.0, 76.2)))
        lo3 = T.find(5, "he follows Ritsuko")
        walk.append((5, lo3, T.find(5, "card 'EVANGELION") - 1, "follow", "ritsuko"))
    safe(w5)

    # --- looking
    L("he lifts the handset", "walk out into the street", lambda pt, st: (65.5, 66.2, 113.5), 1)
    L("he looks down the street", "she is gone when", lambda pt, st: (-90.0, 0.0), 1)
    L("she is gone when", "the ground jumps", girl_cycle, 1)
    L("a jet goes over the street", "the car slides sideways", monster_look, 1)
    L("the wagon passes wall_opens", "the wagon stops at the terminal", window_look, 3)
    L("say 5.01", "the booth lights come on", lambda pt, st: (3096.5, 70.0, 59.0), 5)

    # --- how often pictures are taken in a stretch
    AU("a jet goes over the street", "the car slides sideways", 2.5, 1)
    AU("the car slides sideways", "say 1.04", 1.5, 1)
    AU("say 2.06", "say 2.07", 0.7, 2)
    AU("the car starts to go over", "say 2.10", 0.7, 2)
    AU("the wagon waits in the hall", "the car and the wagon become one rig", 1.5, 3)
    AU("the wagon passes wall_opens", "the wagon stops at the terminal", 3.0, 3)
    AU("first-stage alert", "say 4.12", 0.8, 4)
    AU("the lift goes down", "the doors are open on the dock", 2.0, 4)
    AU("bank 0 on", "say 5.02", 0.6, 5)
    AU("a deep blow from above", "say 5.21", 0.8, 5)
    AU("the gurney starts to roll", "say 5.31", 2.0, 5)
    AU("Rei is thrown from the gurney", "say 5.32", 0.8, 5)
    AU("6.04: the amber fluid begins", "6.07: sfx.contact", 3.0, 6)
    AU("6.07: sfx.contact", "say 6.08", 1.2, 6)
    AU("THE KICK", "say 6.20", 1.0, 6)
    AU("the dawn begins", "silence for the card", 2.5, 7)

    # --- pictures at a cue: (delay after the step is reached, name)
    F(1, "card: held in silence", [(0.8, "card A.D. 2015")], 0)
    F(1, "card: held in silence", [(0.8, "card ANGEL ATTACK")], 1)
    F(1, "walk to the payphone", [(1.5, "wake on the platform")])
    F(1, "he lifts the handset", [(1.2, "the phone")])
    F(1, "he looks down the street", [(1.5, "looking down the street")])
    F(1, "a girl in a school", [(0.6, "the girl appears"), (2.0, "the girl standing")])
    F(1, "she is gone when", [(3.2, "girl looked away")])
    F(1, "the ground jumps", [(0.3, "the jolt")])
    F(1, "a jet goes over the street", [(1.0, "jet"), (3.0, "aircraft"), (6.0, "aircraft later")])
    F(1, "one of the aircraft comes down burning", [(1.5, "crash"), (3.5, "the wreck")])
    F(1, "the blue car out of the smoke", [(1.5, "car out of the smoke")])
    F(1, "the door opens", [(1.0, "door opens")])
    F(2, "the dark lifts", [(0.4, "dark after the blast"), (2.8, "picture comes back")])
    F(3, "the car rolls onto the flat wagon", [(1.0, "car rolls onto wagon"), (3.0, "gate closing"), (6.0, "gate shut")])
    F(3, "the wagon passes wall_opens", [(1.0, "wall opens")])
    F(3, "say 3.08", [(1.0, "the cavern reveal"), (3.5, "the cavern reveal later")])
    F(4, "first-stage alert", [(0.3, "alert red"), (1.6, "alert red pulse")])
    F(4, "the player steps into the lift", [(1.0, "the lift")])
    F(4, "the cage door opens onto darkness", [(1.0, "cage door opens")])
    F(5, "the cage door shuts behind them", [(0.3, "door closed behind them")])
    F(5, "say 5.01", [(2.0, "stand there")])
    F(5, "bank 7 on", [(0.8, "the face bank"), (2.4, "the face lit")])
    F(5, "the booth lights come on", [(0.3, "booth lights stutter"), (1.0, "Gendo lit"), (2.8, "Gendo still")])
    F(5, "a deep blow from above", [(0.3, "first impact"), (1.3, "first impact dust")])
    F(5, "the gurney starts to roll", [(1.2, "gurney rolling")])
    F(5, "the hospital door opens", [(0.5, "hospital door")])
    F(5, "Rei is thrown from the gurney", [(0.2, "second impact"), (0.8, "rig falls"), (1.6, "hand rises"), (2.6, "hand eyes lit"),
                                           (3.6, "rig meets hand"), (5.0, "alarm")])
    F(5, "the hand sinks back", [(0.6, "hand sinks")])
    F(5, "he lifts her", [(0.9, "he lifts her")])
    F(5, "beat 54", [(0.4, "yes everything stops")])
    F(5, "the booth lights go out", [(0.8, "booth lights out")])
    F(5, "the cage goes dark behind them", [(1.0, "cage dark behind"), (3.5, "banks off")])
    F(5, "card: held in silence", [(0.8, "card EVANGELION UNIT 01")])
    F(6, "the hatch closes", [(0.6, "hatch closes")])
    F(6, "DARK: opaque black", [(0.8, "sealed dark")])
    F(6, "dim instrument light", [(0.6, "dim instrument light")])
    F(6, "6.04: the amber fluid begins", [(2.0, "amber begins"), (5.0, "amber at the eyes"), (8.0, "amber full")])
    F(6, "6.07: sfx.contact", [(0.4, "contact"), (1.6, "shimmer"), (3.2, "cockpit white"), (3.8, "cockpit")])
    F(6, "say 6.07", [(1.0, "cockpit 6.07")])
    F(6, "say 6.12", [(1.0, "bolts and bridge")])
    F(6, "the black lifts", [(1.2, "the pad looking up")])
    F(6, "THE KICK", [(0.0, "THE KICK"), (0.8, "up the shaft"), (1.8, "up the shaft later"), (2.8, "up the shaft white")])
    F(6, "THE CUT", [(0.3, "the cut")])
    F(6, "the lift locks, wind", [(1.0, "the surface")])
    F(7, "the dawn begins", [(0.5, "dawn begins")])
    F(7, "card: held in silence", [(0.8, "card TO BE CONTINUED")])
    F(7, "the cage at human size", [(1.0, "back in the cage")])

    # --- legitimate long waits (seconds before a step counts as stuck)
    for text, sc, lim in (("the wagon is at rest at the holding point", 3, 120), ("the wagon passes wall_opens", 3, 60),
                          ("the ride goes on in quiet", 3, 160), ("the wagon stops at the terminal", 3, 60), ("the car is on the wagon", 3, 60),
                          ("the car reaches the ridge", 2, 80), ("the car reaches the gate", 2, 120), ("misato reaches the stop", 4, 120),
                          ("ritsuko reaches the stop", 4, 120), ("the player reaches the lobby", 4, 120)):
        ST(sc, text, lim)
    T.skipped = skipped
    return dict(walk=walk, looks=looks, auto=auto, force=force, stall=stall, skipped=skipped, T=T)


# ------------------------------------------------------------------------------------------------ the fight
class FightDriver:
    """Plays the fight with the fight's own test helpers, more like a person: it walks the giant up to the Angel, clicks the core about once a second
    (the guard swallows every other click), and after each back-off (the monster falls back 30 blocks behind its raised barrier) it closes the distance
    over about 8 s before it hits again.  Photographs the back-off, the raised barrier (a click on it), the beam, the guarded-hit sparks, the phases.
    Heals the giant (test/set gh) when it is low so the whole fight can be seen, unless the plan says lose."""

    def __init__(self, pt):
        self.pt = pt
        self.finished = False
        self.t0 = time.time()
        self.hits = 0
        self.clicks = 0
        self.last_hit = 0.0
        self.st = None
        self.bar = 0
        self.guarded = 0
        self.last_guard_snap = 0.0
        self.healed = 0
        self.lost_done = False
        self.plan = pt.fight_plan
        self.seen = set()
        self.barrier_click_done = False
        self.backoffs = 0
        pt.ev("fight", f"the fight driver starts (plan {self.plan})")
        pt.later(1.0, "fight intro", True)
        pt.later(5.0, "fight intro monster walks", True)

    def fscore(self, name):
        return self.pt.score(name, "angel.fight")

    def in_range(self):
        return "passed" in self.pt.c("execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~-19.75 ~ "
                                     "if entity @e[tag=angel.giant,distance=..12.5]")

    def monster_pos(self):
        return self.pt.epos("@e[type=minecraft:marker,tag=angel.root,limit=1]")

    def note(self, key, what, delay=0.3):
        if key not in self.seen:
            self.seen.add(key)
            self.pt.later(delay, what, True)

    def step(self, dt):
        pt = self.pt
        st = pt.st
        if st["scene"] != 7 or st["step"] != pt.fight_step:
            self.finished = True
            pt.ev("fight", f"the fight is over (clicks {self.clicks}, landed about {self.hits}, back-offs {self.backoffs}, healed {self.healed}x)")
            return
        el = time.time() - self.t0
        phase, stt, ch, gh = self.fscore("#phase"), self.fscore("#st"), self.fscore("#ch"), self.fscore("#gh")
        bar, guarded = self.fscore("#bar") or 0, self.fscore("#guarded") or 0
        if (phase, stt) != self.st:
            pt.log_tl(f"fight phase {phase} state {stt} core hits left {ch} giant hp {gh} barrier {bar}")
            self.st = (phase, stt)
            if stt == 1:
                pt.later(0.5, "beam charge", True)
                pt.later(1.4, "beam charge late", True)
            elif stt == 2:
                pt.later(0.15, "beam fired", True)
                pt.later(0.7, "beam impact", True)
            elif stt == 3:
                pt.later(0.5, "thrust windup", True)
                pt.later(0.95, "thrust ring", True)
            elif stt == 4:
                pt.later(0.1, "thrust strike", True)
            elif stt == 5:
                pt.later(0.8, "stagger crack", True)
                pt.later(2.5, "regenerating", True)
            elif stt == 6:
                pt.later(0.8, "wrap closes in", True)
            elif stt == 7:
                pt.later(0.8, "wrapped", True)
                pt.later(3.0, "wrapped countdown", True)
                pt.later(6.0, "wrapped countdown late", True)
            elif stt == 9:
                self.backoffs += 1
                pt.later(0.4, f"back-off {self.backoffs} the stagger", True)
                pt.later(1.6, f"back-off {self.backoffs} barrier flares", True)
            elif stt == 10:
                pt.later(1.0, f"back-off {self.backoffs} falls back", True)
                pt.later(3.0, f"back-off {self.backoffs} far", True)
            if phase == 4:
                pt.later(0.3, "won", True)
                pt.later(2.0, "won cross of light", True)
                pt.later(5.0, "won later", True)
            if phase == 5:
                pt.later(0.3, "lost", True)
                pt.later(2.5, "lost fade", True)
        if bar != self.bar:
            pt.log_tl(f"barrier {self.bar} -> {bar}")
            if bar == 1:
                pt.later(0.3, "barrier raised", True)
            self.bar = bar
        if guarded > self.guarded:
            self.guarded = guarded
            if time.time() - self.last_guard_snap > 3.0:
                self.last_guard_snap = time.time()
                pt.later(0.1, "guarded hit sparks", True)
        if gh is not None and gh < 40 and self.plan != "lose_now" and phase in (1, 2, 3):
            pt.c("function angel:fight/test/set {name:\"gh\",value:100}")
            self.healed += 1
            pt.ev("fight", f"giant hp was {gh}: healed to 100 (test/set gh)")
        pos = pt.pos or pt.player_pos()
        if phase == 0:
            if pos and el > 4 and pos[2] > 150:
                pt.tp(pos[0], pos[1], pos[2] - 4.5 * dt)
            return
        if phase in (4, 5):
            return
        mp = self.monster_pos()
        pt.pos = pos = pt.player_pos() or pos
        if pos is None or mp is None:
            return
        dz, dx = pos[2] - mp[2], pos[0] - mp[0]
        horiz = math.hypot(dx, dz)
        yaw, pitch = angles((pos[0], pos[1] + 25.9, pos[2]), (mp[0], mp[1] + 20.0, mp[2]))
        pt.turn_to(yaw, pitch, dt, rate=220.0)
        backing = bar == 1 or stt in (9, 10)
        near_goal = 8.5 if stt in (6, 7) else 9.5
        if horiz > near_goal + 1.5:
            speed = 30.0 / 8.0 if backing else 12.0           # after a back-off: the 30 blocks over about 8 s
            step = min(speed * dt, horiz - near_goal)
            f = step / max(horiz, 0.01)
            pt.tp(pos[0] - dx * f, pos[1], pos[2] - dz * f)
        # a click on the raised barrier: once per back-off, a second after it flares
        if backing and stt == 10 and not self.barrier_click_done and time.time() - pt.step_since >= 0:
            self.barrier_click_done = True
            pt.ev("fight", "click on the core behind the raised barrier")
            pt.c("function angel:fight/test/hit_core")
            pt.later(0.3, "barrier click blocked", True)
        if not backing:
            self.barrier_click_done = False
        now = time.time()
        # a person mashes the button while the countdown runs and between guards; calmer in the open phase
        iv = 0.35 if stt in (6, 7) else (0.55 if phase in (2, 3) else pt.a.hit_interval)
        if now - self.last_hit >= iv and (horiz <= near_goal + 4.0 or self.in_range()):
            if not self.in_range() and not backing:
                return
            self.last_hit = now
            if self.plan == "lose_first" and not self.lost_done and self.hits >= 4:
                self.lost_done = True
                pt.ev("fight", "VARIANT: the giant takes 200 damage (test/hurt) to lose the fight")
                pt.c("function angel:fight/test/hurt {dmg:200}")
                pt.later(0.4, "defeat", True)
                self.plan = "lose_now"
                return
            if backing:
                return
            pt.c("function angel:fight/test/hit_core")
            self.clicks += 1
            if ch is not None and (self.last_ch is None or ch < self.last_ch):
                self.hits += 1
            self.last_ch = ch
            if self.clicks in (1, 2):
                pt.later(0.3, f"first click {self.clicks}", True)
            if ch is not None:
                for mark, label in ((50, "50 hits left"), (40, "40 hits left"), (30, "30 hits left"), (20, "20 hits left"), (10, "10 hits left"),
                                    (5, "5 hits left"), (2, "2 hits left")):
                    if ch == mark:
                        self.note(("ch", mark), label)
            if self.clicks % 8 == 3:
                pt.later(0.2, "click", False)
        if phase == 2 and "crack" not in self.seen:
            self.seen.add("crack")
            pt.later(0.4, "core cracked", True)
            pt.later(2.0, "core cracked later", True)

    last_ch = None


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", default=os.path.join(ROOT, "work", "shots", "playthrough"))
    ap.add_argument("--fov", type=int, default=75)
    ap.add_argument("--render", type=int, default=20)
    ap.add_argument("--no-variants", action="store_true")
    ap.add_argument("--skip-main", action="store_true", help="only the variants chain (from scene 5)")
    ap.add_argument("--early-yes", action="store_true")
    ap.add_argument("--start-scene", type=int, default=1, help="jump to this scene with angel:story/scene instead of starting at 1")
    ap.add_argument("--snap-base", type=int, default=0, help="number the pictures from this value + 1 in each scene (to add to an earlier run's folder)")
    ap.add_argument("--keep-server", action="store_true")
    ap.add_argument("--max-minutes", type=float, default=45)
    ap.add_argument("--spacing", type=float, default=1.6, help="least seconds between two ordinary pictures")
    ap.add_argument("--hit-interval", type=float, default=0.95, help="seconds between two core clicks (a human pace)")
    a = ap.parse_args()
    a.plan = None
    a.only = None
    a.with_story = True
    a.datapack = None
    a.world_build = False
    a.monitor = "left"
    a.gui = False
    a.gamma = 0.5
    vt.kill_stale()
    pt = PT(a)
    atexit.register(pt.close)
    code = 0
    try:
        pt.main()
    except BaseException:
        traceback.print_exc()
        try:
            pt.ev("CRASH", traceback.format_exc()[-600:])
            pt.final_report("crash")
        except Exception:
            pass
        code = 1
    finally:
        pt.close()
        atexit.unregister(pt.close)
    sys.exit(code)


if __name__ == "__main__":
    main()
