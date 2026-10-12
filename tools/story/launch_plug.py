"""The inside of the entry plug as a cockpit capsule (scene 6).

What the first real playthrough showed in the middle of the view for 25 s of the fluid (s6_07 .. s6_18) was the BACK OF THE SEAT: the plug set has a
seat back of three grey concrete blocks at z 13 (y 11..13) with a single black block above it as a headrest (y 14), a metre and a half behind the
seat entity.  The boy had been put in the seat without being turned (nothing in the story turns his head but a teleport through black), so he
sat looking at it through the dark glass: a grey slab and a black rectangle with nothing else in the picture.

Now the move into the plug turns him to the front (yaw 180, through the black), and the capsule is a real interior, built of display entities
inside the plug box: an octagonal liner of dark panels with ring seams, a forward wall with a screen and rows of indicator lights, consoles on
the lower corners with lights, two hand grips, an overhead lamp strip, the rear hatch, and a status strip (a text display, tag `angel.lstat`)
that the scene rewrites as the BASE lines are said.  The liner is dim (display brightness 4: visible, never lit up), the indicator lights are
full bright and come on row by row; the real capsule lamps are put out while he is sealed in (`story/launch/plug_dim`, and back with
`story/launch/plug_lit`, which `story/launch/restore` also calls) and two dim light blocks stand in the air, so that the real seat and grips
that are inside the liner are as dim as the liner.

Everything carries angel.story, angel.launch (the restore kills it) and a tag of its own: angel.lliner (the panels), angel.lli_a .. d (the light
rows), angel.lstat (status texts, forward strip or cockpit HUD).
"""
import json

from core import OBJ, TAG, fnum, num, qaxis, sset
from models import Part, summon_part

# the open space inside the capsule (world coordinates): launch_geo.PLUG_BOX
CX, CY, CZ = 3030.5, 12.5, 10.5
HX, HY, HZ = 1.5, 2.5, 4.5
CHAMFER = 0.9
BRIGHT_WALL = (4, 4)
BRIGHT_RIB = (3, 3)
STATUS_AT = (0.0, 1.55, -2.6)           # relative to the box centre: just over the line of sight, 3.6 m ahead of the seat
STATUS_SCALE = 2.1

# the real capsule lamps (local coordinates of the set at x 3000): they go out while he is sealed in
LAMPS = [(30, 15, 7), (30, 15, 10), (30, 15, 13), (27, 12, 10), (33, 12, 10), (30, 12, 5)]
DIM_LIGHTS = [(30, 14, 9, 6), (30, 13, 12, 6)]            # local x, y, z, level: hidden light blocks in the air of the capsule
PLUG_PROBE = (3030, 12, 11)
FLAG = "#l.plug"


def _tags(*t):
    return ["angel.launch", *t]


def _part(tags, block, lo, hi, bright, rot=(0.0, 0.0, 0.0, 1.0), pivot=(0.0, 0.0, 0.0), view=3.0):
    p = Part("x", block, lo, hi, rot=rot, pivot=pivot, bright=bright)
    return summon_part(p, _tags(*tags), tp_duration=0, view_range=view, bright=bright, pos=f"{num(CX)} {num(CY)} {num(CZ)}")


def _box(tags, block, x, y, z, bright):
    return _part(tags, block, (x[0], y[0], z[0]), (x[1], y[1], z[1]), bright)


