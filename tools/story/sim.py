"""Offline simulator and checker.

    python build_story.py --check

For every scene it walks the step graph with a clock and reports how long the scene takes (answers and unknown waits are given the
estimated times stored in the steps), which line is said when, the timed effects that run beside the story, and the vehicle's position in
its route.  It checks that:
  * every script line of the scenes written so far is said exactly once, in script order (nags that repeat a line are listed apart);
  * a wait that depends on a route frame can be reached with the limit the story has set (no deadlock), and that any other open-ended wait
    has a timeout (nothing may soft-lock);
  * every anchor used exists, every function that is called exists (cast / monster / world functions are the known external ones);
  * every frame of every route is on a surface with room above it in the built voxel worlds, and the motion is comfortable (accelerations,
    jerk, turn rates).
"""
import math
import os
import re
import sys

import numpy as np

from core import CFG, TPS, T

EXTERNAL = re.compile(r"^(cast|angel|fight|world)/")
FN_RE = re.compile(r"(?:^|\s)function angel:([A-Za-z0-9_/.\-]+)")
SCHED_RE = re.compile(r"schedule function angel:([A-Za-z0-9_/.\-]+)")


class Clock:
    def __init__(self):
        self.route = None
        self.n = 0.0
        self.ref = 0.0
        self.limit = 0
        self.on = False
        self.sched = []                # [(time, limit)]: raises of the route limit scheduled by `s.after` steps

    def _step(self, t):
        if self.on:
            self.n = min(self.limit, self.n + (t - self.ref) * TPS)
        self.ref = t

    def advance(self, t):
        while self.sched and self.sched[0][0] <= t:
            tt, lim = self.sched.pop(0)
            self._step(max(tt, self.ref))
            self.limit = lim
        self._step(t)

    def copy(self):
        c = Clock()
        c.__dict__.update(self.__dict__)
        c.sched = list(self.sched)
        return c


def walk_scene(ctx, scene, report, take=()):
    """Simulate scene `scene`; returns (events, total_seconds, said_lines)."""
    steps = scene.steps
    t = 0.0
    i = 0
    clk = Clock()
    routes_by_id = {r.id: r for r in ctx.routes.values()}
    events = []
    said = []
    timers = []
    guard = 0
    while 0 <= i < len(steps):
        guard += 1
        if guard > 5000:
            report.error(f"scene {scene.n}: the step graph loops")
            break
        st = steps[i]
        k = st.kind
        label = f"{st.note}" if st.note else ""
        if k == "do" or k == "handover":
            clk.advance(t)
            pend = {}
            for c in st.cmds:
                m = re.search(r"scoreboard players set (#mv\.\w+) angel\.story (-?\d+)", c)
                if m:
                    pend[m.group(1)] = int(m.group(2))
            if "#mv.route" in pend or "#mv.n" in pend:
                if "#mv.route" in pend:
                    clk.route = pend["#mv.route"]
                clk.n = float(pend.get("#mv.n", clk.n))
                clk.on = True
            if "#mv.limit" in pend:
                clk.limit = pend["#mv.limit"]
            if pend.get("#mv.on") == 0:
                clk.on = False
            if "#mv.route" in pend:
                r = routes_by_id.get(clk.route)
                events.append((t, f"route {r.name if r else '?'} starts (limit frame {clk.limit} = {clk.limit / TPS:.1f}s)"))
            elif "#mv.limit" in pend:
                events.append((t, f"route limit raised to frame {clk.limit}"))
            elif "#mv.n" in pend:
                events.append((t, f"route jumps to frame {clk.n:.0f}"))
            if k == "handover":
                events.append((t, f"hand over to scene {st.to}"))
                break
            if label and any(w in label for w in ("beat", "present")):
                events.append((t, label))
            i += 1
        elif k == "after":
            timers.append((t + st.sec, st.note or "timed effect"))
            for c in st.cmds:
                m = re.search(r"scoreboard players set #mv\.limit angel\.story (-?\d+)", c)
                if m:
                    clk.sched.append((t + st.sec, int(m.group(1))))
                    clk.sched.sort()
            i += 1
        elif k == "goto":
            i = scene.labels[st.label]
        elif k == "branch":
            i = scene.labels[st.label] if st.label in take else i + 1
        elif k == "sleep":
            t += st.sec
            i += 1
        elif k == "say":
            ln = st.line
            events.append((t, f"{ln.id} {ln.speaker.upper():8s} {ln.seconds:5.2f}s  {ln.text[:60]}"))
            said.append(ln.id)
            t += ln.ticks / TPS
            i += 1
        elif k == "wait":
            nud = getattr(st, "nudges", None)
            extra = " [+ consent-capable: ends on a non-yes answer]" if getattr(st, "answer_ends", False) else ""
            events.append((t, f"WAIT{st.mode} for {st.speaker}: prompt \"Your turn - {st.prompt}\" (assumed {st.est:.1f}s){extra}"))
            t0 = t
            if nud is not None and nud.lines:
                # the player agrees after the first pass of the nudges: each is said once
                for kk, lid in enumerate(nud.lines):
                    ln = ctx.lines[lid]
                    tk = t0 + nud.first + kk * nud.repeat
                    events.append((tk, f"   nudge {kk + 1}: {ln.id} {ln.speaker.upper():8s} {ln.seconds:5.2f}s  {ln.text[:50]}"))
                    said.append(lid)
                t = max(t0 + st.est, t0 + nud.first + (len(nud.lines) - 1) * nud.repeat + ctx.lines[nud.lines[-1]].seconds + 2.0)
            else:
                t += st.est
            i += 1
        elif k == "until":
            # a route condition: reachable?  other conditions: their estimate
            best = None
            for c in st.conds:
                if hasattr(c, "route"):
                    clk.advance(t)
                    cl = clk.copy()
                    t_ev = t
                    while cl.limit < c.frame and cl.sched:          # a raise of the limit that a timer will make
                        t_ev, lim = cl.sched.pop(0)
                        cl.advance(t_ev)
                        cl.limit = lim
                    if clk.route != c.route.id or not clk.on:
                        report.error(f"scene {scene.n} step {i}: waits for route {c.route.name} frame {c.frame}, but that route is not playing")
                        cand = None
                    elif c.frame > cl.limit:
                        report.error(f"scene {scene.n} step {i}: DEADLOCK: waits for route {c.route.name} frame {c.frame} but the limit is "
                                     f"frame {clk.limit}")
                        cand = None
                    else:
                        cand = max(0.0, (t_ev - t) + (c.frame - cl.n) / TPS)
                else:
                    cand = c.est
                if cand is not None and (best is None or cand < best):
                    best = cand
            if best is None:
                best = st.timeout or 0.0
            if st.timeout and best > st.timeout:
                best = st.timeout
            if not st.timeout and not any(hasattr(c, "route") for c in st.conds) and not any(
                    (("flag" in c.desc) or ("mv" in c.desc)) for c in st.conds):
                report.warn(f"scene {scene.n} step {i} ({label[:50]}): open-ended wait with no timeout (player-dependent)")
            events.append((t, f"wait ~{best:.1f}s: {label[:80]}"))
            t += best
            clk.advance(t)
            i += 1
        else:
            i += 1
    events.sort(key=lambda e: e[0])
    return events, t, said, timers


