"""The objective system: in-world directions ("what do I do now?") for every place where the story waits for the PLAYER to do something.

    from objective import Objective, objective, Ahead, HOW

    s.until(C.near(...), objective=objective("Pick up the phone", at=(x, y, z), line="Walk up to the phone - it picks up by itself"))
    s.objective_on(objective("Follow Misato", at="@e[type=minecraft:mannequin,tag=angel.misato,limit=1]", far=8, still=10))   # a block of steps
    s.objective_off()

An objective is ONE thing at a time (the story is serial).  While it is current it shows, after a short grace (default 2 s, so it does not flash
for a step the player completes at once):

  a) a WAYPOINT at the target (`at`): a floating label (text_display: the objective's `text`, pale yellow, a soft gold triangle under it, billboard,
     see_through so it reads through walls, 25 % black behind it), and a thin vertical beam of translucent white glass (block_display, 70 tall, so it
     stands over the roofs and can be found from behind buildings) with a spark of light at its foot now and then.  Both are re-scaled every 5 ticks
     from the player's distance (17 bands, 1.5 to 120 blocks): the label is kept at about one degree of visual angle (scale 0.1 x distance, between
     0.5 and 12), the beam gets wider the farther it is, so both read from 5 to 80 blocks and neither is huge up close.  The target is an
     `angel.ob_target` marker: a fixed point, or it follows an entity (`at` is a selector: the car, Misato) -- the waypoint rides on it.
  b) a DIRECTION LINE: a short sentence in a world-space panel (one text_display, billboard, the speak prompt's look) 2 m ahead of the player at chest
     height, in the direction he is looking when it is made (computed once: it does not follow his head).  It starts with a small arrow that says
     where the target is relative to where he faces (up = ahead, right, left, "behind you"); on the repeat the second line names the controls
     (`how`).  It stays `secs` seconds (5), and comes again, with a soft chime, whenever the distance to the target has not got smaller for
     `repeat` seconds (15).  If a character stands where it would hang it is lowered to the chest.  On a flat screen the sentence also goes
     on the action bar (not when `function angel:story/controls_vr` was called).
  c) a soft chime when it appears: angel:sfx.speak_chime at pitch 0.62 and volume 0.35 (the speak prompt is pitch 1.0 and 0.6), not inside a
     hush.

Never more than one instruction panel: a new line, the speak prompt (which removes the line), a title card and a new objective all remove the
previous one.  Everything carries the tags angel.story + angel.objective and is removed at the step's exit, by halt/stop, and at load.

Gated objectives (`far=8`, `still=10`): "Follow Misato" shows nothing until the player is more than 8 blocks from the target, or has stood still for 10 s.

The controls wording (`how`, `line` may be a triple (both, vr, flat)): the server cannot tell whether the player is in VR (Vivecraft's server
mod keeps that in Java only: see README), so the default wording covers both; `function angel:story/controls_vr` / `controls_flat` /
`controls_both` (score #ctl 1 / 2 / 0) narrow it.  Controls named are the Oculus Touch defaults (assets/vivecraft/input/oculus_defaults.json).
"""
import json

from core import CFG, NS, OBJ, P, PA, T, TAG, dispatch_tree, fn, fnum, num, sadd, sc, sset, ssub

OBTAG = "angel.objective"
BG = 1711276032                       # 40 % black: the speak prompt's background
BG_WP = 1073741824                    # 25 % black behind the waypoint label
PALE = "#fff3c4"                      # pale yellow-white
GOLD = "#e8c25a"
GREY = "#c4cad6"
THR = (1.5, 2.5, 3.5, 5.0, 6.5, 8.0, 10.0, 13.0, 17.0, 22.0, 28.0, 36.0, 46.0, 58.0, 75.0, 95.0, 120.0)     # band edges in blocks (band k: beyond THR[k-1], within THR[k])
LINE_SCALE = 0.45                     # the direction line: letters ~9 cm tall at 2 m (2.4 degrees)
LINE_DIST, LINE_DROP = 2.0, 0.4       # 2 m ahead, 0.4 below the eyes (chest)
LINE_WIDTH = 170                      # px before the sentence wraps
FOREVER = 20 * 3600

ARROW = {0: "↑ ", 1: "→ ", 2: "← ", 3: "↻ behind you: "}       # ahead, right, left, behind  (-1: no target, no arrow)