def liner():
    """Summon commands for the whole interior: ([commands], [tags of the light rows in the order they come on])."""
    out = []
    T = 0.04
    c = CHAMFER
    fl = HX - c                      # half width of the flat floor / ceiling (0.6)
    wl = HY - c                      # half height of the flat side walls (1.6)
    z0, z1 = -HZ, HZ
    L = ["angel.lliner"]
    # ---- the eight faces (floor, ceiling, two walls, four diagonals), base panels in dark gunmetal
    base = "polished_blackstone"
    out.append(_box(L, base, (-fl, fl), (-HY, -HY + T), (z0, z1), BRIGHT_WALL))
    out.append(_box(L, base, (-fl, fl), (HY - T, HY), (z0, z1), BRIGHT_WALL))
    out.append(_box(L, base, (-HX, -HX + T), (-wl, wl), (z0, z1), BRIGHT_WALL))
    out.append(_box(L, base, (HX - T, HX), (-wl, wl), (z0, z1), BRIGHT_WALL))
    diag = []                         # (centre x, centre y, angle about z)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mx, my = sx * (fl + c / 2.0), sy * (HY - c / 2.0)
            ang = 45.0 if sx * sy < 0 else -45.0
            diag.append((mx, my, ang))
    ln = c * 2 ** 0.5
    for (mx, my, ang) in diag:
        q = qaxis("z", ang)
        out.append(_part(L, base, (mx - ln / 2, my - T / 2, z0), (mx + ln / 2, my + T / 2, z1), BRIGHT_WALL, rot=q, pivot=(mx, my, 0.0)))
    # ---- seams: rings round the tube every 1.5 blocks and a long seam down the middle of each face, black, a hair proud
    SEAM = "black_concrete"
    inset = 0.045
    for zc in (-3.3, -1.8, -0.3, 1.2, 2.7):
        zz = (zc - 0.06, zc + 0.06)
        out.append(_box(L, SEAM, (-fl, fl), (-HY + T, -HY + T + 0.03), zz, BRIGHT_RIB))
        out.append(_box(L, SEAM, (-fl, fl), (HY - T - 0.03, HY - T), zz, BRIGHT_RIB))
        out.append(_box(L, SEAM, (-HX + T, -HX + T + 0.03), (-wl, wl), zz, BRIGHT_RIB))
        out.append(_box(L, SEAM, (HX - T - 0.03, HX - T), (-wl, wl), zz, BRIGHT_RIB))
        for (mx, my, ang) in diag:
            # shifted a little toward the middle of the tube along the panel's normal (a 45 degree panel: (-sx, -sy) / sqrt 2)
            ox_, oy_ = (-1.0 if mx > 0 else 1.0) * inset * 0.7071, (-1.0 if my > 0 else 1.0) * inset * 0.7071
            q = qaxis("z", ang)
            out.append(_part(L, SEAM, (mx + ox_ - ln / 2, my + oy_ - 0.03, zz[0]), (mx + ox_ + ln / 2, my + oy_ + 0.03, zz[1]), BRIGHT_RIB,
                             rot=q, pivot=(mx + ox_, my + oy_, 0.0)))
    # long seams (down the middle of the walls and the floor and ceiling) and a lighter panel inset on each wall
    out.append(_box(L, SEAM, (-0.02, 0.02), (-HY + T, -HY + T + 0.02), (z0, z1), BRIGHT_RIB))
    out.append(_box(L, SEAM, (-0.02, 0.02), (HY - T - 0.02, HY - T), (z0, z1), BRIGHT_RIB))
    for sx in (-1, 1):
        a, b = (sx * (HX - T - 0.02), sx * (HX - T))
        out.append(_box(L, SEAM, (min(a, b), max(a, b)), (-0.02, 0.02), (z0, z1), BRIGHT_RIB))
        # lighter panel inset between the rings, at the height of the hands
        for (za, zb) in ((-3.1, -1.9), (-1.6, -0.4), (-0.1, 1.1), (1.4, 2.6)):
            a, b = (sx * (HX - T - 0.012), sx * (HX - T))
            out.append(_box(L, "gray_concrete", (min(a, b), max(a, b)), (-0.9, 0.9), (za, zb), BRIGHT_WALL))
    # ---- the forward end: the cap, a screen in a frame, the status strip is a text display
    out.append(_box(L, base, (-HX, HX), (-HY, HY), (z0, z0 + T), BRIGHT_WALL))
    out.append(_box(L, "black_concrete", (-1.15, 1.15), (0.30, 1.70), (z0 + T, z0 + T + 0.05), BRIGHT_RIB))
    out.append(_box(["angel.lliner", "angel.lli_a"], "light_blue_stained_glass", (-1.02, 1.02), (0.44, 1.56), (z0 + T + 0.05, z0 + T + 0.07), (5, 5)))
    for xs in (-0.5, 0.0, 0.5):                                # a few lines on the screen: bright dashes
        out.append(_box(["angel.lliner", "angel.lli_a"], "cyan_concrete", (xs - 0.18, xs + 0.18), (0.95, 1.0), (z0 + T + 0.07, z0 + T + 0.09), (13, 13)))
    out.append(_box(["angel.lliner", "angel.lli_a"], "lime_concrete", (-0.9, -0.3), (0.62, 0.66), (z0 + T + 0.07, z0 + T + 0.09), (13, 13)))
    cols = ["lime_concrete", "orange_concrete", "cyan_concrete", "red_concrete", "lime_concrete", "orange_concrete", "cyan_concrete", "lime_concrete"]
    for i, blk in enumerate(cols):                              # the row of indicators under the screen
        x = -0.98 + i * 0.28
        out.append(_box(["angel.lliner", "angel.lli_a"], blk, (x - 0.07, x + 0.07), (0.10, 0.24), (z0 + T + 0.05, z0 + T + 0.12), (15, 15)))
    for j in range(6):                                          # columns of lights down both sides of the cap
        y = -1.15 + j * 0.42
        for sx, blk in ((-1, "orange_concrete" if j % 2 else "lime_concrete"), (1, "cyan_concrete" if j % 2 else "orange_concrete")):
            x = sx * 1.28
            out.append(_box(["angel.lliner", "angel.lli_b"], blk, (x - 0.07, x + 0.07), (y - 0.07, y + 0.07), (z0 + T, z0 + T + 0.08), (15, 15)))
    # ---- the consoles: rows of lights on the lower diagonals, the length of the seat
    for sx in (-1, 1):
        mx, my = sx * (fl + c / 2.0), -(HY - c / 2.0)
        for k, zc in enumerate((-3.4, -2.6, -1.8, -1.0, -0.2, 0.6, 1.4, 2.2)):
            blk = ("lime_concrete", "orange_concrete", "cyan_concrete", "red_concrete")[(k + (0 if sx > 0 else 2)) % 4]
            # on the panel's inner face: toward the middle of the tube along the normal (the lower panels face up and inward)
            px, py = mx - sx * 0.07 * 0.7071 * 1.4, my + 0.07 * 0.7071 * 1.4
            out.append(_part(["angel.lliner", "angel.lli_c"], blk, (px - 0.07, py - 0.07, zc - 0.07), (px + 0.07, py + 0.07, zc + 0.07), (15, 15),
                             rot=qaxis("z", 45.0), pivot=(px, py, zc)))
    # ---- the overhead lamp strips, amber and dim, and the rear hatch
    for sx in (-1, 1):
        out.append(_box(["angel.lliner", "angel.lli_d"], "orange_concrete", (sx * 0.35 - 0.05, sx * 0.35 + 0.05), (HY - T - 0.06, HY - T), (-3.6, 3.6), (8, 8)))
    out.append(_box(L, base, (-HX, HX), (-HY, HY), (z1 - T, z1), BRIGHT_WALL))
    for (xa, xb, ya, yb) in ((-1.0, 1.0, 1.55, 1.7), (-1.0, 1.0, -0.4, -0.25), (-1.0, -0.85, -0.4, 1.7), (0.85, 1.0, -0.4, 1.7)):      # the hatch's rim
        out.append(_box(L, "iron_block", (xa, xb), (ya, yb), (z1 - T - 0.06, z1 - T), (6, 6)))
    out.append(_box(L, "iron_block", (-0.25, 0.25), (0.55, 0.7), (z1 - T - 0.12, z1 - T), (6, 6)))
    out.append(_box(L, "iron_block", (-0.06, 0.06), (-0.1, 1.45), (z1 - T - 0.12, z1 - T), (6, 6)))
    # ---- the hand grips: a bar on each side at the height of the hands, held out from the wall on two posts
    for sx in (-1, 1):
        bx = (min(sx * 0.88, sx * 1.0), max(sx * 0.88, sx * 1.0))
        out.append(_box(L, "light_gray_concrete", bx, (-0.1, 0.02), (0.0, 0.9), (6, 6)))
        for zz in (0.0, 0.8):
            px = (min(sx * 0.88, sx * (HX - T)), max(sx * 0.88, sx * (HX - T)))
            out.append(_box(L, "light_gray_concrete", px, (-0.1, 0.02), (zz, zz + 0.1), (6, 6)))
    return out, ["angel.lli_a", "angel.lli_b", "angel.lli_c", "angel.lli_d"]