class Report:
    def __init__(self):
        self.errors, self.warnings, self.notes = [], [], []

    def error(self, m):
        self.errors.append(m)

    def warn(self, m):
        self.warnings.append(m)

    def note(self, m):
        self.notes.append(m)


def check_lines(ctx, scenes_said, report):
    for scene, said in scenes_said.items():
        if not said:
            report.note(f"scene {scene}: no recorded lines yet (placeholder)")
            continue
        expect = [lid for lid in ctx.line_order if int(lid.split(".")[0]) == scene]
        # lines that are said only by a nag (conditional) are not part of the main flow
        nag_only = set()
        s = next(s for s in ctx.scenes if s.n == scene)
        for st in s.steps:
            if st.kind == "until" and st.nag:
                for c in st.nag[2]:
                    m = re.search(r"say/(\d+_\d+)", c)
                    if m:
                        nag_only.add(m.group(1).replace("_", "."))
        main_expected = [l for l in expect if l not in nag_only or l in said]
        dup = sorted({l for l in said if said.count(l) > 1})
        if dup:
            report.error(f"scene {scene}: lines said more than once in the main flow: {dup}")
        missing = [l for l in main_expected if l not in said]
        if missing:
            report.error(f"scene {scene}: script lines never said: {missing}")
        if [l for l in said if l in main_expected] != [l for l in main_expected if l in said]:
            report.error(f"scene {scene}: lines are not said in script order: {said}")
        extra = [l for l in said if l not in expect]
        if extra:
            report.error(f"scene {scene}: lines said that do not belong to the scene: {extra}")
        for l in sorted(nag_only):
            if l in said:
                report.note(f"scene {scene}: line {l} is repeated by a nag when the player is slow")
            else:
                report.note(f"scene {scene}: line {l} is conditional ({ctx.lines[l].section or 'nag'}); said only by a nag")
        if not dup and not missing:
            report.note(f"scene {scene}: all {len(main_expected)} script lines said once, in order"
                        + (f" (+ conditional {sorted(nag_only)})" if nag_only else ""))


def check_functions(out, ctx, report):
    have = {k[len("data/angel/function/"):-len(".mcfunction")] for k in out.files if k.startswith("data/angel/function/")}
    bad = set()
    for rel, text in out.files.items():
        if not rel.endswith(".mcfunction"):
            continue
        for line in text.splitlines():
            if line.startswith("#"):
                continue
            for m in FN_RE.finditer(line):
                f = m.group(1)
                if "$(" in f or f.startswith("story/s$"):
                    continue
                if f not in have and not EXTERNAL.match(f):
                    bad.add((rel.split("/")[-1], f))
            for m in SCHED_RE.finditer(line):
                f = m.group(1)
                if f not in have:
                    bad.add((rel.split("/")[-1], "schedule " + f))
    for where, f in sorted(bad):
        report.error(f"{where}: calls function {f}, which does not exist")
    ext = set()
    for rel, text in out.files.items():
        if rel.endswith(".mcfunction"):
            for m in re.finditer(r"function angel:((?:cast|angel|fight|world)/[a-z_/]+)", text):
                ext.add(m.group(1))
    report.note("external functions called: " + ", ".join(sorted(ext)))


def check_commands(out, report):
    """Every command line of every generated function against the game's own command tree (tools/world/cmdcheck.py, structural only)."""
    try:
        import cmdcheck
    except Exception as e:                                  # noqa: BLE001
        report.note(f"command syntax check not available ({e})")
        return
    checker = cmdcheck.Checker()
    funcs = {rel.split("/function/", 1)[-1]: text.splitlines() for rel, text in out.files.items() if rel.endswith(".mcfunction")}
    bad = cmdcheck.check_functions(funcs, checker)
    n = sum(len(v) for v in funcs.values())
    if not bad:
        report.note(f"command syntax: all {n} lines of {len(funcs)} functions fit the game's command tree")
    for path, ln, line, msg in bad[:30]:
        report.warn(f"command syntax: {path}:{ln}: {msg}: {line[:110]}")
    if len(bad) > 30:
        report.warn(f"command syntax: ... and {len(bad) - 30} more")


