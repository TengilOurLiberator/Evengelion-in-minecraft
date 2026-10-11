"""The scene description API and its compiler.

A scene is a Python function that records STEPS on a Scene object.  The compiler turns them into a tick-driven state
machine on the scoreboard objective `angel.story`:

    #scene   which scene is running          #step   index of the current step
    each step i is three functions:   angel:story/s<N>/e<i>  (enter, runs once)
                                      angel:story/s<N>/p<i>  (poll, runs every tick while step i is current)
                                      angel:story/s<N>/x<i>  (exit, advances to step i+1)
    angel:story/s<N>/poll dispatches to the poll of the current step through a binary tree.

Conditions (`Cond`) are lists of `execute` sub-commands ANDed together, so  `execute <cond> run function ...`  is valid.
"""
import math

from core import (blind, CAST_IDS, CFG, CHARACTERS, DISPLAY_NAMES, NS, OBJ, P, T, dispatch_tree, fn, num, sadd, sc, sset, ssub,
                  at_xyz, PA)


# --------------------------------------------------------------------------------------------------- conditions
class Cond:
    def __init__(self, frags, est=None, desc=""):
        self.frags = list(frags)
        self.est = est            # seconds the offline simulator assumes it takes for this to become true
        self.desc = desc

    def __and__(self, other):
        return Cond(self.frags + other.frags, max(self.est or 0, other.est or 0) or None, f"{self.desc} & {other.desc}")

    def text(self):
        return " ".join(self.frags)

    def __invert__(self):
        if len(self.frags) == 1 and self.frags[0].startswith("if "):
            return Cond(["unless " + self.frags[0][3:]], desc="not " + self.desc)
        raise ValueError("only a single `if` condition can be negated: " + self.text())


class C:
    """Condition builders."""

    @staticmethod
    def raw(text, est=None, desc=""):
        return Cond([text], est, desc or text)

    @staticmethod
    def near(x, y, z, r, est=None):
        return Cond([f"positioned {num(x)} {num(y)} {num(z)} if entity {P(f'distance=..{num(r)}')}"], est, f"player within {r} of ({num(x)},{num(y)},{num(z)})")

    @staticmethod
    def score(name, rng, est=None):
        return Cond([sc(name, rng)], est, f"{name} in {rng}")

    @staticmethod
    def flag(name, est=None):
        return Cond([sc(f"#f.{name}", "1")], est, f"flag {name}")

    @staticmethod
    def entity(sel, est=None):
        return Cond([f"if entity {sel}"], est, f"entity {sel}")

    @staticmethod
    def not_talking():
        return Cond([sc("#talking", "0")], None, "no line playing")

    @staticmethod
    def data(sel, path, est=None):
        return Cond([f"if data entity {sel} {path}"], est, f"data {path}")


class Nudges:
    """Reminders run while a wait goes on (the player says nothing): `cmds[k]` is a list of commands, run in order; the first after `first`
    seconds of waiting, then one every `repeat` seconds (never while a recorded line plays or the bridge is speaking: it tries again a
    second later); after the last one the series goes on from index `loop_from` (default 1: 0, 1, 2, 1, 2, 1, 2 ...).
    `lines`: the recorded lines the first pass of the nudges says, for the offline checker."""

    def __init__(self, first, repeat, cmds, loop_from=1, lines=()):
        self.first, self.repeat, self.cmds, self.loop_from, self.lines = first, repeat, [list(c) for c in cmds], loop_from, list(lines)

    def nominal(self):
        """seconds until the player agrees after the first pass of the nudges (for the checker's estimate)"""
        return self.first + self.repeat * max(0, len(self.cmds) - 1) + 3.0

    def next_index(self, k):
        return k + 1 if k + 1 < len(self.cmds) else self.loop_from


# --------------------------------------------------------------------------------------------------- steps
class Step:
    def __init__(self, kind, **kw):
        self.kind = kind
        self.__dict__.update(kw)
        self.index = None
        self.note = kw.get("note", "")