def light_rows_off():
    """The light rows as they are spawned (dark): their brightness is 0 until switched."""
    return [f"execute as @e[tag={t}] run data merge entity @s {{brightness:{{sky:0,block:0}}}}" for t in ("angel.lli_a", "angel.lli_b", "angel.lli_c", "angel.lli_d")]


def light_row_on(tag, level=15):
    return f"execute as @e[tag={tag}] run data merge entity @s {{brightness:{{sky:{level},block:{level}}}}}"


# ---------------------------------------------------------------------------------------------------- the status text
def _text_comp(line1, line2, color):
    comp = [{"text": line1, "color": color, "bold": True}]
    if line2:
        comp += [{"text": "\n"}, {"text": line2, "color": "gray"}]
    return comp


def status_spawn(line1, line2="", color="green", scale=STATUS_SCALE, rel=STATUS_AT, abs_pos=None, tag="angel.lstat", billboard="center", bg=1073741824):
    """A text display (the status strip).  rel: relative to the box centre; abs_pos: absolute world coordinates instead."""
    x, y, z = abs_pos if abs_pos else (CX + rel[0], CY + rel[1], CZ + rel[2])
    return (f'summon minecraft:text_display {num(x)} {num(y)} {num(z)} {{Tags:["{TAG}","angel.launch","{tag}","angel.lstat"],billboard:"{billboard}",'
            f'background:{bg},brightness:{{sky:15,block:15}},line_width:600,shadow:0b,see_through:0b,alignment:"center",view_range:2.0f,'
            f'text:{json.dumps(_text_comp(line1, line2, color), ensure_ascii=True)},'
            f'transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[{fnum(scale)},{fnum(scale)},{fnum(scale)}],right_rotation:[0f,0f,0f,1f]}}}}')