SOUND_LINE = re.compile(r"(?:^|\s)(playsound|stopsound)\s")
EVENT_RE = re.compile(r"\bangel:([a-z_]+\.[A-Za-z0-9_.]+)")
CALL_RE = re.compile(r"(?<!schedule )function angel:([A-Za-z0-9_/.\-]+)")
SCHED_AT_RE = re.compile(r"schedule function angel:([A-Za-z0-9_/.\-]+) (\d+)t")


def check_sounds(out, report):
    """Every angel: sound event that any generated function plays or stops exists in the pack's sounds.json."""
    from core import SOUNDS
    import json
    try:
        with open(SOUNDS, encoding="utf-8") as f:
            have = set(json.load(f))
    except (OSError, ValueError) as e:
        report.error(f"cannot read sounds.json: {e}")
        return
    used = {}
    for rel, text in out.files.items():
        if not rel.endswith(".mcfunction"):
            continue
        for line in text.splitlines():
            if line.startswith("#") or not SOUND_LINE.search(line):
                continue
            for ev in EVENT_RE.findall(line.split("playsound", 1)[-1] if "playsound" in line else line.split("stopsound", 1)[-1]):
                used.setdefault(ev, set()).add(rel.split("/function/")[-1])
    missing = {e: sorted(w)[:3] for e, w in used.items() if e not in have}
    for e, w in sorted(missing.items()):
        report.error(f"sound event angel:{e} is played or stopped by {w} but is not in sounds.json")
    report.note(f"sounds: {len(used)} angel: events played or stopped by the story, all present in sounds.json" if not missing else
                f"sounds: {len(used) - len(missing)} of {len(used)} angel: events present in sounds.json")
    vanilla = {}
    for rel, text in out.files.items():
        if rel.endswith(".mcfunction"):
            where = "/".join(rel.split("/function/")[-1].split("/")[:2])
            for line in text.splitlines():
                m = re.search(r"playsound (minecraft:[a-z_.]+)", line) if not line.startswith("#") else None
                if m:
                    vanilla.setdefault(m.group(1).replace("minecraft:", ""), set()).add(where)
    if vanilla:
        report.note("vanilla stand-in sounds still played (event: where): " + "; ".join(f"{e}: {', '.join(sorted(w))}" for e, w in sorted(vanilla.items())))
        # each of them must exist in the game's own sounds.json (the client logs "Unable to play unknown soundEvent" and plays nothing otherwise:
        # that is how `block.iron_chain.hit` was found missing in 26.3); read from the installed client's asset index
        try:
            mc = os.path.join(os.environ["APPDATA"], ".minecraft")
            idx_dir = os.path.join(mc, "assets", "indexes")
            known = None
            for name in sorted(os.listdir(idx_dir)):
                idx = json.load(open(os.path.join(idx_dir, name), encoding="utf-8"))["objects"]
                if "minecraft/sounds.json" in idx:
                    hh = idx["minecraft/sounds.json"]["hash"]
                    known = set(json.load(open(os.path.join(mc, "assets", "objects", hh[:2], hh), encoding="utf-8")))
            if known is None:
                raise OSError("no asset index with minecraft/sounds.json")
            gone = sorted(e for e in vanilla if e not in known)
            for e in gone:
                report.error(f"vanilla sound event minecraft:{e} ({', '.join(sorted(vanilla[e]))}) does not exist in this game version")
            report.note(f"vanilla sounds: all {len(vanilla)} stand-in events exist in the installed game's sounds.json" if not gone else
                        f"vanilla sounds: {len(gone)} of {len(vanilla)} do not exist")
        except (OSError, KeyError, ValueError) as e:
            report.note(f"vanilla sound ids not verified (no installed client asset index: {e})")
    return used


def sounds_in(out, lines, t0, depth=0, seen=None):
    """[(tick, description)] of every sound that `lines` (a function body) can start, following function calls and scheduled functions."""
    events = []
    if depth > 8:
        return events
    for line in lines:
        if line.startswith("#"):
            continue
        if "playsound" in line:
            m = re.search(r"playsound (\S+)", line)
            events.append((t0, f"playsound {m.group(1) if m else '?'}"))
        for m in SCHED_AT_RE.finditer(line):
            body = out.files.get(f"data/angel/function/{m.group(1)}.mcfunction")
            if body is not None:
                events += sounds_in(out, body.splitlines(), t0 + int(m.group(2)), depth + 1)
        for m in CALL_RE.finditer(line):
            if "$(" in m.group(1):
                continue
            body = out.files.get(f"data/angel/function/{m.group(1)}.mcfunction")
            if body is not None:
                events += sounds_in(out, body.splitlines(), t0, depth + 1)
    return events