# the controls, in the words of the Oculus Touch defaults (right-handed), as (both, vr, flat)
HOW = {
    "walk": ("Walk: left thumbstick (keyboard: W A S D)", "Walk: left thumbstick", "Walk: W A S D"),
    "look": ("Look: just turn your head (mouse: move the mouse)", "Look: just turn your head", "Look: move the mouse"),
    "hit": ("Swing your hand at it - or press the right trigger (mouse: left click)", "Swing your hand at it - or squeeze the right trigger",
            "Left click on it"),
}


class Ahead:
    """A target made once, when the objective begins, relative to where the player stands and looks (the tutorial's sample light)."""
    def __init__(self, dist=6.0, side=0.0, up=-1.6):
        self.dist, self.side, self.up = dist, side, up

    def __repr__(self):
        return f"Ahead({self.dist},{self.side},{self.up})"


class Objective:
    """text: the waypoint label (and the default sentence); line: the direction-line sentence (str or (both, vr, flat)); how: the controls line
    (a key of HOW, a str or a triple), shown on the repeat (or always with first_how); at: None | (x, y, z) | "@e[...]" (follows) | Ahead;
    grace: seconds before it shows; far / still: gate it (only when more than `far` blocks from the target, or standing still `still` s);
    waypoint / lines: switch either off; bearing: the arrow; giant: scale factor for the panel (the 16x giant of scene 7); repeat, secs: seconds."""

    def __init__(self, text, at=None, line=None, how=None, grace=None, waypoint=True, lines=True, bearing=True, giant=1, repeat=None, secs=None,
                 sound=True, far=None, still=None, lift=0.0, first_how=False, generic=False):
        self.text = text
        self.at = at
        self.line = line if line is not None else text
        self.how = HOW[how] if isinstance(how, str) and how in HOW else how
        import pace
        cap = pace.PACE.ob_grace_cap                          # the video pacing shows even the objectives that had a long grace within 3 s
        self.grace = CFG.ob_grace if grace is None else (float(grace) if cap is None else min(float(grace), cap))
        self.waypoint = bool(waypoint) and at is not None
        self.lines = lines
        self.bearing = bearing and at is not None
        self.giant = giant
        self.repeat = CFG.ob_repeat if repeat is None else float(repeat)
        self.secs = CFG.ob_line_secs if secs is None else float(secs)
        self.sound = sound
        self.far, self.still = far, still
        self.lift = lift
        self.first_how = first_how
        self.generic = generic

    def key(self):
        return repr(sorted((k, repr(v)) for k, v in self.__dict__.items()))

    @property
    def gated(self):
        return self.far is not None or self.still is not None

    def follows(self):
        return isinstance(self.at, str)

    def target_desc(self):
        if self.at is None:
            return "(no target)"
        if isinstance(self.at, str):
            import re
            m = re.search(r"tag=(angel\.[a-z_]+)", self.at)
            return "follows " + (m.group(1) if m else self.at)
        if isinstance(self.at, Ahead):
            return "ahead of the player"
        return "(%g, %g, %g)" % tuple(self.at)

    def texts(self, c):
        """(sentence, controls line or None) for the control scheme c (0 both, 1 vr, 2 flat)"""
        def pick(v):
            return v if v is None or isinstance(v, str) else v[c]
        return pick(self.line), pick(self.how)


def objective(text, at=None, **kw):
    return Objective(text, at, **kw)


def follow_objective(who, text=None, line=None):
    """'Follow Misato' / 'Follow Dr. Akagi' attached to the character: shows only when he is more than 8 blocks behind her or has stood still for 10 s."""
    name = {"misato": "Misato", "ritsuko": "Dr. Akagi", "gendo": "your father", "rei": "Rei"}[who]
    return Objective(text or f"Follow {name}", at=f"@e[type=minecraft:mannequin,tag=angel.{who},limit=1]",
                     line=line or f"{text or 'Follow ' + name} - just walk after her", how="walk", grace=0.0, far=8.0, still=10.0)


def note_panel(lines, signature):
    """The photograph's note as a readable floating note: a pale panel, dark italic text, signed.  Returns the command that makes it (kill with
    `kill @e[tag=angel.ob_note]`); it hangs 1.7 m ahead of where he is looking at that moment, a little below the eyes, and does not follow his head."""
    parts = []
    for ln in lines:
        parts.append({"text": ln + "\n", "color": "#2a2630", "italic": True})
    parts.append({"text": signature, "color": "#5a4638", "italic": True})
    bg = (0xE6 << 24) | 0xF1E7D0
    bg -= 1 << 32 if bg >= 1 << 31 else 0
    s = 0.5
    return (f'execute as {P()} at @s anchored eyes positioned ^ ^-0.2 ^1.7 run summon minecraft:text_display ~ ~ ~ '
            f'{{Tags:["{TAG}","{OBTAG}","angel.ob_note"],billboard:"center",background:{bg},brightness:{{sky:15,block:15}},line_width:150,shadow:0b,'
            f'see_through:0b,view_range:0.6f,alignment:"center",text:{json.dumps(parts, ensure_ascii=True)},'
            f'transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[{s}f,{s}f,{s}f],right_rotation:[0f,0f,0f,1f]}}}}')