def status_set(line1, line2="", color="green"):
    """Rewrite every status text (the strip in the capsule, the HUD in the cockpit)."""
    return (f"execute as @e[tag=angel.lstat] run data merge entity @s {{text:{json.dumps(_text_comp(line1, line2, color), ensure_ascii=True)}}}")


def hud_spawn(eye, line1="POWER", line2="CONNECTED", color="green", scale=0.5):
    """The cockpit's status HUD: a small panel of text hanging 1.15 ahead of the eyes (south: down the bridge) and 0.62 below them, in the amber."""
    return status_spawn(line1, line2, color, scale=scale, abs_pos=(eye[0], eye[1] - 0.62, eye[2] + 1.15), tag="angel.lhud")


# ---------------------------------------------------------------------------------------------------- the real capsule's lights
def register(ctx):
    """Write story/launch/plug_dim and plug_lit; plug_lit is also part of story/launch/restore (the story stopping with him sealed in)."""
    if "story/launch/plug_dim" in ctx.extra_functions:
        return
    probe = ctx.probe("hq")
    o = probe.o
    cells = []
    for (x, y, z) in LAMPS:
        nm = (probe.name(o[0] + x, y, z) or "minecraft:air").replace("minecraft:", "")
        if nm == "sea_lantern":
            cells.append((x, y, z))
        else:
            ctx.warn(f"launch_plug: capsule lamp cell {(x, y, z)} is {nm}, not a sea_lantern: left alone")
    air = []
    for (x, y, z, lv) in DIM_LIGHTS:
        nm = probe.name(o[0] + x, y, z)
        if nm is not None and nm.replace("minecraft:", "") != "air":
            ctx.warn(f"launch_plug: dim light cell {(x, y, z)} is {nm}, not air: skipped")
        else:
            air.append((x, y, z, lv))
    ctx.extra_functions["story/launch/plug_dim"] = (
        [sset(FLAG, 1)] + [f"setblock {o[0] + x} {y} {z} minecraft:black_concrete" for (x, y, z) in cells]
        + [f"setblock {o[0] + x} {y} {z} minecraft:light[level={lv}]" for (x, y, z, lv) in air])
    ctx.extra_functions["story/launch/plug_lit"] = (
        [sset(FLAG, 0)] + [f"setblock {o[0] + x} {y} {z} minecraft:sea_lantern" for (x, y, z) in cells]
        + [f"setblock {o[0] + x} {y} {z} minecraft:air" for (x, y, z, lv) in air])
    restore = ctx.extra_functions.get("story/launch/restore")
    line = f"execute if score {FLAG} {OBJ} matches 1 if loaded {PLUG_PROBE[0]} {PLUG_PROBE[1]} {PLUG_PROBE[2]} run function angel:story/launch/plug_lit"
    if restore is not None and line not in restore:
        restore.append(line)
    ctx.load_extra.append(f"execute unless score #running {OBJ} matches 1 if score {FLAG} {OBJ} matches 1 if loaded {PLUG_PROBE[0]} {PLUG_PROBE[1]} "
                          f"{PLUG_PROBE[2]} run function angel:story/launch/plug_lit")