def check_quiet(ctx, out, report):
    """A `s.quiet(a, b)` step declares a window of seconds in which nothing may sound.  Every step that runs in the same instant as it (the timed
    effects `s.after` that follow it, up to the first step that takes time) is followed through every function it calls and schedules."""
    n_windows = 0
    for scene in ctx.scenes:
        for i, st in enumerate(scene.steps):
            q = getattr(st, "quiet", None)
            if not q:
                continue
            n_windows += 1
            lo, hi = int(round(q[0] * TPS)), int(round(q[1] * TPS))
            events = []
            j = i + 1
            while j < len(scene.steps):
                nx = scene.steps[j]
                if nx.kind == "after":
                    body = out.files.get(f"data/angel/function/{nx.path}.mcfunction", "").splitlines()
                    events += sounds_in(out, body, T(nx.sec))
                elif nx.kind == "do":
                    events += sounds_in(out, nx.cmds, 0)
                else:
                    break
                j += 1
            bad = [(t, d) for t, d in events if lo < t < hi]
            near = sorted((t, d) for t, d in events if t <= hi + 6)
            for t, d in bad:
                report.error(f"scene {scene.n}: a sound ({d}) is scheduled at tick {t}, inside the quiet window ticks {lo}..{hi}")
            if not bad:
                report.note(f"scene {scene.n} quiet window ticks {lo}..{hi}: no sound starts inside it (the sounds that do start around it: "
                            + ", ".join(f"tick {t} {d.split(':')[-1]}" for t, d in near) + ")")
    return n_windows


def check_descent(ctx, report):
    """music.descent's bloom (tick 160) must land on geofront.reveal: the ticks from the music's start to the reveal frame, from the steps."""
    d = getattr(ctx, "descent", None)
    scene = next((s for s in ctx.scenes if s.n == 3), None)
    if not d or not scene:
        return
    t_music = t_release = None
    clock = 0
    for st in scene.steps:
        if st.kind == "do" and any("music_descent/start" in c for c in st.cmds):
            t_music = 0
        if st.kind == "after" and any("music_descent/start" in c for c in st.cmds):
            t_music = T(st.sec)
        if st.kind == "do" and any("mv.limit" in c and f" {ctx.routes['geofront_ride'].end} " in c + " " for c in st.cmds):
            t_release = 0
        if st.kind == "after" and any("mv.limit" in c for c in st.cmds):
            t_release = T(st.sec)
    if t_music is None or t_release is None:
        report.error("scene 3: cannot find the music.descent start and the wagon's release in the steps")
        return
    ticks = (t_release - t_music) + (d["reveal"] - d["station"]) - d.get("offset", 0)
    if ticks != d["bloom"]:
        report.error(f"scene 3: music.descent starts {ticks} ticks before the reveal, its bloom is at tick {d['bloom']}")
    else:
        report.note(f"scene 3: music.descent reaches its bloom exactly on geofront.reveal: music at tick 0, wagon let go at tick {t_release - t_music} "
                    f"(from rest at frame {d['station']}), reveal frame {d['reveal']} at tick {ticks} = {ticks / 20.0:.2f} s; wall_opens at tick "
                    f"{t_release - t_music + d['wall'] - d['station']}")


def check_cards(ctx, out, report):
    """The card font exists (definition, atlas, licence) and has every character the cards use."""
    import json
    import cardfont
    problems = []
    for path in (cardfont.OUT_JSON, cardfont.OUT_PNG, cardfont.OUT_LICENSE):
        import os
        if not os.path.isfile(path):
            problems.append(f"missing {os.path.relpath(path, cardfont.ROOT)} (run tools/story/cardfont.py)")
    try:
        with open(cardfont.OUT_JSON, encoding="utf-8") as f:
            fj = json.load(f)
        bm = fj["providers"][0]
        if bm.get("type") != "bitmap" or not (0 < bm["ascent"] <= bm["height"]) or any(len(r) != len(bm["chars"][0]) for r in bm["chars"]):
            problems.append("card.json: the bitmap provider is malformed")
    except (OSError, ValueError, KeyError, IndexError) as e:
        problems.append(f"card.json: {e}")
    for key in ctx.cards:
        for t in (key[0], key[1] or ""):
            if key[2] == cardfont.FONT_ID and not cardfont.covers(t):
                problems.append(f"card {t!r} has characters outside the font")
    for p in problems:
        report.error("cards: " + p)
    if not problems:
        report.note(f"cards: {len(ctx.cards)} cards, all in font {cardfont.FONT_ID} (card.json + card.png present, every character covered)")


def waits_without_nudge(ctx, report):
    rows, gentle = [], []
    for scene in ctx.scenes:
        for st in scene.steps:
            if st.kind != "wait":
                continue
            nud = getattr(st, "nudges", None)
            if not nud:
                rows.append(f"{scene.n}:{st.index}")
            elif nud.gentle:
                gentle.append(f"{scene.n}:{st.index}")
    report.note("waits with no nudge at all (only the speak prompt and angel:story/skip): " + (", ".join(rows) if rows else "none"))
    for r in rows:
        report.error(f"wait {r} has no nudge (the engine gives every wait a gentle default)")
    report.note(f"waits with the engine's gentle default nudge (a look at the player and the prompt pulsing with its chime after 12 s of silence, "
                f"then every 15 s): {', '.join(gentle) if gentle else 'none'}")