def _tf(tx, ty, tz, sx, sy, sz):
    return (f"transformation:{{translation:[{fnum(tx)},{fnum(ty)},{fnum(tz)}],left_rotation:[0f,0f,0f,1f],"
            f"scale:[{fnum(sx)},{fnum(sy)},{fnum(sz)}],right_rotation:[0f,0f,0f,1f]}}")


def _comp(parts):
    return json.dumps(parts, ensure_ascii=True)


def band_scale(b):
    """label scale in band b"""
    d = THR[b] if b < len(THR) else THR[-1] * 1.2
    return max(0.5, min(12.0, 0.1 * d))


def beam_width(b):
    d = THR[b] if b < len(THR) else THR[-1] * 1.2
    return 0.03 + 0.006 * d


# --------------------------------------------------------------------------------------------------- generation
def register_load(ctx):
    """Called from system.build_system: the scoreboard constants and defaults the objective system needs."""
    return []


def build_objectives(out, ctx):
    objs = ctx.objectives
    facs = sorted({o.giant for o in objs} | {1})
    NB = len(THR) + 1                                  # bands 0..len(THR); 99 = no target
    A = "angel.objective"
    tgt = "@e[tag=angel.ob_target,limit=1]"
    ob = lambda name: f"function {NS}:story/ob/{name}"

    # ---- begin / end
    out.function("story/ob/end", [f"kill @e[tag={OBTAG}]", sset("#ob.on", 0), sset("#ob.shown", 0), sset("#ob.line", -1)])
    for k, o in enumerate(objs):
        out.function(f"story/ob/b{k}", [
            fn("story/ob/end"),
            sset("#ob.on", 1), sset("#ob.k", k), sset("#ob.t", 0), sset("#ob.g", T(o.grace)), sset("#ob.shown", 0),
            sset("#ob.vis", 0 if o.gated else 1), sset("#ob.gate", 1 if o.gated else 0), sset("#ob.wp", 1 if o.waypoint else 0),
            sset("#ob.fl", 1 if o.follows() else 0), sset("#ob.hast", 1 if o.at is not None else 0), sset("#ob.bb", 9999), sset("#ob.b", 99), sset("#ob.bl", -1), sset("#ob.np", 0),
            sset("#ob.line", -1), sset("#ob.rn", 0), sset("#ob.gf", o.giant), sset("#ob.rep", T(o.repeat)), sset("#ob.secs", T(o.secs)),
            sset("#ob.stillt", T(o.still) if o.still else 99999999), sset("#ob.sn", 0), sset("#ob.snd", 1 if o.sound else 0),
            sset("#ob.nl", 1 if o.lines else 0), sset("#ob.dir", -1), sset("#stk", 0), sset("#stkh", 0),
            sset("#ob.px0", -99999999), sset("#ob.pz0", -99999999),
            ob("td/root")])

    # ---- the target marker (one per objective), its following, and the dispatch trees
    marker = f'{{Tags:["{TAG}","{A}","angel.ob_target"]}}'
    td, fd, wd, ld, bd = {}, {}, {}, {}, {}
    for k, o in enumerate(objs):
        if o.at is None:
            out.function(f"story/ob/t{k}", ["# (no target)"])
        elif isinstance(o.at, str):
            out.function(f"story/ob/t{k}", [f"execute at {o.at} run summon minecraft:marker ~ ~ ~ {marker}"])
            out.function(f"story/ob/f{k}", [f"tp @e[tag=angel.ob_target] {o.at}"])
            fd[k] = [fn(f"story/ob/f{k}")]
        elif isinstance(o.at, Ahead):
            a = o.at
            out.function(f"story/ob/t{k}", [f"execute as {P()} at @s anchored eyes positioned ^{num(a.side)} ^{num(a.up)} ^{num(a.dist)} run summon minecraft:marker ~ ~ ~ {marker}"])
        else:
            x, y, z = o.at
            out.function(f"story/ob/t{k}", [f"summon minecraft:marker {num(x)} {num(y)} {num(z)} {marker}"])
        td[k] = [fn(f"story/ob/t{k}")]
        # the waypoint label
        if o.waypoint:
            parts = [{"text": o.text, "color": PALE}, {"text": "\n▼", "color": GOLD}]
            out.function(f"story/ob/w{k}", [
                f'summon minecraft:text_display ~ ~ ~ {{Tags:["{TAG}","{A}","angel.ob_wp","angel.ob_label"],billboard:"center",background:{BG_WP},'
                f'brightness:{{sky:15,block:15}},line_width:260,shadow:1b,see_through:1b,view_range:3.0f,teleport_duration:5,interpolation_duration:5,'
                f'text:{_comp(parts)},{_tf(0, 1.0 + o.lift, 0, 0.5, 0.5, 0.5)}}}'])
            wd[k] = [fn(f"story/ob/w{k}")]
        # the direction line (variants: first/repeat x controls x bearing) and the action-bar text
        out.function(f"story/ob/l{k}", _line_function(o))
        ld[k] = [fn(f"story/ob/l{k}")]
        bar = []
        for c in (0, 2):
            sentence, _ = o.texts(c)
            bar.append(f"execute if score #ctl {OBJ} matches {c} run title {PA()} actionbar " + json.dumps({"text": sentence, "color": "gray"}, ensure_ascii=True))
        out.function(f"story/ob/a{k}", bar)
        bd[k] = [fn(f"story/ob/a{k}")]
    dispatch_tree(out, "story/ob/td", "#ob.k", td)
    dispatch_tree(out, "story/ob/fd", "#ob.k", fd)
    dispatch_tree(out, "story/ob/wd", "#ob.k", wd)
    dispatch_tree(out, "story/ob/ld", "#ob.k", ld)
    dispatch_tree(out, "story/ob/bd", "#ob.k", bd)

    # ---- the waypoint's beam, its bands
    out.function("story/ob/wp_spawn", [
        ob("wd/root"),
        f'summon minecraft:block_display ~ ~ ~ {{Tags:["{TAG}","{A}","angel.ob_wp","angel.ob_beam"],block_state:"minecraft:white_stained_glass",'
        f'brightness:{{sky:15,block:15}},view_range:4.0f,teleport_duration:5,interpolation_duration:5,{_tf(-0.05, -0.5, -0.05, 0.1, 70, 0.1)}}}'])
    out.function("story/ob/band_apply_label", _band_label_lines(NB))
    out.function("story/ob/band_apply_beam", [
        f"execute if score #ob.b {OBJ} matches {b}{'' if b < NB - 1 else '..'} run data merge entity @e[tag=angel.ob_beam,limit=1] {{start_interpolation:0,interpolation_duration:5,"
        f"{_tf(-beam_width(b) / 2, -0.5, -beam_width(b) / 2, beam_width(b), 70, beam_width(b))}}}" for b in range(NB)])
    out.function("story/ob/band_apply", [ob("band_apply_label"), ob("band_apply_beam"), f"scoreboard players operation #ob.bl {OBJ} = #ob.b {OBJ}"])

    # ---- the distance band, the player's stillness
    band = [sset("#ob.b", 0)]
    for i, t in enumerate(THR):
        band.append(f"execute unless entity @e[tag=angel.ob_target,distance=..{t:g},limit=1] run {sset('#ob.b', i + 1)}")
    out.function("story/ob/band", band)
    out.function("story/ob/measure", [
        sset("#ob.b", 99),
        f"execute if entity {tgt} as {P()} at @s run function {NS}:story/ob/band",
        f"execute store result score #ob.px {OBJ} as {P()} run data get entity @s Pos[0] 4",
        f"execute store result score #ob.pz {OBJ} as {P()} run data get entity @s Pos[2] 4",
        f"scoreboard players operation #ob.dx {OBJ} = #ob.px {OBJ}", f"scoreboard players operation #ob.dx {OBJ} -= #ob.px0 {OBJ}",
        f"scoreboard players operation #ob.dz {OBJ} = #ob.pz {OBJ}", f"scoreboard players operation #ob.dz {OBJ} -= #ob.pz0 {OBJ}",
        sset("#ob.mv", 0),
        f"execute unless score #ob.dx {OBJ} matches -3..3 run {sset('#ob.mv', 1)}",
        f"execute unless score #ob.dz {OBJ} matches -3..3 run {sset('#ob.mv', 1)}",
        f"execute if score #ob.mv {OBJ} matches 1 run {sset('#ob.sn', 0)}",
        f"execute if score #ob.mv {OBJ} matches 1 run scoreboard players operation #ob.px0 {OBJ} = #ob.px {OBJ}",
        f"execute if score #ob.mv {OBJ} matches 1 run scoreboard players operation #ob.pz0 {OBJ} = #ob.pz {OBJ}",
        f"execute if score #ob.mv {OBJ} matches 0 run {sadd('#ob.sn', 5)}"])

    # ---- the sample (every 5 ticks while an objective is on)
    out.function("story/ob/progress", [f"scoreboard players operation #ob.bb {OBJ} = #ob.b {OBJ}", sset("#ob.np", 0), sset("#stk", 0)])
    out.function("story/ob/gate", [
        sset("#ob.vis", 0),
        f"execute if score #ob.sn {OBJ} >= #ob.stillt {OBJ} run {sset('#ob.vis', 1)}",
        f"execute if score #ob.b {OBJ} matches 6..30 run {sset('#ob.vis', 1)}",          # band 6 = beyond 8 blocks
        f"execute if score #ob.mv {OBJ} matches 1 run {sset('#stk', 0)}"])
    out.function("story/ob/sample", [
        fn("story/ob/measure"),
        sset("#ob.pr", 0),
        f"execute if score #ob.b {OBJ} < #ob.bb {OBJ} run {sset('#ob.pr', 1)}",
        f"execute if score #ob.pr {OBJ} matches 1 run function {NS}:story/ob/progress",
        f"execute if score #ob.pr {OBJ} matches 0 run {sadd('#ob.np', 5)}",
        f"execute if score #ob.gate {OBJ} matches 1 run function {NS}:story/ob/gate",
        sset("#ob.ok", 0),
        f"execute if score #ob.vis {OBJ} matches 1 if score #ob.t {OBJ} >= #ob.g {OBJ} run {sset('#ob.ok', 1)}",
        f"execute if score #ob.ok {OBJ} matches 1 if score #ob.shown {OBJ} matches 0 run function {NS}:story/ob/appear",
        f"execute if score #ob.ok {OBJ} matches 0 if score #ob.shown {OBJ} matches 1 run function {NS}:story/ob/hide",
        f"execute if score #ob.shown {OBJ} matches 1 run function {NS}:story/ob/update",
        f"execute if score #ob.shown {OBJ} matches 1 if score #ob.np {OBJ} >= #ob.rep {OBJ} run function {NS}:story/ob/reline"])
    chime = lambda vol: (f"execute unless score #hush {OBJ} matches 1 as {P()} at @s run playsound angel:sfx.speak_chime master {PA()} ~ ~ ~ {vol} 0.62 0.2")
    out.function("story/ob/chime", [chime(0.35)])
    out.function("story/ob/appear", [
        sset("#ob.shown", 1), sset("#ob.np", 0), sset("#ob.rn", 0), sset("#ob.bl", -1),
        f"execute if score #ob.wp {OBJ} matches 1 at {tgt} run function {NS}:story/ob/wp_spawn",
        f"execute if score #ob.snd {OBJ} matches 1 run function {NS}:story/ob/chime",
        f"execute if score #ob.nl {OBJ} matches 1 run function {NS}:story/ob/line"])
    out.function("story/ob/hide", ["kill @e[tag=angel.ob_wp]", "kill @e[tag=angel.ob_line]", sset("#ob.shown", 0), sset("#ob.line", -1)])
    out.function("story/ob/update", [
        f"execute if entity {tgt} run tp @e[tag=angel.ob_wp] {tgt}",
        f"execute unless score #ob.b {OBJ} = #ob.bl {OBJ} if entity @e[tag=angel.ob_label,limit=1] run function {NS}:story/ob/band_apply",
        f"execute at {tgt} run particle minecraft:end_rod ~ ~1.0 ~ 0.12 0.9 0.12 0.004 1 force"])
    out.function("story/ob/rechime", [chime(0.22)])
    out.function("story/ob/reline", [sset("#ob.np", 0), f"execute if score #ob.nl {OBJ} matches 1 run function {NS}:story/ob/rechime",
                                     f"execute if score #ob.nl {OBJ} matches 1 run function {NS}:story/ob/line"])

    # ---- the direction line
    out.function("story/ob/bearing", [
        sset("#ob.dir", -1),
        f"execute unless entity {tgt} run return 0",
        "kill @e[tag=angel.ob_tmp]",
        f'execute as {P()} at @s run summon minecraft:marker ~ ~ ~ {{Tags:["{TAG}","{A}","angel.ob_tmp"]}}',
        f"execute as @e[tag=angel.ob_tmp,limit=1] at @s facing entity {tgt} feet run rotate @s ~ ~",
        f"execute store result score #ob.ty {OBJ} run data get entity @e[tag=angel.ob_tmp,limit=1] Rotation[0] 10",
        f"execute as {P()} store result score #ob.py {OBJ} run data get entity @s Rotation[0] 10",
        f"scoreboard players operation #ob.ty {OBJ} -= #ob.py {OBJ}",
        f"scoreboard players operation #ob.ty {OBJ} %= #c3600 {OBJ}",
        f"execute if score #ob.ty {OBJ} matches 1801.. run scoreboard players remove #ob.ty {OBJ} 3600",
        "kill @e[tag=angel.ob_tmp]",
        f"execute if score #ob.ty {OBJ} matches -300..300 run {sset('#ob.dir', 0)}",
        f"execute if score #ob.ty {OBJ} matches 301..1350 run {sset('#ob.dir', 1)}",
        f"execute if score #ob.ty {OBJ} matches -1350..-301 run {sset('#ob.dir', 2)}",
        f"execute if score #ob.ty {OBJ} matches 1351.. run {sset('#ob.dir', 3)}",
        f"execute if score #ob.ty {OBJ} matches ..-1351 run {sset('#ob.dir', 3)}"])
    place = [fn("story/ob/bearing"), sset("#ob.low", 0)]
    spots = []
    for f in facs:
        spots.append(f"execute if score #ob.gf {OBJ} matches {f} as {P()} at @s anchored eyes positioned ^ ^{num(-LINE_DROP * f)} ^{num(LINE_DIST * f)}")
    for f in facs:
        place.append(f"{spots[facs.index(f)]} if entity @e[tag=angel.char,distance=..{num(1.5 * f)}] run {sset('#ob.low', 1)}")
    place.append("kill @e[tag=angel.ob_line]")
    for f in facs:
        place.append(f"execute if score #ob.low {OBJ} matches 0 {spots[facs.index(f)][len('execute '):]} run function {NS}:story/ob/ld/root")
        place.append(f"execute if score #ob.low {OBJ} matches 1 if score #ob.gf {OBJ} matches {f} as {P()} at @s anchored eyes positioned "
                     f"^ ^{num(-1.0 * f)} ^{num(1.8 * f)} run function {NS}:story/ob/ld/root")
    place += [f"scoreboard players operation #ob.line {OBJ} = #ob.secs {OBJ}",
              f"execute unless score #ctl {OBJ} matches 1 run function {NS}:story/ob/bd/root",
              sadd("#ob.rn")]
    out.function("story/ob/line", place)
    out.function("story/ob/line_off", ["kill @e[tag=angel.ob_line]", sset("#ob.line", -1)])
    # the generic line of a watched step that has no objective of its own (the 60 s safety net): kills the old one, speaks the objective's sentence
    for k, o in enumerate(objs):
        if o.generic:
            out.function(f"story/ob/line_generic_{k}", [sset("#ob.k", k), sset("#ob.dir", -1), sset("#ob.gf", 1), sset("#ob.rn", 1), sset("#ob.secs", T(10)),
                                                        fn("story/ob/line")])

    # ---- the tick
    out.function("story/ob/tick", [
        f"execute if score #ob.line {OBJ} matches 1.. run {ssub('#ob.line')}",
        f"execute if score #ob.line {OBJ} matches 0 run function {NS}:story/ob/line_off",
        f"execute unless score #ob.on {OBJ} matches 1 run return 0",
        f"execute if score #ob.hast {OBJ} matches 1 unless entity {tgt} run function {NS}:story/ob/td/root",
        f"execute if score #ob.fl {OBJ} matches 1 run function {NS}:story/ob/fd/root",
        sadd("#ob.t"),
        f"scoreboard players operation #ob.m {OBJ} = #ob.t {OBJ}",
        f"scoreboard players operation #ob.m {OBJ} %= #c5 {OBJ}",
        f"execute if score #ob.m {OBJ} matches 0 run function {NS}:story/ob/sample"])
    # ---- controls and the safety net's settings
    out.function("story/controls_both", [sset("#ctl", 0), f'tellraw @a {{"text":"[angel] instructions name both VR and keyboard controls","color":"gray"}}'])
    out.function("story/controls_vr", [sset("#ctl", 1), f'tellraw @a {{"text":"[angel] instructions name VR controls only","color":"gray"}}'])
    out.function("story/controls_flat", [sset("#ctl", 2), f'tellraw @a {{"text":"[angel] instructions name keyboard and mouse only","color":"gray"}}'])
    out.function("story/stuck", [f"$scoreboard players set #stk_hint {OBJ} $(hint_s)", f"scoreboard players operation #stk_hint {OBJ} *= #c20 {OBJ}",
                                 f"$scoreboard players set #stk_skip {OBJ} $(skip_s)", f"scoreboard players operation #stk_skip {OBJ} *= #c20 {OBJ}"])
    out.function("story/stuck_off", [sset("#stk_skip", 99999999), sset("#stk_hint", 99999999)])