class Scene:
    """Records the steps of one scene.  Every method appends a step and returns the Scene (so calls can be chained)."""

    def __init__(self, n, title, ctx):
        self.n = n
        self.title = title
        self.ctx = ctx
        self.steps = []
        self.labels = {}
        self.extra_functions = {}      # name -> lines, written under story/s<n>/
        self._last_char = None         # id of the last character who spoke (for the wait prompt)
        self._fcount = 0
        self.scheduled = []            # function paths used with `schedule`, cleared by halt
        self.sim_paths = {}            # name -> dict(take=[labels], skip=("5.25", "5.41")): alternative routes the checker also walks

    # ----------------------------------------------------------------------------------- bookkeeping
    def _add(self, step):
        step.index = len(self.steps)
        self.steps.append(step)
        return self

    def label(self, name):
        """Name the position of the next step (target for goto / branch)."""
        if name in self.labels:
            raise ValueError(f"scene {self.n}: label {name!r} defined twice")
        self.labels[name] = len(self.steps)
        return self

    def function(self, name, lines):
        """A reusable function of this scene; returns the command that calls it."""
        if isinstance(lines, str):
            lines = [lines]
        self.extra_functions[name] = list(lines)
        return fn(f"story/s{self.n}/f_{name}")

    def _anon(self, lines, prefix="f"):
        self._fcount += 1
        name = f"{prefix}{self._fcount}"
        self.extra_functions[name] = list(lines)
        return name

    # ----------------------------------------------------------------------------------- instant steps
    def do(self, *cmds, note=""):
        """Run commands (as the server, no position) and go straight on."""
        flat = []
        for c in cmds:
            flat += c if isinstance(c, (list, tuple)) else [c]
        return self._add(Step("do", cmds=flat, note=note))

    def beat(self, n):
        """Set the story beat (characters/beats.md)."""
        return self.do(sset("#beat", n), note=f"beat {n}")

    def present(self, **who):
        """present(misato=1, ritsuko=2, gendo=0, rei=0): 0 absent, 1 in person, 2 voice only."""
        cmds = [sset(f"#present_{k}", v) for k, v in who.items()]
        return self.do(*cmds, note="present " + ",".join(f"{k}={v}" for k, v in who.items()))

    def flag(self, name, value=1):
        return self.do(sset(f"#f.{name}", value), note=f"flag {name}={value}")

    def after(self, sec, *cmds, note=""):
        """Run commands `sec` seconds from now WITHOUT waiting (a timed effect running beside the story).  Cleared by halt."""
        flat = []
        for c in cmds:
            flat += c if isinstance(c, (list, tuple)) else [c]
        name = self._anon(flat, "a")
        path = f"story/s{self.n}/f_{name}"
        self.scheduled.append(path)
        return self._add(Step("after", sec=sec, path=path, cmds=flat, note=note))

    def goto(self, label):
        return self._add(Step("goto", label=label))

    def branch(self, cond, label):
        """If `cond` holds go to `label`, otherwise carry on with the next step."""
        return self._add(Step("branch", cond=cond, label=label))

    # ----------------------------------------------------------------------------------- waiting steps
    def sleep(self, sec, note=""):
        return self._add(Step("sleep", sec=sec, note=note))

    def say(self, lid, gap=None):
        """Play recorded line `lid` ("1.04") and go on when it has finished plus `gap` seconds of silence (default 0.4)."""
        ln = self.ctx.lines[lid]
        self._add(Step("say", lid=lid, line=ln, note=f"{lid} {ln.speaker}"))
        if ln.speaker in CHARACTERS:
            self._last_char = ln.speaker
        g = CFG.gap if gap is None else gap
        if g > 0:
            self._add(Step("sleep", sec=g, note="gap", gap=True))
        return self

    def wait_answer(self, speaker=None, prompt=None, timeout=None, est=None, note="", **kw):
        """Hold the story (#wait = 1) until the player has said something and the bridge has had the character answer.
        `speaker`: who is being answered (default: the last character who spoke); `prompt`: text after the dash, e.g.
        "answer Misato"; `timeout`: seconds after which the story goes on anyway (default: the global setting, off).
        Extra keywords: see `_wait` (`nudges`)."""
        return self._wait(1, speaker, prompt, timeout, est, note, **kw)

    def wait_consent(self, speaker=None, prompt="will you pilot it?", timeout=None, est=None, note="", **kw):
        """Hold the story (#wait = 2) until the player agrees (angel:story/consented).
        Extra keywords (see `_wait`): `answer_ends=True` makes the wait end WITHOUT consent (#consent stays 0) as soon as the bridge has
        voiced a reply to something the player said that was not a yes; `nudges=Nudges(...)` runs a series of nudges while it waits."""
        return self._wait(2, speaker, prompt, timeout, est, note, **kw)

    def _wait(self, mode, speaker, prompt, timeout, est, note, answer_ends=False, nudges=None):
        spk = speaker or self._last_char or "misato"
        if spk not in CHARACTERS:
            raise ValueError(f"wait speaker must be one of {CHARACTERS}, not {spk!r}")
        if prompt is None:
            prompt = f"answer {DISPLAY_NAMES[spk]}"
        variant = self.ctx.prompt_variant(prompt)
        if nudges is not None and est is None:
            est = nudges.nominal()
        return self._add(Step("wait", mode=mode, speaker=spk, prompt=prompt, variant=variant, timeout=timeout,
                              est=est if est is not None else CFG.answer_est, note=note or f"WAIT {mode} {spk}",
                              answer_ends=answer_ends, nudges=nudges))

    def until(self, cond, timeout=None, on_timeout=None, est=None, hint=None, hint_after=40, nag=None, note="", on_done=None, tick=None):
        """Wait until `cond` (a Cond, or a list of alternative Conds: any one will do) holds.
        timeout:    seconds after which `on_timeout` (list of commands) runs and the story goes on (nothing may soft-lock);
        hint:       (actionbar text, [extra commands]) shown once after `hint_after` seconds of waiting;
        nag:        (first_seconds, repeat_seconds_or_None, [commands]) run when the player is slow (not while a line plays);
        on_done:    commands run when the condition becomes true or the timeout hits (before the next step);
        tick:       commands run every tick before the condition is looked at (to refresh a score the condition reads)."""
        conds = cond if isinstance(cond, (list, tuple)) else [cond]
        if est is None:
            est = min((c.est for c in conds if c.est is not None), default=CFG.answer_est)
        return self._add(Step("until", conds=list(conds), timeout=timeout, on_timeout=on_timeout or [], est=est, hint=hint,
                              hint_after=hint_after, nag=nag, on_done=on_done or [], tick=tick or [],
                              note=note or " | ".join(c.desc for c in conds)))

    def setup_done(self):
        """Mark the end of the steps that (re)build the scene's starting state.  A jump (`angel:story/scene {n:N}`) runs them all;
        a hand-over from the previous scene (`angel:story/sN/cont`) starts after them, because the state is already standing."""
        self.setup_end = len(self.steps)
        return self

    def next_scene(self, n, jump=False):
        """Hand over to scene n: by default seamlessly (`cont`, state carried over); jump=True rebuilds it (`angel:story/scene {n:N}`),
        which is what to use when the next scene starts somewhere else."""
        cmd = f"function {NS}:story/scene {{n:{n}}}" if jump else fn(f"story/s{n}/cont")
        return self._add(Step("handover", cmds=[cmd], to=n, jump=jump, note=f"-> scene {n} ({'rebuilt' if jump else 'continued'})"))

    # ----------------------------------------------------------------------------------- convenience
    def fade(self, cmds=(), black=1.5, rest=0.0, note="fade"):
        """A short fade through darkness around `cmds`, which run once the picture is dark.
        The blindness effect darkens at once and fades back over the last second of its duration; nothing is rotated or moved
        under the player's head except while it is dark.  Story time taken = black + 1.0 (the fade-in) + rest seconds."""
        black = max(black, 0.6)
        self.do(blind(black + 1.0), note=note + " (to dark)")
        self.sleep(0.4, note=note + " (dark)")
        if cmds:
            self.do(*cmds, note=note + " (in the dark)")
        self.sleep(black - 0.4 + 1.0 + rest, note=note + " (fade in)")
        return self

    def sim_path(self, name, take, skip=None):
        """Tell the offline checker about an alternative route through the scene: the labels whose `branch` is taken, and the span of
        lines (first, last) that route skips ("5.25", "5.41").  The checker walks it too and verifies exactly that."""
        self.sim_paths[name] = dict(take=list(take), skip=skip)
        return self

    # ----------------------------------------------------------------------------------- sound and cards
    def bed(self, key, note=""):
        """Start the ambience bed angel:amb.<key> (the bed in play stops first); None stops the bed."""
        cmds = self.ctx.audio.start("bed", key) if key else self.ctx.audio.stop("bed")
        return self.do(*cmds, note=note or (f"bed {key}" if key else "bed off"))

    def music(self, key, note=""):
        """Start the music cue angel:music.<key> (the cue in play stops first); None stops the music."""
        cmds = self.ctx.audio.start("music", key) if key else self.ctx.audio.stop("music")
        return self.do(*cmds, note=note or (f"music {key}" if key else "music off"))

    def loop(self, key, note=""):
        """Start the repeating effect layer angel:sfx.<key> (an alarm); None stops it."""
        cmds = self.ctx.audio.start("loop", key) if key else self.ctx.audio.stop("loop")
        return self.do(*cmds, note=note or (f"loop {key}" if key else "loop off"))

    def sfx(self, event, at=None, vol=1.0, pitch=1.0, minvol=0.0, note=""):
        from audio import sfx
        return self.do(sfx(event, at, vol, pitch, minvol), note=note or event)

    def card(self, text, small=None, hold=3.5, sound="sfx.card", font=None, bold=True, color="white"):
        """A title card, white capitals on black, readable in VR and on a flat screen (cards.py).  Takes about hold + 1.5 s."""
        from cards import card_index
        from audio import sfx as _sfx
        k = card_index(self.ctx, text, small, font, bold, color)
        self.do(blind(hold + 5), note=f"card {text!r}: to black")
        self.sleep(0.5, note="card: dark")
        self.do(fn("story/card/bg"), f"effect clear {PA()} minecraft:blindness", note="card: the black room, blindness off")
        self.sleep(0.35, note="card: black")
        self.do(_sfx(sound), fn(f"story/card/c{k}"), note=f"card: hit, then the text {text!r}")
        self.sleep(hold, note="card: held in silence")
        self.do(fn("story/card/off_text"), blind(3), fn("story/card/off"), note="card: text away, dark, room away")
        self.sleep(0.6, note="card: dark")
        return self

    def say_all(self, *lids):
        for l in lids:
            self.say(l)
        return self