# --------------------------------------------------------------------------------------------------- a tiny interpreter for the engine's own functions
class McSim:
    """Runs the generated functions' scoreboard logic (set/add/remove/operation, `execute if|unless score ... matches`, `function`, `return`)
    so that a test can drive the compiled nudge code tick by tick.  Everything else (sounds, entities, selectors) is ignored; an `execute` with a
    condition it does not know does not run its command.  `calls` records every function that ran: [(tick, path)]."""
    def __init__(self, out):
        self.files = {k[len("data/angel/function/"):-len(".mcfunction")]: v.splitlines() for k, v in out.files.items()
                      if k.startswith("data/angel/function/") and k.endswith(".mcfunction")}
        self.score = {}
        self.tick = 0
        self.calls = []

    def get(self, name):
        return self.score.get(name, 0)

    @staticmethod
    def _in(rng, v):
        if ".." in rng:
            lo, hi = rng.split("..")
            return (lo == "" or v >= int(lo)) and (hi == "" or v <= int(hi))
        return v == int(rng)

    def run_function(self, path, depth=0):
        self.calls.append((self.tick, path))
        if depth > 12 or path not in self.files:
            return 0
        for line in self.files[path]:
            r = self.run(line, depth)
            if r is not None and r[0] == "return":
                return r[1]
        return 0

    def run(self, line, depth=0):
        line = line.strip()
        if not line or line.startswith("#"):
            return None
        toks = line.split()
        if toks[0] == "execute":
            i = 1
            while i < len(toks):
                w = toks[i]
                if w in ("if", "unless") and i + 4 < len(toks) + 1 and toks[i + 1] == "score" and toks[i + 4] == "matches":
                    ok = self._in(toks[i + 5], self.get(toks[i + 2]))
                    if (w == "if") != ok:
                        return None
                    i += 6
                elif w == "run":
                    return self.run(" ".join(toks[i + 1:]), depth)
                else:
                    return None                      # a selector, a position, a data test ...: not simulated
            return None
        if toks[0] == "return":
            if len(toks) > 1 and toks[1] == "run":
                self.run(" ".join(toks[2:]), depth)
            return ("return", 0)
        if toks[0] == "function":
            self.run_function(toks[1].split(":", 1)[1], depth + 1)
            return None
        if toks[0] == "scoreboard" and toks[1] == "players":
            op = toks[2]
            if op == "set":
                self.score[toks[3]] = int(toks[5])
            elif op == "add":
                self.score[toks[3]] = self.get(toks[3]) + int(toks[5])
            elif op == "remove":
                self.score[toks[3]] = self.get(toks[3]) - int(toks[5])
            elif op == "operation":
                a, o, b = toks[3], toks[5], toks[6]
                if o == "=":
                    self.score[a] = self.get(b)
        return None


def check_nudge_cadence(ctx, out, report, minutes=3.0):
    """Drive every compiled nudge series (waits with their own nudges, and the engine's gentle default) through three minutes of SILENCE, tick by
    tick, on the generated functions themselves, and assert the cadence: the first nudge after `first` s, and every later one `repeat` s after
    the END of the previous one's line (for a nudge with no line, after its start).  A recorded line is simulated for its real duration."""
    from engine import Nudges
    lines_ticks = {l.key: l.ticks for l in ctx.lines.values()}
    n_checked, bad = 0, 0
    for scene in ctx.scenes:
        for st in scene.steps:
            nud = getattr(st, "nudges", None)
            if st.kind != "wait" or nud is None:
                continue
            i, base = st.index, f"story/s{scene.n}/"
            m = McSim(out)
            m.score.update({"#step": i, "#wait": st.mode, "#talking": 0, "#line_left": 0, "#bridge_speaking": 0, "#wt": -1, "#force": 0,
                            "#timeout_s": 0, "#nagt": 0, "#nagi": 0})
            starts, ends = [], []                               # nudge starts (ticks); ticks at which the line a nudge started ended
            prev_talking = 0
            for tick in range(int(minutes * 60 * TPS)):
                m.tick = tick
                n0 = len(m.calls)
                # t_line, as the engine ticks it
                if m.get("#talking") == 1:
                    m.score["#line_left"] = m.get("#line_left") - 1
                    if m.get("#line_left") <= 0:
                        m.score["#talking"] = 0
                m.run_function(f"{base}p{i}")           # (the say functions it runs set #talking and #line_left themselves: McSim runs them too)
                if any(path == f"{base}nn{i}" for _, path in m.calls[n0:]):
                    starts.append(tick)
                if prev_talking == 1 and m.get("#talking") == 0:
                    ends.append(tick)
                prev_talking = m.get("#talking")
            n_checked += 1
            first_t, rep_t = T(nud.first), T(nud.repeat)
            problems = []
            if not starts or abs(starts[0] - first_t) > 1:
                problems.append(f"first nudge at tick {starts[0] if starts else None}, expected {first_t}")
            # the gap from the end of the previous nudge (its line's end, else its start) to the next start
            for k in range(1, len(starts)):
                line_end = next((e for e in ends if starts[k - 1] <= e <= starts[k]), starts[k - 1])
                gap = starts[k] - line_end
                if abs(gap - rep_t) > 1:
                    problems.append(f"nudge {k + 1} began {gap} ticks after the end of nudge {k} (expected {rep_t})")
                    break
            if nud.lines and len(starts) < 3:
                problems.append(f"only {len(starts)} nudges in {minutes:g} minutes")
            if problems:
                bad += 1
                report.error(f"nudges of scene {scene.n} step {i} ({st.note[:40]}): " + "; ".join(problems) + f"  (starts {starts[:8]})")
    report.note(f"nudge cadence: {n_checked} nudged waits driven through {minutes:g} minutes of silence on the compiled functions: "
                + ("every gap from the end of one nudge line to the start of the next is the configured interval" if not bad else f"{bad} wrong"))