def _band_label_lines(NB):
    out = []
    for b in range(NB):
        sc_ = band_scale(b)
        sel = f"matches {b}" if b < NB - 1 else f"matches {b}.."
        out.append(f"execute if score #ob.b {OBJ} {sel} run data merge entity @e[tag=angel.ob_label,limit=1] {{start_interpolation:0,interpolation_duration:5,"
                   f"{_tf(0, 1.0 + 0.3 * sc_, 0, sc_, sc_, sc_)}}}")
    return out


def _line_function(o):
    """The summons of the direction line for objective o (run at the spot, as the player): one per (first showing / repeat) x (controls) x (arrow)."""
    f = o.giant
    sc_ = LINE_SCALE * f
    dirs = (-1, 0, 1, 2, 3) if o.bearing else (-1,)
    texts = {c: o.texts(c) for c in (0, 1, 2)}
    uniform = len(set(texts.values())) == 1

    def summon(sentence, how, d):
        parts = []
        if d in ARROW:
            parts.append({"text": ARROW[d], "color": GOLD})
        parts.append({"text": sentence, "color": PALE})
        if how:
            parts.append({"text": "\n" + how, "color": GREY})
        return (f'summon minecraft:text_display ~ ~ ~ {{Tags:["{TAG}","{OBTAG}","angel.ob_line"],billboard:"center",background:{BG},'
                f'brightness:{{sky:15,block:15}},line_width:{LINE_WIDTH},shadow:1b,see_through:0b,view_range:1.0f,teleport_duration:0,'
                f'text:{_comp(parts)},{_tf(0, 0, 0, sc_, sc_, sc_)}}}')

    variants = []                                                   # (guards, sentence, controls line)
    for c in ((0,) if uniform else (0, 1, 2)):
        sentence, how = texts[c]
        cg = [] if uniform else [f"score #ctl {OBJ} matches {c}"]
        if how is None:
            variants.append((cg, sentence, None))
        elif o.first_how:
            variants.append((cg, sentence, how))
        else:
            variants.append((cg + [f"score #ob.rn {OBJ} matches 0"], sentence, None))
            variants.append((cg + [f"score #ob.rn {OBJ} matches 1.."], sentence, how))
    lines = []
    for guards, sentence, how in variants:
        for d in dirs:
            g = list(guards) + ([f"score #ob.dir {OBJ} matches {d}"] if len(dirs) > 1 else [])
            pre = "execute " + " ".join("if " + x for x in g) + " run " if g else ""
            lines.append(pre + summon(sentence, how, d))
    return lines