# --------------------------------------------------------------------------------------------------- compiling
class Compiler:
    def __init__(self, out, ctx):
        self.out = out
        self.ctx = ctx

    def adv(self, scene, j):
        if j >= len(scene.steps):
            return [sset("#step", -1), f"# end of scene {scene.n}"]
        return [sset("#step", j), fn(f"story/s{scene.n}/e{j}")]

    def compile(self, scene):
        n = scene.n
        steps = scene.steps
        out = self.out
        polls = {}
        for st in steps:
            i = st.index
            base = f"story/s{n}"
            enter = [sset("#force", 0)]
            poll = None
            exit_pre = []
            k = st.kind
            nxt = i + 1
            if k == "do":
                enter += st.cmds
                enter += self.adv(scene, nxt)
            elif k == "handover":
                enter += st.cmds           # the next scene takes over #step; nothing here may touch it afterwards
            elif k == "after":
                enter += [f"schedule function {NS}:{st.path} {max(1, T(st.sec))}t"]
                out.function(st.path, st.cmds)
                enter += self.adv(scene, nxt)
            elif k == "goto":
                enter += self.adv(scene, scene.labels[st.label])
            elif k == "branch":
                pre = [sset("#br", 0), f"execute {st.cond.text()} run {sset('#br', 1)}"]
                out.function(f"{base}/b{i}", self.adv(scene, scene.labels[st.label]))
                enter += pre + [f"execute if score #br {OBJ} matches 1 run function {NS}:{base}/b{i}",
                                f"execute if score #br {OBJ} matches 0 run function {NS}:{base}/b{i}n"]
                out.function(f"{base}/b{i}n", self.adv(scene, nxt))
            elif k == "sleep":
                enter += [sset("#sleep", max(1, T(st.sec)))]
                poll = [ssub("#sleep"), f"execute {sc('#sleep', '..0')} run function {NS}:{base}/x{i}"]
            elif k == "say":
                enter += [fn(f"say/{st.line.key}")]
                poll = [f"execute {sc('#talking', '0')} run function {NS}:{base}/x{i}"]
            elif k == "wait":
                enter += [sset("#wait", st.mode), sset("#speaker", CHARACTERS.index(st.speaker) + 1), sset("#pk", st.variant),
                          sset("#wt", T(st.timeout) if st.timeout else -1)]
                if not st.timeout:
                    enter += [f"execute {sc('#timeout_s', '1..')} run function {NS}:story/wt_global"]
                poll = [f"execute {sc('#wait', '0')} run function {NS}:{base}/x{i}",
                        f"execute if score #step {OBJ} matches {i} {sc('#wait', '1..')} {sc('#wt', '0..')} run function {NS}:story/wait_tick"]
                exit_pre = [sset("#wait", 0)]
                bsp = f"score #bridge_speaking {OBJ} matches 1.."
                if getattr(st, "answer_ends", False):
                    # a consent-capable wait that also ends, without consent, once the bridge has voiced an answer to something the
                    # player said that was not a yes: #bsa is -1 (the bridge was already speaking at the start: ignore that), 0 (armed),
                    # 1 (it has started to answer)
                    enter += [sset("#bsa", 0), f"execute if {bsp} run {sset('#bsa', -1)}"]
                    poll += [f"execute if score #step {OBJ} matches {i} if score #bsa {OBJ} matches -1 unless {bsp} run {sset('#bsa', 0)}",
                             f"execute if score #step {OBJ} matches {i} if score #bsa {OBJ} matches 0 if {bsp} run {sset('#bsa', 1)}",
                             f"execute if score #step {OBJ} matches {i} if score #bsa {OBJ} matches 1 unless {bsp} run {sset('#wait', 0)}"]
                nud = getattr(st, "nudges", None)
                if nud is not None:
                    enter += [sset("#nagt", 0), sset("#nagi", 0)]
                    # the nudge series: gate (a line or the bridge is speaking: try again in a second), then the body of the current index
                    out.function(f"{base}/n{i}", [
                        f"execute {sc('#talking', '0')} unless {bsp} run function {NS}:{base}/nn{i}",
                        f"execute {sc('#talking', '1')} run {sset('#nagt', T(nud.first) - 20)}",
                        f"execute if {bsp} run {sset('#nagt', T(nud.first) - 20)}"])
                    body = [f"scoreboard players operation #nk {OBJ} = #nagi {OBJ}"]
                    for kk in range(len(nud.cmds)):
                        body.append(f"execute {sc('#nk', str(kk))} run {sset('#nagi', nud.next_index(kk))}")
                    for kk in range(len(nud.cmds)):
                        body.append(f"execute {sc('#nk', str(kk))} run function {NS}:{base}/nb{i}_{kk}")
                    body.append(sset("#nagt", T(nud.first) - T(nud.repeat)))
                    out.function(f"{base}/nn{i}", body)
                    for kk, cmds_ in enumerate(nud.cmds):
                        out.function(f"{base}/nb{i}_{kk}", cmds_)
                    poll += [sadd("#nagt"),
                             f"execute if score #step {OBJ} matches {i} {sc('#nagt', str(T(nud.first)))} run function {NS}:{base}/n{i}"]
            elif k == "until":
                enter += [sset("#stept", 0), sset("#nagt", 0), sset("#hinted", 0)]
                poll = list(st.tick)
                first_cond = True
                for c in st.conds:
                    guard = "" if first_cond else f"if score #step {OBJ} matches {i} "
                    first_cond = False
                    poll.append(f"execute {guard}{c.text()} run function {NS}:{base}/x{i}")
                poll.append(sadd("#stept"))
                poll.append(sadd("#nagt"))
                if st.timeout:
                    out.function(f"{base}/t{i}", st.on_timeout + [f"function {NS}:{base}/x{i}"])
                    poll.append(f"execute if score #step {OBJ} matches {i} {sc('#stept', str(T(st.timeout)))} run function {NS}:{base}/t{i}")
                if st.hint:
                    text, extra = st.hint if isinstance(st.hint, (tuple, list)) else (st.hint, [])
                    hl = [f"title {PA()} actionbar " + _text(text, "gray")] + list(extra)
                    out.function(f"{base}/h{i}", hl)
                    poll.append(f"execute if score #step {OBJ} matches {i} {sc('#stept', str(T(st.hint_after)))} run function {NS}:{base}/h{i}")
                if st.nag:
                    first, repeat, cmds = st.nag
                    # the nag only speaks when no other line is playing; otherwise it tries again in a second
                    body = list(cmds)
                    out.function(f"{base}/n{i}", [f"execute {sc('#talking', '0')} run function {NS}:{base}/nn{i}",
                                                  f"execute {sc('#talking', '1')} run {sset('#nagt', T(first) - 20)}"])
                    out.function(f"{base}/nn{i}", body + ([sset("#nagt", T(first) - T(repeat))] if repeat else [sset("#nagt", -999999)]))
                    poll.append(f"execute if score #step {OBJ} matches {i} {sc('#nagt', str(T(first)))} run function {NS}:{base}/n{i}")
                exit_pre = list(st.on_done)
            else:
                raise ValueError(f"unknown step kind {k}")
            if poll is not None:
                poll.append(f"execute if score #step {OBJ} matches {i} {sc('#force', '1')} run function {NS}:{base}/x{i}")
                out.function(f"{base}/p{i}", poll)
                out.function(f"{base}/x{i}", exit_pre + self.adv(scene, nxt))
                polls[i] = [fn(f"{base}/p{i}")]
            out.function(f"{base}/e{i}", enter)
        dispatch_tree(out, f"story/s{n}/pt", "#step", polls)
        out.function(f"story/s{n}/poll", [fn(f"story/s{n}/pt/root")])
        for name, lines in scene.extra_functions.items():
            out.function(f"story/s{n}/f_{name}", lines)
        # begin: a clean slate, then step 0.  `angel:story/scene {n:N}` calls this.
        out.function(f"story/s{n}/begin", [fn("story/halt"), sset("#scene", n), sset("#step", 0), sset("#running", 1),
                                           sset("#wait", 0), sset("#talking", 0), sset("#line_left", 0),
                                           sset("#mv.on", 0), sset("#ride", 0),
                                           fn(f"story/s{n}/e0") if steps else "# (empty scene)"])
        # cont: the previous scene left the state standing; carry on after the setup steps
        k = getattr(scene, "setup_end", 0) or 0
        if k < len(steps):
            out.function(f"story/s{n}/cont", [sset("#scene", n), sset("#running", 1), sset("#wait", 0), sset("#step", k), fn(f"story/s{n}/e{k}")])
        else:
            out.function(f"story/s{n}/cont", [sset("#scene", n), sset("#step", -1), "# (nothing after the setup)"])


def _text(s, color="white"):
    import json
    return json.dumps({"text": s, "color": color}, ensure_ascii=False)