def check_hush(ctx, out, report):
    """Between `s.hush()` and `s.unhush()` no step may start a sound (the recorded voices are `say` steps and are not looked at)."""
    n = 0
    for scene in ctx.scenes:
        inside = False
        for st in scene.steps:
            h = getattr(st, "hush", None)
            if h == "begin":
                inside, n = True, n + 1
                continue
            if h == "end":
                inside = False
                continue
            if not inside:
                continue
            if st.kind == "after":
                body = out.files.get(f"data/angel/function/{st.path}.mcfunction", "").splitlines()
                ev = sounds_in(out, body, 0)
            elif st.kind == "do":
                ev = sounds_in(out, st.cmds, 0)
            else:
                continue
            for _, d in ev:
                report.error(f"scene {scene.n} step {st.index}: {d} starts inside a hush ({st.note[:50]})")
    report.note(f"hush: {n} silent span(s); no step inside them starts a sound, music, bed or loop")


def check_music(ctx, out, report):
    """Every music cue and bed the story starts, against tools/sound/manifest.json: a cue that is a loop file restarts itself, one that is not
    plays once (or is chained to its loop file); a bed is a loop file."""
    import json
    from audio import MUSIC_CHAIN, MUSIC_LOOP
    mp = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sound", "manifest.json")
    try:
        with open(mp, encoding="utf-8") as f:
            man = json.load(f)
        man = man.get("sounds", man)
    except (OSError, ValueError) as e:
        report.warn(f"music check skipped: cannot read tools/sound/manifest.json ({e})")
        return
    rows = []
    for (kind, key), c in sorted(ctx.audio.cues.items()):
        ev = c["event"].split(":", 1)[1]
        ent = man.get(ev)
        if not isinstance(ent, dict):
            report.warn(f"{kind} {key}: {ev} is not in the sound manifest")
            continue
        is_loop = bool(ent.get("loop"))
        if kind == "bed" and not is_loop:
            report.error(f"bed {key}: {ev} is not a loop file in the manifest")
        if kind == "music":
            chained = key in MUSIC_CHAIN
            if is_loop and not c["loop"]:
                report.error(f"music {key}: {ev} is a loop file but the story plays it once (it would go silent after {ent.get('seconds')} s): add it to MUSIC_LOOP")
            elif not is_loop and c["loop"]:
                report.error(f"music {key}: {ev} is NOT a loop file but the story restarts it every {ent.get('seconds')} s")
            elif chained:
                lp = man.get(f"music.{MUSIC_CHAIN[key]}", {})
                if not lp.get("loop"):
                    report.error(f"music {key}: its chained loop file music.{MUSIC_CHAIN[key]} is not a loop in the manifest")
                rows.append(f"{key} (then {MUSIC_CHAIN[key]} looped)")
            else:
                rows.append(f"{key} ({'loops' if c['loop'] else 'plays once, ' + str(ent.get('seconds')) + ' s'})")
    report.note("music cues in the story: " + ", ".join(rows))


def check_relocations(ctx, out, report):
    """Every teleport of the player in a `do` or `after` step: made through `Scene.move_player` (dismount, forceload, teleport, WAIT until he is
    there) or not.  A scene that begins in another set than the player's last one (2000 blocks, unloaded chunks, perhaps still on a vehicle seat)
    must use it: for scenes 4 and up an unguarded teleport into a set other than the scene's own is an error; for the scenes that other hands are
    editing (1 to 3) the call sites that should adopt it are listed."""
    import lead
    from core import P
    pat = re.compile(re.escape(f"tp {P()} ") + r"(-?[\d.]+) (-?[\d.]+) (-?[\d.]+)")
    adopt, guarded_n = [], 0
    for scene in ctx.scenes:
        tps = []                                            # (step, set, guarded)
        for st in scene.steps:
            if st.kind == "after":
                cmds = out.files.get(f"data/angel/function/{st.path}.mcfunction", "").splitlines()
            elif st.kind == "do":
                cmds = st.cmds
            else:
                continue
            for c in cmds:
                m = pat.search(c)
                if m:
                    tps.append((st, lead._set_of(float(m.group(1))), bool(getattr(st, "guarded", False)), (m.group(1), m.group(2), m.group(3))))
        guarded_n += sum(1 for t in tps if t[2])
        home = next((t[1] for t in tps if t[2]), None)
        for st, setname, g, xyz in tps:
            if g:
                continue
            if home is None:
                home = setname                              # the first teleport of a scene without a guarded move defines where it is
                if scene.n >= 4:
                    report.error(f"scene {scene.n} step {st.index}: the scene's first teleport ({setname}) is not made through Scene.move_player")
                else:
                    adopt.append(f"s{scene.n:02d} step {st.index} -> {setname} {', '.join(xyz)} ({st.note[:50]})")
            elif setname != home:
                if scene.n >= 4:
                    report.error(f"scene {scene.n} step {st.index}: unguarded teleport from the {home} set into {setname} ({st.note[:50]})")
                else:
                    adopt.append(f"s{scene.n:02d} step {st.index} -> {setname} {', '.join(xyz)} ({st.note[:50]})")
    report.note(f"player moves: {guarded_n} teleports go through Scene.move_player (dismount, forceload, teleport, wait until he is within 4 blocks, "
                f"re-teleport every second); " + ("scenes 1 to 3 call sites that should adopt it: " + "; ".join(adopt) if adopt else "no unguarded cross-set teleport left"))