# --------------------------------------------------------------------------------------------------- the opening tutorial
def tutorial_objectives():
    look = Objective("Look around", line=("Look around you  -  turn your head (mouse: move the mouse)", "Look around you  -  turn your head, or push the right thumbstick",
                                          "Look around you  -  move the mouse"), grace=0.6, waypoint=False, bearing=False, sound=False, secs=FOREVER, repeat=3600)
    move = Objective("Move", line=("Move: left thumbstick (keyboard: W A S D)", "Move: left thumbstick", "Move: W A S D"), grace=0.4, waypoint=False,
                     bearing=False, sound=False, secs=FOREVER, repeat=3600)
    speak = Objective("Speak", line='When you see "Your turn", just speak aloud', grace=0.4, waypoint=False, bearing=False, sound=False, secs=FOREVER, repeat=3600)
    light = Objective("Like this", at=Ahead(7.0, 2.5, -1.6), line="A light like this marks where to go", grace=0.4, waypoint=True, bearing=True, sound=True,
                      secs=FOREVER, repeat=3600)
    return look, move, speak, light


def tutorial_short(s, pl):
    """The video pacing's tutorial: TWO lines, under 12 s in all, and each is over the moment he does the thing:
    1. "Look around, and walk: left thumbstick (keyboard W A S D)": done when he has moved 2.5 blocks (or after 5 s);
    2. 'When you see "Your turn", just speak aloud', with a sample waypoint beside him ("a light like this marks where to go"): done when he has walked
       another few blocks (or after 4 s)."""
    from engine import C, Cond
    move = Objective("Move", line=("Look around, and walk: left thumbstick (keyboard: W A S D)", "Look around, and walk: left thumbstick",
                                   "Look around (mouse), and walk: W A S D"),
                     grace=0.3, waypoint=False, bearing=False, sound=False, secs=FOREVER, repeat=3600)
    speak = Objective("Like this", at=Ahead(7.0, 2.5, -1.6),
                      line='When you see "Your turn", just speak aloud  -  a light like this marks where to go',
                      grace=0.3, waypoint=True, bearing=True, sound=True, secs=FOREVER, repeat=3600)
    far = lambda r: Cond([f"as @e[tag=angel.tut_mark,limit=1] at @s unless entity {pl.replace('limit=1', f'limit=1,distance=..{r}')}"], 3.0, f"he has moved {r} blocks")
    s.branch(C.score("#tut.off", "1"), "tutorial_done")
    s.do(f'execute as {pl} at @s run summon minecraft:marker ~ ~ ~ {{Tags:["{TAG}","angel.tut_mark"]}}', note="tutorial: mark where he stands")
    s.until(far(2.5), timeout=5.0, objective=move, no_skip=True, est=2.5, note="TUTORIAL 1/2 'Look around, and walk' (over at 2.5 blocks, or after 5 s)")
    s.until(far(7.0), timeout=4.0, objective=speak, no_skip=True, est=3.5,
            note="TUTORIAL 2/2 'When you see Your turn, just speak aloud' + a sample light (over at 7 blocks, or after 4 s)")
    s.do("kill @e[tag=angel.tut_mark]", note="tutorial over")
    s.label("tutorial_done")