def check_encoding(ctx, out, report):
    """Everything generated is plain ASCII (non-ASCII text is written as \\uXXXX), and no story source file holds mojibake (a UTF-8 character that was
    once read as Latin-1, like the bullet that made the speak prompt show boxes)."""
    import os
    bad = [rel for rel, text in out.files.items() if not text.isascii()]
    for rel in bad[:5]:
        report.error(f"generated file {rel} contains non-ASCII characters")
    here = os.path.dirname(os.path.abspath(__file__))
    # a UTF-8 lead byte read as Latin-1 / cp1252 (U+00C2, U+00C3, U+00E2) followed by a continuation byte read the same way, or U+FFFD; the pattern is
    # built from code points so that this file itself holds no such text
    lead_ = "".join(chr(c) for c in (0xC2, 0xC3, 0xE2))
    cont_ = "".join(chr(c) for c in list(range(0x80, 0xC0)) + [0x152, 0x153, 0x160, 0x161, 0x178, 0x17D, 0x17E, 0x192, 0x2C6, 0x2DC] + list(range(0x2013, 0x203B)) + [0x20AC, 0x2122])
    pat = re.compile(f"[{lead_}][{cont_}]|{chr(0xFFFD)}")
    n_src = 0
    for d, _, fs in os.walk(here):
        if "__pycache__" in d:
            continue
        for f in fs:
            if not f.endswith((".py", ".md")):
                continue
            n_src += 1
            p = os.path.join(d, f)
            try:
                text = open(p, encoding="utf-8").read()
            except UnicodeDecodeError as e:
                report.error(f"{p}: not valid UTF-8 ({e})")
                continue
            for ln, line in enumerate(text.splitlines(), 1):
                if pat.search(line):
                    report.error(f"{os.path.relpath(p, here)}:{ln}: mojibake: {line.strip()[:80]!r}")
    report.note(f"encoding: all {len(out.files)} generated files are ASCII; {n_src} story source files are valid UTF-8 with no mojibake")


def check_prompt(out, report):
    """The speak prompt's text, as it will be stored on the entity: the speech-bubble glyph (U+1F4AC, in the default font's Unifont layer) is an
    escape, and the stored string decodes to it."""
    import json
    txt = out.files.get("data/angel/function/story/prompt/v0/spawn.mcfunction", "")
    if "\\ud83d\\udcac" not in txt or "Your turn" not in txt:
        report.error("the speak prompt does not hold the speech-bubble escape and 'Your turn'")
        return
    m = re.search(r'text:(\[\{.*?\}\]),transformation', txt)
    if m:
        comp = json.loads(m.group(1))
        if comp[0]["text"] != "\U0001F4AC ":
            report.error(f"the prompt's first component decodes to {comp[0]['text']!r}")
            return
    report.note("prompt: 'speech balloon (U+1F4AC) Your turn' + the small second line, stored as \\ud83d\\udcac escapes (ASCII)")


def comfort(route):
    f = np.array(route.frames, float)
    v = np.hypot(np.diff(f[:, 0]), np.diff(f[:, 2])) * TPS
    v3 = np.linalg.norm(np.diff(f[:, :3], axis=0), axis=1) * TPS
    v3 = np.convolve(np.pad(v3, 2, mode="edge"), np.ones(5) / 5, mode="valid")        # one frame of rounding must not read as a jolt
    a = np.diff(v3) * TPS
    j = np.diff(a) * TPS
    yaw = np.degrees(np.unwrap(np.radians(f[:, 3])))
    yr = np.abs(np.diff(yaw)) * TPS
    pr = np.abs(np.diff(f[:, 4])) * TPS
    return {"vmax": float(v3.max()), "amax": float(np.abs(a).max()), "jmax": float(np.abs(j).max()), "yaw_rate": float(yr.max()),
            "pitch_rate": float(pr.max()), "pitch": float(np.abs(f[:, 4]).max()), "seconds": len(f) / TPS}


def check_routes(ctx, report, step=2):
    """Replay every frame against the voxel worlds."""
    lines = []
    for r in ctx.routes.values():
        c = comfort(r)
        lines.append(f"route {r.name:15s} {c['seconds']:6.1f}s  vmax {c['vmax']:5.2f} b/s  accel {c['amax']:5.2f}  jerk {c['jmax']:6.2f}  "
                     f"yaw rate {c['yaw_rate']:6.1f} deg/s  pitch {c['pitch']:4.1f} deg (rate {c['pitch_rate']:5.1f})  stations {dict(r.stations)} marks {dict(r.marks)}")
        if c["jmax"] > 40 and r.name != "slide_in":
            report.warn(f"route {r.name}: jerk up to {c['jmax']:.0f} b/s^3 (a rider will feel the start or stop)")
        if c["yaw_rate"] > 60 and r.name != "slide_in":
            report.warn(f"route {r.name}: turns up to {c['yaw_rate']:.0f} deg/s")
        # ground / headroom
        rig = ctx.rigs[r.rig]
        is_train = rig.name.startswith("cartrain")
        probe = ctx.probe("geofront" if is_train else "outskirts")
        worst_dy, worst_hit, hits_total, nfr, first_hit = 0.0, None, {}, 0, {}
        surf = {}
        for i in range(0, len(r.frames), step):
            x, y, z, yaw, pitch = r.frames[i]
            if is_train:
                # the wagon bed (1 thick, 5 x 9) must sit on the deck; the box above must be free
                gy = probe.ground_under(x, z, yaw, hw=2.2, hl=4.0, ref_y=y)
                gy = [v for v in gy if v is not None]
                dy = (y - 1.0) - sum(gy) / len(gy) if gy else 99
                hits = probe.box_hits(x, y, z, yaw, hw=2.5, hl=4.5, h=2.4, y_from=0.95, pitch=pitch)
            else:
                gy = probe.ground_under(x, z, yaw, ref_y=y)
                gy = [v for v in gy if v is not None]
                # a route may declare that its model rides above the ground on purpose (a car on a wagon's deck): Route.deck_lift[i] is the
                # planned height of the deck above the set's ground at frame i; only what is left over counts as 'off the ground'
                lift = getattr(r, "deck_lift", None)
                dy = y - (lift[i] if lift else 0.0) - (sum(gy) / len(gy)) if gy else 99
                hits = probe.box_hits(x, y, z, yaw, y_from=0.95, pitch=pitch)
            sn = probe.surface_name(x, z, y if not is_train else y - 1.0)
            sn = (sn or "none").replace("minecraft:", "").split("[")[0]
            surf[sn] = surf.get(sn, 0) + 1
            if abs(dy) > abs(worst_dy):
                worst_dy, worst_at = dy, (round(x, 1), round(y, 1), round(z, 1), i)
            for nm, n in hits.items():
                hits_total[nm] = hits_total.get(nm, 0) + n
                first_hit.setdefault(nm, (i, round(x, 1), round(y, 1), round(z, 1)))
            nfr += 1
        tot = sum(surf.values()) or 1
        lines.append("      under the centre line: " + ", ".join(f"{k} {100 * v // tot}%" for k, v in sorted(surf.items(), key=lambda kv: -kv[1])[:5]))
        lines.append(f"      ground: worst offset {worst_dy:+.2f} blocks" + (f" at {worst_at}" if abs(worst_dy) > 0.01 else "")
                     + f"; blocks inside the car's box over {nfr} frames: {hits_total if hits_total else 'none'}")
        if abs(worst_dy) > 0.75:
            report.warn(f"route {r.name}: the model is up to {worst_dy:+.2f} blocks off the ground (at x,y,z,frame {worst_at})")
        if hits_total:
            report.warn(f"route {r.name}: solid blocks inside the car's box: {dict(sorted(hits_total.items(), key=lambda kv: -kv[1])[:6])}; "
                        f"first at (frame, x, y, z) {dict(list(first_hit.items())[:6])}")
    return lines


def main_check(ctx, out):
    report = Report()
    scenes_said = {}
    print("=" * 100)
    total = 0.0
    for scene in ctx.scenes:
        events, secs, said, timers = walk_scene(ctx, scene, report)
        scenes_said[scene.n] = said
        total += secs
        alt_report = []
        for name, spec in scene.sim_paths.items():
            ev2, secs2, said2, _ = walk_scene(ctx, scene, report, take=set(spec["take"]))
            skip = spec.get("skip")
            key = lambda l: tuple(int(v) for v in l.split("."))
            expect = [l for l in said if not (skip and key(skip[0]) <= key(l) <= key(skip[1]))]
            if said2 != expect:
                report.error(f"scene {scene.n} path {name!r}: lines {said2} differ from the main path minus {skip}: {expect}")
            else:
                report.note(f"scene {scene.n} path {name!r}: {len(said2)} lines, in order, skipping exactly {skip[0]}-{skip[1]} ({secs2:.0f}s)" if skip
                            else f"scene {scene.n} path {name!r}: {len(said2)} lines ({secs2:.0f}s)")
            alt_report.append((name, secs2, ev2))
        print(f"SCENE {scene.n}: {scene.title}   nominal duration {secs:5.1f}s ({secs / 60:.1f} min)  [{len(scene.steps)} steps, {len(said)} lines]")
        for te, text in events:
            print(f"   {te:6.1f}s  {text}")
        for name, secs2, ev2 in alt_report:
            print(f"   -- path {name!r}: nominal duration {secs2:5.1f}s; the lines it says: " + ", ".join(e[1].split()[0] for e in ev2 if re.match(r"^\d\.\d\d ", e[1])))
        if timers:
            print("   timed effects beside the story: " + "; ".join(f"{tt:.1f}s {n[:40]}" for tt, n in sorted(timers)[:14]) + (" ..." if len(timers) > 14 else ""))
        print()
    print(f"all scenes: {total:.0f}s ({total / 60:.1f} min) of story with answers assumed {CFG.answer_est:.0f}s")
    check_lines(ctx, scenes_said, report)
    check_functions(out, ctx, report)
    check_sounds(out, report)
    check_quiet(ctx, out, report)
    check_descent(ctx, report)
    check_cards(ctx, out, report)
    waits_without_nudge(ctx, report)
    check_nudge_cadence(ctx, out, report)
    check_hush(ctx, out, report)
    check_music(ctx, out, report)
    check_encoding(ctx, out, report)
    check_prompt(out, report)
    check_relocations(ctx, out, report)
    check_commands(out, report)
    for l in check_routes(ctx, report):
        print(l)
    print("anchors used:", ", ".join(sorted(ctx.used_anchors)))
    missing = [a for a in ctx.used_anchors if a not in ctx.anchors]
    if missing:
        report.error(f"anchors that do not exist: {missing}")
    else:
        report.note(f"all {len(ctx.used_anchors)} anchors used exist in anchors.json")
    print("=" * 100)
    for n in report.notes:
        print("note   ", n)
    for w in report.warnings:
        print("warning", w)
    for e in report.errors:
        print("ERROR  ", e)
    print(f"{len(report.errors)} errors, {len(report.warnings)} warnings")
    return 1 if report.errors else 0