def tutorial(s):
    """The 20-second opening tutorial (scene 1, just after he wakes: the A.D. 2015 card stays the film's first image and the tutorial happens in the world
    he will walk in).  One line at a time, in the speak prompt's look, each leaving as he does the thing, or after 8 s: look around (60 degrees of yaw),
    move (3 blocks), 'Your turn' means speak (a 5 s hold), a sample waypoint beside him (a 6 s hold).  Skipped when #tut.off is 1
    (`function angel:story/start_no_tutorial`)."""
    from engine import C, Cond
    import pace
    pl = P()
    if pace.PACE.tutorial == "short":
        return tutorial_short(s, pl)
    look, move, speak, light = tutorial_objectives()
    y_get = lambda n: f"execute as {pl} store result score #tut.{n} {OBJ} run data get entity @s Rotation[0] 10"
    s.branch(C.score("#tut.off", "1"), "tutorial_done")
    s.do(y_get("y0"), sset("#tut.m", 0), note="tutorial: remember where he looks")
    s.until(Cond([f"if score #tut.m {OBJ} matches 1"], 4.0, "he has turned his head 60 degrees"), timeout=8.0, objective=look,
            tick=[y_get("y1"), f"scoreboard players operation #tut.d {OBJ} = #tut.y1 {OBJ}", f"scoreboard players operation #tut.d {OBJ} -= #tut.y0 {OBJ}",
                  f"scoreboard players operation #tut.d {OBJ} %= #c3600 {OBJ}", f"execute if score #tut.d {OBJ} matches 1801.. run scoreboard players remove #tut.d {OBJ} 3600",
                  f"execute unless score #tut.d {OBJ} matches -599..599 run {sset('#tut.m', 1)}"],
            note="TUTORIAL 1/4 'Look around' (done at 60 degrees of yaw, or after 8 s)")
    s.do(f'execute as {pl} at @s run summon minecraft:marker ~ ~ ~ {{Tags:["{TAG}","angel.tut_mark"]}}', note="tutorial: mark where he stands")
    s.until(Cond([f"as @e[tag=angel.tut_mark,limit=1] at @s unless entity {pl.replace('limit=1', 'limit=1,distance=..3')}"], 5.0, "he has moved 3 blocks"), timeout=8.0,
            objective=move, no_skip=True, note="TUTORIAL 2/4 'Move: left thumbstick (keyboard: W A S D)' (done at 3 blocks, or after 8 s)")
    s.until(C.never(), timeout=5.0, objective=speak, note="TUTORIAL 3/4 'When you see Your turn, just speak aloud' (5 s)")
    s.until(C.never(), timeout=6.0, objective=light, note="TUTORIAL 4/4 'A light like this marks where to go' (a sample waypoint beside him, 6 s)")
    s.do("kill @e[tag=angel.tut_mark]", note="tutorial over")
    s.label("tutorial_done")
