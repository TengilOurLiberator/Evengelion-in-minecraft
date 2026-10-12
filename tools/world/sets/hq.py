"""HQ - the underground headquarters: corridors, the flooded approach, THE CAGE with the giant's head, the entry plug
and the launch shaft.  192 x 160 x 192 (x east, y up, z south); every coordinate below is local to the set.

PLAN (top view, x ->, z v; bottom-left of the box is the north-west corner)

    z   0.. 17   x  0..17   LAUNCH SHAFT  14 x 14, floor (pad) y 3, open to the roof y 156, roof sealed 157..159
    z   4.. 16   x 25..35   ENTRY PLUG    a white tube, floor y 9, 3 wide at the floor, 5 at its belly, 9 long
    z  22..141   x 56..132  THE CAGE      interior x 64..128, z 24..137, y 6..111 (floor 5, roof 112); centre line x = 96
                            red-orange coolant (tinted glass over magma) y 7..36; the giant's head 15 wide, 27 tall (chin y 46,
                            crown y 72, horn tip y 75), z 40..62, its face plane z 59, eyes y 61..64;
                            the umbilical bridge deck y 53, x 94..98 (rails on 93 and 99), z 71..137, ending in a hazard lip (no end
                            rail, no grating; invisible barriers at z 70); the player stops at z 72.5, 13.5 from the face plane;
                            the commander's booth is an open balcony beside the head's right cheek, level with the east catwalk: x 105..114,
                            z 49..54, y 62..71 (no glass; a one-block parapet on the south side), he stands at (107.0, 63, 53.75): 23 blocks from
                            the stop, 23 degrees up, 29 degrees to the right
    z 142..188   x  9..150  B: THE FLOODED CHAMBER  y 33..79, lake surface y 50, catwalk deck y 53, dock west, cage door north
    z 142..188   x  0..189  A: THE CORRIDORS  two levels: U (floor y 130) and L (floor y 106), tall escalator void between

Walking order: start (lobby, east, x 176) -> west along the corridor -> moving-walkway hall -> loop ring (passes the same
orange door twice) -> escalator hall (down) -> lower corridor -> elevator lobby (x 11) -> car (x 5) ~~ lowered ~~ dock
(x 14, y 53) -> catwalk east -> cage door (96, 143) -> bridge north -> face (96.5, 72.5).

LIGHT (all of it is deliberate; the set is capped so that no skylight can reach any interior cell - see skylight_check):
    corridors   hidden level-15 light blocks on the floor cells and along the walls: 12..15 everywhere, near neutral white
    flood/cage  always-on amber run-lights (RUN_LIGHTS) along every walkway edge, a glow under the coolant, red emergency lamps
                (EMERGENCY, level 10) on walls and pylons and a rim of hidden light round the giant's head
    cage lamps  CAGE_LIGHTS / BOOTH_LIGHTS stay off until the story switches them on; EYE_GLOW is the optional glow with the eyes.
                The floodlight (see FLOODLIGHT below): hidden level-15 blocks in front of the giant (the last bank: the face), lamp masts and a
                gantry as visible sources, a diamond lattice of lights on the side and north walls, the deck; measured by verify_light().

Run this file to build and write checks + previews:  python hq.py [--quick]; to re-bake the floodlight after a change of the giant:  python hq.py --design
"""
import json
import math
import os
import random
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
from voxel import World  # noqa: E402

SIZE = (192, 160, 192)
YAW = {"south": 0.0, "west": 90.0, "north": 180.0, "east": -90.0}
RNG_SEED = 20151

# ------------------------------------------------------------------------------------------------ palette
AIR = "minecraft:air"
PURPLE = "purple_concrete"
PURPLE_LIT = "purple_wool"
PURPLE_HI = "amethyst_block"
PURPLE_DARK = "obsidian"
LIME = "lime_concrete"
LIME_DARK = "green_concrete"
ORANGE = "orange_concrete"
BLACK = "black_concrete"
GRAY = "gray_concrete"
LGRAY = "light_gray_concrete"
WHITE = "white_concrete"
YELLOW = "yellow_concrete"
IRON = "iron_block"
EYE_OFF = "minecraft:black_concrete"
EYE_ON = "minecraft:sea_lantern"               # cold white, emits 15, the brightest block there is (glowstone is mottled tan, ochre froglight a pale cream brick)
LAMP_OFF = "minecraft:gray_concrete"           # dead lamp panel
LAMP_ON = "minecraft:sea_lantern"
LIQUID = "orange_stained_glass"
LIQUID_BED = "magma_block"

# ------------------------------------------------------------------------------------------------ global geometry
CX = 96                       # centre column of the cage / head / bridge (cell index)
SURF = 36                     # top block of the coolant in the cage
FLOOR_C = 6                   # magma bed of the cage
BRIDGE_Y = 53                 # bridge deck block row (feet at 54)
HEAD_X0 = CX - 10             # head cell ix 0 -> world x (the centre column ix 10 is x = CX)
HEAD_Y0 = 46                  # chin underside; the eye slits land at y 61..64, the player's eye is at 55.6
HEAD_ZF = 63                  # front-most head cell (iz 0) world z; iz increases to the north
FACE_PLANE_Z = HEAD_ZF - 4.0  # south surface of the face plate at eye level (s = 5): z 59.0
STOP_DIST = 13.5              # the "face" anchor stands this far from the face plane
ZS = 7                        # the stop and everything laid out from it moved this far south when the head grew
FACE_Z = FACE_PLANE_Z + STOP_DIST   # 72.5: where the player stops on the bridge
SHIELD_Z = 71 + ZS            # z of the column the hand covers (the "shield" anchor)
SHOULDER_Z = 54             # z of the giant's right shoulder joint (the hand's reach grows with the stop)
GURNEY_Z = 72 + ZS            # first of the three rows of the gurney spur (79..81)

EYES_LEFT = []                # filled by build(): (x, y, z) cells, viewer's left (west) eye
EYES_RIGHT = []               # viewer's right (east) eye
CAGE_LIGHTS = []              # (x, y, z, block_when_on); all are built OFF (LAMP_OFF) by default
BOOTH_LIGHTS = []             # the subset lighting the commander's booth
EMERGENCY = []                # (x, y, z) red lamps that are on from the start (hidden light block level EMERGENCY_LEVEL beside each)
EYE_GLOW = []                 # (x, y, z, block_when_on): hidden light blocks that put a glow on the brow and the bridge end; built as
                              # air - set them with the eyes (optional; the eye blocks themselves already emit 15)
DOORS = {}                    # name -> dict(box=(x1,y1,z1,x2,y2,z2), closed=block) doors the story opens
EMERGENCY_LEVEL = 10          # light level of an emergency lamp (it was 7: not enough to read anything by)
HAND = {}                     # filled by hand_boxes()


def _validate_enabled():
    return os.path.exists(BLOCKS_JSON)


BLOCKS_JSON = r"D:\genesis-vr\work\mcdata\out\reports\blocks.json"


def validate_palette(w):
    """Every block id + state used must exist in the 26.3 block report."""
    if not os.path.exists(BLOCKS_JSON):
        return ["blocks.json not found"]
    rep = json.load(open(BLOCKS_JSON))
    bad = []
    for b in w.palette[1:]:
        name, _, rest = b.partition("[")
        info = rep.get(name)
        if info is None:
            bad.append("unknown block " + b)
            continue
        if rest:
            props = info.get("properties", {})
            for kv in rest.rstrip("]").split(","):
                k, _, v = kv.partition("=")
                if k not in props or v not in props[k]:
                    bad.append("bad state %s on %s" % (kv, name))
    return bad


# ------------------------------------------------------------------------------------------------ small helpers
def bs(name, **kw):
    if not kw:
        return name
    return name + "[" + ",".join("%s=%s" % (k, str(v).lower() if isinstance(v, bool) else v) for k, v in kw.items()) + "]"


def box(w, x1, y1, z1, x2, y2, z2, b):
    w.fill(x1, y1, z1, x2, y2, z2, b)


def carve(w, x1, y1, z1, x2, y2, z2):
    w.fill(x1, y1, z1, x2, y2, z2, AIR)


def hollow(w, x1, y1, z1, x2, y2, z2, shell, thick=1):
    """A closed box room: solid shell `thick` thick around an air interior x1..x2 etc."""
    t = thick
    w.fill(x1 - t, y1 - t, z1 - t, x2 + t, y2 + t, z2 + t, shell)
    w.fill(x1, y1, z1, x2, y2, z2, AIR)


# ------------------------------------------------------------------------------------------------ colours for the previews
_RGB = {
    "white": (207, 213, 214), "orange": (224, 97, 0), "magenta": (169, 48, 159), "light_blue": (35, 137, 198),
    "yellow": (221, 160, 20), "lime": (94, 167, 24), "pink": (213, 101, 142), "gray": (50, 53, 58),
    "light_gray": (125, 125, 115), "cyan": (21, 119, 136), "purple": (100, 31, 156), "blue": (44, 46, 143),   # (gray, yellow, black: measured)
    "brown": (96, 60, 32), "green": (73, 91, 36), "red": (142, 33, 33), "black": (8, 10, 15),
}
_EXACT = {
    "amethyst_block": (134, 97, 191), "obsidian": (10, 7, 17), "magma_block": (140, 60, 20), "sea_lantern": (172, 200, 205),
    "ochre_froglight": (240, 220, 140), "glowstone": (255, 205, 100), "verdant_froglight": (200, 240, 170), "iron_block": (205, 205, 205),
    "polished_blackstone": (45, 43, 49), "blackstone": (42, 38, 44), "deepslate_tiles": (51, 52, 52), "polished_deepslate": (70, 70, 75),
    "chiseled_polished_blackstone": (50, 46, 54), "smooth_quartz": (235, 230, 222), "quartz_block": (235, 230, 222),
    "copper_grate": (180, 105, 75), "weathered_copper": (100, 150, 120), "cut_copper": (190, 110, 80),
    "iron_bars": (150, 150, 155), "iron_chain": (60, 62, 70), "glass_pane": (190, 225, 235), "glass": (190, 225, 235), "tinted_glass": (50, 40, 60),
    "redstone_torch": (230, 40, 20), "shroomlight": (240, 150, 70), "magma": (140, 60, 20), "purpur_block": (169, 125, 169), "lantern": (230, 170, 80),
    "smooth_stone": (160, 160, 160), "stone_bricks": (125, 125, 125), "polished_andesite": (140, 140, 140),
    "light": (255, 240, 200), "ladder": (130, 100, 60), "iron_door": (200, 200, 205), "iron_trapdoor": (190, 190, 195),
    "lightning_rod": (200, 120, 90), "end_rod": (240, 240, 240), "copper_bulb": (200, 120, 80), "crying_obsidian": (40, 12, 80),
    "coal_block": (20, 20, 20), "redstone_block": (170, 20, 10), "redstone_lamp": (140, 90, 50), "dark_prismarine": (50, 90, 80),
    "cyan_stained_glass": (60, 160, 180), "light_blue_stained_glass": (100, 160, 220), "orange_stained_glass": (230, 130, 40),
    "red_stained_glass": (200, 50, 40), "black_stained_glass": (30, 30, 40), "stone": (125, 125, 125), "gray_wool": (65, 68, 72),
}


def block_rgb(name):
    name = name.replace("minecraft:", "")
    if name in _EXACT:
        return _EXACT[name]
    for k in _EXACT:                                  # stairs and slabs of an exactly coloured block
        if name.startswith(k + "_stairs") or name.startswith(k + "_slab"):
            return _EXACT[k]
    for c, rgb in _RGB.items():
        if name.startswith(c + "_") or name == c:
            f = 1.0
            if "terracotta" in name:
                f = 0.7
            if "wool" in name:
                f = 1.12
            return tuple(min(255, int(v * f)) for v in rgb)
    if "stone" in name or "deepslate" in name:
        return (100, 100, 105)
    if "copper" in name:
        return (190, 110, 80)
    return (200, 80, 200)


_THIN = ("iron_bars", "glass_pane", "iron_chain", "ladder", "_fence", "torch", "lightning_rod", "end_rod", "chain", "lantern", "_wall", "stained_glass_pane", "button", "lever", "tripwire", "grate")
_GLASS = ("glass", "light")
_EMIT = {"sea_lantern": 15, "ochre_froglight": 15, "verdant_froglight": 15, "pearlescent_froglight": 15, "glowstone": 15,
         "magma_block": 3, "redstone_torch": 7, "redstone_wall_torch": 7, "lantern": 15, "end_rod": 14, "shroomlight": 15,
         "crying_obsidian": 10, "soul_lantern": 10, "copper_bulb": 0, "redstone_lamp": 0, "lava": 15, "jack_o_lantern": 15}


def tables(w):
    n = len(w.palette)
    rgb = np.zeros((n, 3), np.float32)
    kind = np.zeros(n, np.uint8)           # 0 empty, 1 opaque, 2 translucent (glass), 3 thin (see-through)
    alpha = np.zeros(n, np.float32)
    emit = np.zeros(n, np.int8)
    for i, b in enumerate(w.palette):
        if b is None:
            continue
        nm = b.split("[")[0].replace("minecraft:", "")
        if nm == "air":
            continue
        rgb[i] = block_rgb(nm)
        if nm == "barrier":                 # invisible, solid for walking, clear for light
            kind[i] = 0
            continue
        if nm == "light":
            kind[i] = 0
            if "level=" in b:
                emit[i] = int(b.split("level=")[1].split(",")[0].split("]")[0])
            continue
        if any(t in nm for t in _THIN) and "glass" not in nm.replace("glass_pane", "") and nm != "sea_lantern":
            # thin things: the real frames show bars and chains as a sparse mesh, so they only veil what is behind them a little
            kind[i], alpha[i] = 3, (0.30 if "grate" in nm else (0.28 if "bars" in nm else (0.2 if ("chain" in nm or "ladder" in nm) else 0.3)))
        elif "glass" in nm and "pane" not in nm:
            kind[i], alpha[i] = 2, (0.12 if nm == "glass" else (0.8 if nm == "tinted_glass" else 0.45))     # clear glass is nearly clear
        elif "pane" in nm:
            kind[i], alpha[i] = 3, (0.15 if nm == "glass_pane" else 0.45)
        else:
            kind[i] = 1
        emit[i] = _EMIT.get(nm, 0)
        if nm == "copper_bulb" and "lit=true" in b:
            emit[i] = 15
        if nm == "redstone_lamp" and "lit=true" in b:
            emit[i] = 15
    return rgb, kind, alpha, emit


def light_map(w, tab=None, region=None):
    """Minecraft-style block light (0..15) of the whole canvas; opaque blocks and untouched cells stop it."""
    rgb, kind, alpha, emit = tab or tables(w)
    a = w.a
    em = emit[a]
    L = np.where(em > 0, em, 0).astype(np.int8)
    part = partial_flags(w)[a]
    stops = np.array([bool(b) and b.split("[")[0].endswith("tinted_glass") for b in w.palette])      # tinted glass stops block light
    pass_ = (((kind[a] != 1) & ~stops[a]) | part) & (a != 0)       # light travels through air, glass, thin things, stairs and slabs
    for _ in range(15):
        m = L.copy()
        for ax in range(3):
            for sh in (1, -1):
                s = np.roll(L, sh, axis=ax)
                if sh == 1:
                    sl = [slice(None)] * 3
                    sl[ax] = slice(0, 1)
                    s[tuple(sl)] = 0
                else:
                    sl = [slice(None)] * 3
                    sl[ax] = slice(-1, None)
                    s[tuple(sl)] = 0
                m = np.maximum(m, (s - 1).clip(0))
        L = np.where(pass_, np.maximum(m, L), L).astype(np.int8)
    return L


# ------------------------------------------------------------------------------------------------ ray-cast renderer
# What the game's lightmap makes of block light level 0..15 (r, g, b multipliers on a block's colour, no skylight).  MEASURED from the
# real frame work/shots/gallery2/hq_face_cage_lights_on_look_up.png (1600 x 900, fov 75, gamma 0.5): the median colour of flat
# concrete faces (purple, lime, yellow, grey) against the block-light level this module's own simulation gives the cell in front of
# them.  The curve is close to linear in the level (level 13 = 0.92 of level 15, level 10 = 0.73, level 7 = 0.49, level 4 = 0.32), with
# a warm tint below 14 (blue falls first) and the biome's cold ambient floor at 0.  (The earlier curve, level/(4-3 level) with a gamma
# mix, put level 13 at 0.80 and level 10 at 0.57: too dark in the middle and too steep at the bottom.)
LIGHTMAP_LUT = np.array([
    (0.115, 0.150, 0.260), (0.160, 0.215, 0.300), (0.200, 0.240, 0.320), (0.250, 0.280, 0.340),
    (0.320, 0.320, 0.340), (0.380, 0.370, 0.380), (0.420, 0.410, 0.380), (0.490, 0.460, 0.400),
    (0.550, 0.500, 0.420), (0.670, 0.620, 0.500), (0.730, 0.680, 0.550), (0.790, 0.730, 0.600),
    (0.860, 0.810, 0.690), (0.925, 0.890, 0.760), (0.990, 0.970, 0.905), (1.000, 1.000, 1.000)], np.float32)
# directional face shade of the game: top 1.0, north/south 0.8, east/west 0.6, bottom 0.5
SHADE_TOP, SHADE_Z, SHADE_X, SHADE_BOTTOM = 1.0, 0.8, 0.6, 0.5


def lightmap_rgb(lv, gamma=None):
    """Colour multiplier for block light lv (0..1 = level / 15) from LIGHTMAP_LUT (linear between the levels).  (n,) -> (n, 3)."""
    x = np.clip(np.asarray(lv, np.float32) * 15.0, 0.0, 15.0)
    i0 = np.floor(x).astype(np.int32)
    i1 = np.minimum(i0 + 1, 15)
    t = (x - i0)[..., None]
    return (LIGHTMAP_LUT[i0] * (1 - t) + LIGHTMAP_LUT[i1] * t).astype(np.float32)


def raycast(a, tab, path, eye, target, fov=70.0, size=(960, 540), ortho=None, light=None, ambient=0.45, offset=(0, 0, 0),
            sky=(10, 10, 14), fog=0.0, maxd=700.0, gbuf=None):
    """Render the voxel array `a` (palette ids) from `eye` towards `target`.  Perspective by default (fov = vertical),
    orthographic when `ortho` = pixels per block.  `light` is an optional block-light grid (0..15) for true shading."""
    from PIL import Image
    rgb, kind, alpha, emit = tab
    ox, oy, oz = offset
    eye = np.array(eye, np.float64) - (ox, oy, oz)
    target = np.array(target, np.float64) - (ox, oy, oz)
    sx, sy, sz = a.shape
    W, H = size
    f = target - eye
    f /= np.linalg.norm(f)
    right = np.cross(f, [0, 1, 0])
    if np.linalg.norm(right) < 1e-6:
        right = np.array([1.0, 0, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, f)
    U, V = np.meshgrid((np.arange(W) + 0.5) / W * 2 - 1, 1 - (np.arange(H) + 0.5) / H * 2)
    if ortho:
        org = eye[None, None, :] + U[..., None] * (W / 2 / ortho) * right + V[..., None] * (H / 2 / ortho) * up
        d = np.broadcast_to(f, org.shape).copy()
    else:
        t = math.tan(math.radians(fov) / 2)
        d = f[None, None, :] + U[..., None] * t * (W / H) * right + V[..., None] * t * up
        d /= np.linalg.norm(d, axis=2, keepdims=True)
        org = np.broadcast_to(eye, d.shape).copy()
    org = org.reshape(-1, 3)
    d = d.reshape(-1, 3)
    N = org.shape[0]
    d = np.where(np.abs(d) < 1e-9, 1e-9, d)
    inv = 1.0 / d
    bmax = np.array([sx, sy, sz], np.float64)
    t1 = (0 - org) * inv
    t2 = (bmax - org) * inv
    tnear = np.minimum(t1, t2).max(axis=1)
    tfar = np.maximum(t1, t2).min(axis=1)
    valid = tfar > np.maximum(tnear, 0)
    t0 = np.maximum(tnear, 0) + 1e-4
    pos = org + d * t0[:, None]
    idx = np.nonzero(valid)[0]
    pos = pos[idx]
    dd = d[idx]
    cell = np.floor(pos).astype(np.int32)
    cell = np.clip(cell, 0, [sx - 1, sy - 1, sz - 1])
    step = np.sign(dd).astype(np.int32)
    tdelta = np.abs(1.0 / dd)
    tmax = np.where(dd > 0, (cell + 1 - pos) / dd, (cell - pos) / dd)
    tmax = np.where(np.isfinite(tmax), tmax, 1e18)
    # per-ray state
    col = np.zeros((N, 3), np.float32)
    col[:] = np.array(sky, np.float32)
    C = np.zeros((idx.size, 3), np.float32)       # accumulated translucent colour
    T = np.ones(idx.size, np.float32)
    lastid = np.zeros(idx.size, np.int32)
    lastax = np.zeros(idx.size, np.int32)
    tcur = t0[idx].copy()
    ids = np.arange(idx.size)
    final = np.zeros((idx.size, 3), np.float32)
    done = np.zeros(idx.size, bool)
    fshade = np.array([0.80, 1.0, 0.90], np.float32)  # by axis hit, with sign handling below
    steps = int(sx + sy + sz + 6)
    act = ids.copy()
    if gbuf is not None:                          # per-pixel hit record (palette id, axis, sign, light level of the lit cell) for calibration
        gbuf["cid"] = np.zeros(N, np.int32)
        gbuf["ax"] = np.full(N, -1, np.int8)
        gbuf["sg"] = np.zeros(N, np.int8)
        gbuf["lv"] = np.zeros(N, np.float32)
    for _ in range(steps):
        if act.size == 0:
            break
        c = cell[act]
        cid = a[c[:, 0], c[:, 1], c[:, 2]].astype(np.int32)
        k = kind[cid]
        # opaque hit
        hit = k == 1
        if hit.any():
            hi = act[hit]
            hc = c[hit]
            ax = lastax[hi]
            sg = step[hi, ax]
            sh = np.where(ax == 1, np.where(sg < 0, SHADE_TOP, SHADE_BOTTOM), np.where(ax == 0, SHADE_X, SHADE_Z)).astype(np.float32)
            base = rgb[cid[hit]]
            if light is not None:
                pc = hc.copy()
                pc[np.arange(hi.size), ax] -= sg
                pc = np.clip(pc, 0, [sx - 1, sy - 1, sz - 1])
                lv = light[pc[:, 0], pc[:, 1], pc[:, 2]].astype(np.float32) / 15.0
                lum = lightmap_rgb(lv) * sh[:, None]       # (emitters are lit by the 14 or 15 of the air beside them, like everything else)
            else:
                lum = (ambient + (1 - ambient) * sh)[:, None]
                em = emit[cid[hit]] > 0
                lum = np.where(em[:, None], 1.15, lum)
            colr = base * lum
            if gbuf is not None:
                gi = idx[hi]
                gbuf["cid"][gi] = cid[hit]
                gbuf["ax"][gi] = ax
                gbuf["sg"][gi] = sg
                if light is not None:
                    gbuf["lv"][gi] = lv * 15.0
            if fog > 0:
                tf = np.exp(-fog * tcur[hi])[:, None]
                colr = colr * tf + np.array(sky, np.float32) * (1 - tf)
            final[hi] = C[hi] + T[hi][:, None] * colr
            done[hi] = True
        # translucent
        tr = (k == 2) | (k == 3)
        if tr.any():
            ti = act[tr]
            tid = cid[tr]
            newl = lastid[ti] != tid
            ti2 = ti[newl]
            tid2 = tid[newl]
            if ti2.size:
                al = alpha[tid2]
                base = rgb[tid2]
                if light is not None:
                    cc = cell[ti2]
                    lv = light[cc[:, 0], cc[:, 1], cc[:, 2]].astype(np.float32) / 15.0
                    base = base * lightmap_rgb(lv)
                C[ti2] += (T[ti2] * al)[:, None] * base
                T[ti2] *= (1 - al)
            lastid[ti] = tid
        else:
            pass
        if hit.any():
            act = act[~hit]
        # step
        if act.size == 0:
            break
        tm = tmax[act]
        ax = np.argmin(tm, axis=1)
        r = np.arange(act.size)
        tcur[act] = tm[r, ax]
        cell[act, ax] += step[act, ax]
        tmax[act, ax] += tdelta[act, ax]
        lastax[act] = ax
        cc = cell[act]
        inb = (cc[:, 0] >= 0) & (cc[:, 0] < sx) & (cc[:, 1] >= 0) & (cc[:, 1] < sy) & (cc[:, 2] >= 0) & (cc[:, 2] < sz) & (tcur[act] < maxd)
        out = act[~inb]
        if out.size:
            final[out] = C[out] + T[out][:, None] * np.array(sky, np.float32)
        act = act[inb]
    if act.size:
        final[act] = C[act] + T[act][:, None] * np.array(sky, np.float32)
    col[idx] = final
    img = np.clip(col.reshape(H, W, 3), 0, 255).astype(np.uint8)
    Image.fromarray(img).save(path)
    return img


def partial_masks(w):
    """(n, 2, 2, 2) bool [wx, wy, wz]: the part of its block each palette entry fills (full unless a slab or a stair)."""
    M = np.ones((len(w.palette), 2, 2, 2), bool)
    for i, b in enumerate(w.palette):
        if not b:
            continue
        name, _, rest = b.partition("[")
        props = dict(kv.split("=") for kv in rest.rstrip("]").split(",")) if rest else {}
        if name.endswith("_slab") and props.get("type", "bottom") != "double":
            M[i] = False
            M[i][:, 0 if props.get("type", "bottom") == "bottom" else 1, :] = True
        elif name.endswith("_stairs"):
            M[i] = stair_mask(props["facing"], props["half"], props["shape"])
    return M


def partial_flags(w):
    return partial_masks(w).reshape(len(w.palette), 8).sum(axis=1) < 8


def raycast_fine(w, tab, path, eye, target, crop, light=None, ortho=None, **kw):
    """raycast() at half-block resolution inside `crop` = ((x0, y0, z0), (x1, y1, z1)) cells, so that stairs and slabs show
    their real shape.  Coordinates are the set's, as for raycast()."""
    lo, hi = crop
    sl = tuple(slice(l, h) for l, h in zip(lo, hi))
    a = w.a[sl]
    M = partial_masks(w)
    nx, ny, nz = a.shape
    E = np.where(M[a], a[..., None, None, None], 1).astype(np.uint16)
    E = E.transpose(0, 3, 1, 4, 2, 5).reshape(2 * nx, 2 * ny, 2 * nz)
    Lf = None
    if light is not None:
        Lc = light[sl]
        part = (M.reshape(len(M), 8).sum(axis=1) < 8)[a]
        if part.any():
            from scipy.ndimage import maximum_filter
            Lc = np.where(part, maximum_filter(Lc, size=3), Lc)
        Lf = np.repeat(np.repeat(np.repeat(Lc, 2, 0), 2, 1), 2, 2)
    off = np.array(lo, float)
    e = tuple((np.array(eye, float) - off) * 2.0)
    t = tuple((np.array(target, float) - off) * 2.0)
    return raycast(E, tab, path, e, t, ortho=(ortho / 2.0 if ortho else None), light=Lf, **kw)

def sees(a, tab, p, q, transparent_kinds=(0, 2, 3), masks=None):
    """Line of sight from point p to point q through the voxel array (glass, bars and air let it through).  With `masks`
    (partial_masks) a ray is only stopped by the filled part of a slab or stair.  Returns (clear, cell_first_blocking or None)."""
    rgb, kind, alpha, emit = tab
    p = np.array(p, float)
    q = np.array(q, float)
    d = q - p
    L = np.linalg.norm(d)
    d /= L
    n = int(L * 8) + 1
    for i in range(1, n):
        s = p + d * (L * i / n)
        c = tuple(np.floor(s).astype(int))
        if not (0 <= c[0] < a.shape[0] and 0 <= c[1] < a.shape[1] and 0 <= c[2] < a.shape[2]):
            return False, c
        if a[c] == 0:
            return False, c
        if kind[a[c]] not in transparent_kinds and a[c] != 1:
            if masks is not None and not masks[a[c]].all():
                o = np.clip(np.floor((s - np.array(c)) * 2).astype(int), 0, 1)
                if not masks[a[c]][o[0], o[1], o[2]]:
                    continue
            tc = tuple(np.floor(q).astype(int))
            if c != tc:
                return False, c
    return True, None


# ================================================================================================ SHAPES: STAIRS AND SLABS
# Everything sculpted below is a continuous solid sampled at half-block resolution (2 x 2 x 2 samples per block).  Each block
# then becomes the full block, slab or stair (straight or corner) whose shape agrees best with its eight samples, which is
# what lets slopes, chamfers, the chin point and the horn taper read finer than a block grid.
_DIRV = {"north": (0, -1), "south": (0, 1), "west": (-1, 0), "east": (1, 0)}
_CCW = {"north": "west", "west": "south", "south": "east", "east": "north"}
STAIR_SHAPES = ("straight", "outer_left", "outer_right", "inner_left", "inner_right")
QUANT_SHAPES = ("straight",)          # corner stairs make a speckled surface; slabs and straight stairs read cleaner


def _side(d):
    """Sub-cells (wx, wz) on side d of a block; wx 0 west / 1 east, wz 0 north / 1 south."""
    return {(x, z) for x in (0, 1) for z in (0, 1)
            if (d[0] == -1 and x == 0) or (d[0] == 1 and x == 1) or (d[1] == -1 and z == 0) or (d[1] == 1 and z == 1)}


def stair_mask(facing, half, shape):
    """Occupied octants [wx, wy, wz] of a stair block (the high back is on the facing side; left is counter-clockwise)."""
    m = np.zeros((2, 2, 2), bool)
    base = 0 if half == "bottom" else 1
    m[:, base, :] = True
    f = _DIRV[facing]
    left = _DIRV[_CCW[facing]]
    right = (-left[0], -left[1])
    if shape == "straight":
        cells = _side(f)
    elif shape == "outer_left":
        cells = _side(f) & _side(left)
    elif shape == "outer_right":
        cells = _side(f) & _side(right)
    elif shape == "inner_left":
        cells = _side(f) | _side(left)
    else:
        cells = _side(f) | _side(right)
    for (x, z) in cells:
        m[x, 1 - base, z] = True
    return m


def _candidates():
    c = [(("empty",), np.zeros((2, 2, 2), bool)), (("full",), np.ones((2, 2, 2), bool))]
    for t, y in (("bottom", 0), ("top", 1)):
        m = np.zeros((2, 2, 2), bool)
        m[:, y, :] = True
        c.append((("slab", t), m))
    for shape in QUANT_SHAPES:
        for half in ("bottom", "top"):
            for f in ("north", "south", "east", "west"):
                c.append((("stair", f, half, shape), stair_mask(f, half, shape)))
    return c


_BITW = np.zeros((2, 2, 2), np.int64)
for _x in range(2):
    for _y in range(2):
        for _z in range(2):
            _BITW[_x, _y, _z] = 1 << (_x * 4 + _y * 2 + _z)
_CANDS = _candidates()
_CODES = [int((m * _BITW).sum()) for _, m in _CANDS]


def _build_lut():
    lut = np.zeros(256, np.int32)
    order = [1, 0] + list(range(2, len(_CANDS)))              # a tie between full and empty keeps the mass
    for c in range(256):
        best, bi = 99, 1
        for i in order:
            d = bin(c ^ _CODES[i]).count("1")
            if d <= (99 if i < 2 else 1) and d < best:        # slabs and stairs only when (nearly) exact
                best, bi = d, i
        lut[c] = bi
    return lut


_LUT = _build_lut()
NO_SHAPE = ("obsidian", "iron_block", "amethyst_block")      # materials with no stairs or slabs


def quantize(sub):
    """Boolean samples (2nx, 2ny, 2nz) in world orientation -> candidate index per block (0 empty, 1 full, 2.. slabs, stairs)."""
    nx, ny, nz = (s // 2 for s in sub.shape)
    s = sub.reshape(nx, 2, ny, 2, nz, 2).transpose(0, 2, 4, 1, 3, 5)
    return _LUT[(s * _BITW).sum(axis=(3, 4, 5))]


def shape_block(mat, ci):
    d = _CANDS[ci][0]
    if d[0] == "full":
        return mat
    base = PURPLE if mat in NO_SHAPE else mat
    if d[0] == "slab":
        return bs(base + "_slab", type=d[1])
    return bs(base + "_stairs", facing=d[1], half=d[2], shape=d[3])


def sub_axes(x0, x1, y0, y1, z0, z1):
    """World coordinates of the half-block sample centres over the cells x0..x1, y0..y1, z0..z1."""
    X = (x0 + (np.arange(2 * (x1 - x0 + 1)) + 0.5) / 2.0)[:, None, None]
    Y = (y0 + (np.arange(2 * (y1 - y0 + 1)) + 0.5) / 2.0)[None, :, None]
    Z = (z0 + (np.arange(2 * (z1 - z0 + 1)) + 0.5) / 2.0)[None, None, :]
    return X, Y, Z


# ================================================================================================ THE GIANT'S HEAD
# Head grid: ix 0..20 (x = HEAD_X0 + ix, mirror symmetric about ix 10), iy 0.. (y = HEAD_Y0 + iy, iy 0 is the chin underside),
# iz 0.. (z = HEAD_ZF - iz, iz 0 the front-most cell).  Head coordinates: u across from the centre line, v up from the chin
# underside, s back from the front plane (s = iz at a cell's front face).  The face looks south, at the bridge.
HC = 10
HW, HH, HD = 21, 40, 28
EYE_IZ = 5                      # the lit eye block sits in cell iz 5, flush with the face plate (it was iz 6, a one-deep recess: the sill and
                                # the brow hid 16 to 64 percent of each eye from the stop, which looks up at the slits at 20 to 30 degrees)
EYE_K = (2, 3, 4, 5, 6)         # |ix - HC| of the cells of one eye: five long and ONE high, stepping up towards the temple
NOSE_PROUD = 1.8
HALF_W = 7.4                    # half width of the face at the brow: fifteen blocks
HORN_TOP = 30.5                  # v of the horn tip (the stop sees chin tip to horn tip in about 100 degrees)


def eye_low(k):
    """Row (iy) of the eye slit at |ix - HC| = k.  The slit is one row high, climbs outwards (an angry glare) and sits in the
    top row of the old two-row socket, so the brow's overhang roofs it.  The player looks up at it from 5 to 9 blocks below, so
    the one-deep recess and the sill cut the lit face down to well under a block of glow."""
    return int(math.floor(17.0 + 0.5 * (k - 1.5))) - 1


def _hsub():
    U = ((np.arange(2 * HW) + 0.5) / 2.0 - (HC + 0.5))[:, None, None]
    V = ((np.arange(2 * HH) + 0.5) / 2.0)[None, :, None]
    S = ((np.arange(2 * HD) + 0.5) / 2.0)[None, None, :]
    return U, V, S


def head_field(horn_on=True):
    """Boolean occupancy of the head on its half-block sample grid (2HW, 2HH, 2HD), head orientation."""
    Us, V, S = _hsub()
    U = np.abs(Us)
    cap = np.minimum(0.55 + 0.37 * V, HALF_W)                       # steady taper from the brow down to the chin point
    # cranium: a swept-back dome (sheared ellipsoid) and the long wedge of the lower face
    Sc = S - 0.25 * (V - 18.0)
    cran = ((U / HALF_W) ** 3 + (np.abs(V - 17.5) / 8.8) ** 3) ** (2.0 / 3.0) + ((Sc - 13.5) / 9.8) ** 2 <= 1.0
    vb = np.clip((S - 3.2) * 0.55, 0.0, None)                     # the jaw's underside climbs from the chin to the throat
    wedge = (V >= vb) & (V <= 21.5) & (S <= 15.0)
    tt = U / np.maximum(cap, 0.5)
    rec = 3.0 * np.clip((tt - 0.55) / 0.45, 0, 1) ** 1.5          # the face plate is flat and falls away at its edges
    recv = rec * (V >= 9.0)
    chin = 2.0 + 0.23 * V + 0.9 * U                              # chin plate: a prow, point forward
    F0 = np.where(V < 9.0, chin, np.where(V < 10.0, 6.0, 5.0)) + recv
    base = (cran | wedge) & (U <= cap) & (S >= F0)
    # brow ridge: a heavy overhang over the eyes, lowest at the nose and climbing to the temples
    vbb = 17.0 + 0.5 * np.maximum(U - 1.5, 0.0)
    recb = 3.0 * np.clip((U - 5.4) / 2.3, 0, 1) ** 1.5
    Fb = 3.5 + np.maximum(0.0, V - (vbb + 2.0)) + recb
    ub = HALF_W - 0.9 * np.maximum(0.0, V - (vbb + 1.5)) ** 1.2          # the ridge rounds off into the temple, no tufts
    brow = (V >= vbb) & (V <= vbb + 4.6) & (U <= ub) & (S >= Fb) & (S <= 8.0)
    # nose ridge and cheek plates
    nose = (U < 1.0) & (V >= 10.0) & (V <= 17.5) & (S >= 5.0 - NOSE_PROUD * np.clip(1 - U / 1.0, 0, 1)) & (S <= 8.0)
    kk = np.rint(U)
    lowv = np.floor(17.0 + 0.5 * (kk - 1.5)) - 2.0
    cheek = (U >= 1.6) & (U <= cap - 0.4) & (V >= 10.0) & (V < lowv - 0.5) & (S >= 4.2 + recv) & (S <= 8.0)
    # horn: one blade rising from the middle of the forehead, up and forward, a crescent in profile, tapering to a point
    hv = np.clip((V - 20.5) / (HORN_TOP - 20.5), 0.0, 1.0)             # 0 at the root, 1 at the tip
    lead = 5.0 - 0.7 * hv ** 1.6                                      # the leading edge rises from the brow and leans forward
    trail = 4.3 + 6.5 * np.clip((HORN_TOP - V) / 6.5, 0.0, 3.0) ** 0.9
    hx = np.where(hv < 0.45, 1.5, 0.4 + 1.1 * ((1.0 - hv) / 0.55) ** 1.5)   # three wide at the root, one wide above
    horn = (V >= 19.5) & (V <= HORN_TOP) & (S >= lead) & (S <= trail) & (U <= hx)
    carve = np.zeros(base.shape, bool)
    for k in EYE_K:
        lo = eye_low(k)
        carve |= (np.abs(U - k) < 0.5) & (V >= lo) & (V < lo + 1) & (S < EYE_IZ)
    return (base | brow | nose | cheek | (horn if horn_on else False)) & ~carve


def head_blocks():
    """(names, (left_eye_cells, right_eye_cells), cand): names is an object array (HW, HH, HD), '' for air; eye cells are
    head-grid triples; cand is the quantised shape index per cell."""
    occ = head_field()
    cand = quantize(occ[:, :, ::-1])[:, :, ::-1]                 # to world orientation and back
    eyes_l, eyes_r = [], []
    for k in EYE_K:
        for r in (0,):
            for sgn in (-1, 1):
                ix, iy = HC + sgn * k, eye_low(k) + r
                cand[ix, iy, EYE_IZ] = 1
                (eyes_l if sgn < 0 else eyes_r).append((ix, iy, EYE_IZ))
    occc = cand > 0
    full = cand == 1
    below = np.zeros_like(occc)
    below[:, 1:, :] = occc[:, :-1, :]
    above = np.zeros_like(occc)
    above[:, :-1, :] = occc[:, 1:, :]
    mat = np.full(cand.shape, "", dtype=object)
    mat[occc] = PURPLE
    iy_, iz_ = np.arange(HH)[None, :, None], np.arange(HD)[None, None, :]
    ix_ = np.arange(HW)[:, None, None]
    brow_under = (iy_ >= 16) & (iy_ <= 21) & (iz_ >= 5) & (iz_ <= 6) & (np.abs(ix_ - HC) <= 6)       # the ceiling of the eye socket
    jaw_under = (iy_ <= 8) | ((iy_ <= 10) & (iz_ <= 5))
    mat[full & ~below & above & (brow_under | jaw_under)] = PURPLE_DARK      # the undersides of the brow, jaw and chin
    # jaw seam
    for d in range(-3, 4):
        if occc[HC + d, 9, 6]:
            mat[HC + d, 9, 6] = BLACK

    def front_cell(ix, iy, zmax=HD):
        col = np.nonzero(occc[ix, iy, :zmax])[0]
        return int(col[0]) if col.size else None

    # the nose ridge stands between two dark channels down the face
    for iy in range(10, 16):
        for sgn in (-1, 1):
            iz = front_cell(HC + sgn, iy, 7)
            if iz is not None and full[HC + sgn, iy, iz]:
                mat[HC + sgn, iy, iz] = PURPLE_DARK
    # lime: centre spine up the forehead and along the horn
    for iy in range(18, HH):
        iz = front_cell(HC, iy)
        if iz is not None:
            mat[HC, iy, iz] = LIME
    # lime: the brow edge, following its slant
    brow_row = lambda d: int(math.floor(17.0 + 0.5 * max(d - 1.5, 0.0)))
    for d in range(0, 8):
        top = brow_row(d + 1) if d < 7 else brow_row(d)             # each column also carries the step up to the next one, so the line is unbroken
        for row in range(brow_row(d), top + 1):
            for sgn in ((-1, 1) if d else (1,)):
                ix = HC + sgn * d
                iz = front_cell(ix, row, 7)
                if iz is not None:
                    mat[ix, row, iz] = LIME
    # lime: chin stripe down the front and under the point
    for iy in range(0, 9):
        iz = front_cell(HC, iy)
        if iz is not None:
            mat[HC, iy, iz] = LIME
    for iz in range(0, 9):
        col = np.nonzero(occc[HC, :, iz])[0]
        if col.size:
            mat[HC, int(col[0]), iz] = LIME
    for sgn in (-1, 1):                                              # two small orange status studs at the ends of the seam
        iz = front_cell(HC + sgn * 4, 9)
        if iz is not None:
            mat[HC + sgn * 4, 9, iz] = ORANGE
    names = np.full(cand.shape, "", dtype=object)
    for ix, iy, iz in zip(*np.nonzero(occc)):
        names[ix, iy, iz] = shape_block(mat[ix, iy, iz], cand[ix, iy, iz])
    for (ix, iy, iz) in eyes_l + eyes_r:
        names[ix, iy, iz] = EYE_OFF
    return names, (eyes_l, eyes_r), cand


def head_stats():
    """Size of the head as built (cells): face width and height (chin underside to crown, horn left out), height with the horn,
    depth, and the world y range of the eye cells."""
    c = quantize(head_field(False)[:, :, ::-1])[:, :, ::-1] > 0
    ch = quantize(head_field(True)[:, :, ::-1])[:, :, ::-1] > 0
    xs, ys, zs = np.nonzero(c)
    _, ysh, _ = np.nonzero(ch)
    ey = [HEAD_Y0 + iy for (_, iy, _) in [(0, eye_low(k) + r, 0) for k in EYE_K for r in (0,)]]
    return dict(width=int(xs.max() - xs.min() + 1), height=int(ys.max() + 1), height_horn=int(ysh.max() + 1), depth=int(zs.max() - zs.min() + 1),
                eye_lo=min(ey) + 0.0, eye_hi=max(ey) + 1.0)

# ---- neck, shoulders, pylons (world coordinates)
def giant_upper(w, with_head=True):
    """Head poking out of the coolant above the neck; registers EYES_LEFT / EYES_RIGHT (world cells, EYE_OFF / EYE_ON)."""
    names, (el, er), cand = head_blocks()
    for ix, iy, iz in zip(*np.nonzero(names != "")):
        w.set(HEAD_X0 + ix, HEAD_Y0 + iy, HEAD_ZF - iz, names[ix, iy, iz])
    EYES_LEFT[:] = sorted((HEAD_X0 + ix, HEAD_Y0 + iy, HEAD_ZF - iz) for ix, iy, iz in el)
    EYES_RIGHT[:] = sorted((HEAD_X0 + ix, HEAD_Y0 + iy, HEAD_ZF - iz) for ix, iy, iz in er)


def place_field(w, box_, sub, matfn):
    """Quantise `sub` (samples over the cells box_ = (x0, x1, y0, y1, z0, z1)) and place it; matfn(x, y, z cell grids) -> names."""
    x0, x1, y0, y1, z0, z1 = box_
    cand = quantize(sub)
    gx, gy, gz = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1), np.arange(z0, z1 + 1), indexing="ij")
    mat = matfn(gx, gy, gz, cand)
    for ix, iy, iz in zip(*np.nonzero(cand > 0)):
        w.set(x0 + ix, y0 + iy, z0 + iz, shape_block(mat[ix, iy, iz], cand[ix, iy, iz]))
    return cand

def _tube(w, cells, pts, r0, r1, colour_fn):
    """Sweep a tapering tube along the polyline pts (world coords); colour_fn(t, dist_frac, p) -> block."""
    pts = np.array(pts, float)
    seg = [np.linspace(pts[i], pts[i + 1], 40) for i in range(len(pts) - 1)]
    path = np.vstack(seg)
    tt = np.linspace(0, 1, len(path))
    lo = np.floor(path.min(axis=0) - r0 - 1).astype(int)
    hi = np.ceil(path.max(axis=0) + r0 + 1).astype(int)
    for x in range(lo[0], hi[0] + 1):
        for y in range(lo[1], hi[1] + 1):
            for z in range(lo[2], hi[2] + 1):
                d = np.sqrt(((path - (x + 0.5, y + 0.5, z + 0.5)) ** 2).sum(axis=1))
                i = d.argmin()
                rad = r0 + (r1 - r0) * tt[i]
                if d[i] <= rad:
                    cells[(x, y, z)] = colour_fn(tt[i], d[i] / rad, (x, y, z))


def hand_cells(raised, ref=(CX, BRIDGE_Y, SHIELD_Z)):
    """The giant's right hand and forearm as {(x,y,z): block}.  ref is the shield column (x, deck row, z).  The forearm
    always starts inside the right shoulder, so the two versions can be swapped with a plain clear-and-place."""
    rx, ry, rz = ref
    cells = {}

    def arm_col(t, d, p):
        band = int(t * 14)
        if band % 5 == 4:
            return LIME
        if d > 0.8:
            return PURPLE_LIT if p[1] >= ry - 17 else PURPLE
        return PURPLE if band % 2 else PURPLE_LIT

    if raised:
        shoulder = (rx - 15, ry - 14, SHOULDER_Z)                 # the shoulder is fixed on the giant; the reach grows with the stop
        wrist = (rx - 7, ry + 8, rz - 2)
        _tube(None, cells, [shoulder, (rx - 12, ry - 3, (SHOULDER_Z + rz - 2) // 2), wrist], 4.3, 3.0, arm_col)
        for x in range(rx - 4, rx + 5):          # cuff
            pass
        # hand: palm-down roof 11 wide, 7 long, fingers pointing south.  From below (where the player stands) the palm reads as
        # armour: violet with a darker pattern, dark knuckle joints, a lime rim and lime fingertips.
        y0 = ry + 8
        for x in range(rx - 5, rx + 6):
            for z in range(rz - 4, rz + 3):
                if x in (rx - 5, rx + 5) or z == rz - 4:
                    ub = LIME                                              # rim of the palm
                elif z == rz + 2:
                    ub = PURPLE_DARK                                       # knuckle line at the finger roots
                elif (x - rx) % 4 == 0 and z <= rz:
                    ub = PURPLE                                            # tendon grooves
                else:
                    ub = PURPLE_LIT
                cells[(x, y0, z)] = ub                                     # palm (underside)
                cells[(x, y0 + 1, z)] = PURPLE
                cells[(x, y0 + 2, z)] = PURPLE_LIT if (x + z) % 6 else LIME   # back of the hand
        for x in range(rx - 5, rx + 6):
            cells[(x, y0 + 2, rz - 4)] = LIME_DARK
        for i, fx in enumerate((rx - 5, rx - 2, rx + 1, rx + 4)):         # four fingers, 2 wide
            ln = (5, 6, 6, 5)[i]
            for dz in range(ln):
                z = rz + 3 + dz
                dropy = 1 if dz >= ln - 2 else 0
                for x in (fx, fx + 1):
                    joint = dz % 3 == 2 and dz < ln - 1
                    cells[(x, y0 + 1 - dropy, z)] = PURPLE_DARK if joint else PURPLE_LIT      # underside of the finger
                    cells[(x, y0 + 2 - dropy, z)] = PURPLE_LIT if dz % 3 != 2 else LIME
                    if dz == ln - 1:
                        cells[(x, y0 - dropy + 1, z)] = LIME                                  # lime fingertips
                        cells[(x, y0 + 2 - dropy, z)] = LIME
        for k in range(4):                        # thumb on the west side, angled down
            for x in (rx - 8 + 0, rx - 7, rx - 6):
                for z in (rz - 2 + k // 2, rz - 1 + k // 2):
                    cells[(x, y0 + 1 - (k // 2), z + k)] = LIME if k == 3 else (PURPLE_DARK if k == 2 else PURPLE_LIT)
                    cells[(x, y0 + 2 - (k // 2), z + k)] = PURPLE_LIT
    else:
        shoulder = (rx - 15, ry - 17, SHOULDER_Z)
        wrist = (rx - 12, ry - 17, rz - 3)
        _tube(None, cells, [shoulder, (rx - 13, ry - 17, (SHOULDER_Z + rz - 3) // 2), wrist], 3.8, 3.0, arm_col)
        y0 = ry - 18                              # top of the hand just above the coolant (SURF = 36 -> 35..38 shows)
        for x in range(rx - 17, rx - 7):
            for z in range(rz - 3, rz + 4):
                cells[(x, y0, z)] = PURPLE
                cells[(x, y0 + 1, z)] = PURPLE
                cells[(x, y0 + 2, z)] = PURPLE_LIT if (x + z) % 5 else LIME
        for i, fx in enumerate((rx - 17, rx - 14, rx - 11, rx - 8)):
            ln = (5, 6, 6, 5)[i]
            for dz in range(ln):
                z = rz + 4 + dz
                for x in (fx, fx + 1):
                    cells[(x, y0 + 1, z)] = PURPLE
                    cells[(x, y0 + 2, z)] = PURPLE_LIT if dz % 3 != 2 else LIME
                    if dz == ln - 1:
                        cells[(x, y0 + 2, z)] = LIME_DARK
        for k in range(4):
            for x in (rx - 6, rx - 5):
                cells[(x, y0 + 1, rz - 1 + k)] = PURPLE
                cells[(x, y0 + 2, rz - 1 + k)] = PURPLE_LIT
    return cells


def hand_bbox(raised):
    c = hand_cells(raised)
    xs, ys, zs = zip(*c.keys())
    return (min(xs), min(ys), min(zs), max(xs), max(ys), max(zs))


def hand(w, x, y, z, raised):
    """Place the giant's right hand and forearm.  (x, y, z) is the shield column on the bridge: x, deck row, z.  The hand
    version not wanted must be cleared first (see hand_bbox) - clear the box with air, then place the other."""
    for (px, py, pz), b in hand_cells(raised, (x, y, z)).items():
        w.set(px, py, pz, b)


def giant_full(w):
    """Head, neck, shoulders, pylons and the submerged body (seen dark through the coolant); right hand lowered."""
    # --- submerged torso, visible as a dark shape through the tinted glass
    box(w, CX - 22, FLOOR_C + 1, 28, CX + 22, SURF, 60, "polished_blackstone")
    box(w, CX - 18, FLOOR_C + 1, 40, CX + 18, SURF, 58, "obsidian")
    for z in range(30, 60, 6):
        box(w, CX - 22, FLOOR_C + 1, z, CX + 22, SURF - 14, z, PURPLE)       # armour seams seen through the liquid
    # --- chest and shoulders above the coolant: one violet mass, a dark waterline band, the collar rising to the neck
    bx = (CX - 25, CX + 25, SURF + 1, SURF + 11, 30, 61)
    X, Y, Z = sub_axes(*bx)
    dx = X - (CX + 0.5)
    foot = (dx / 23.5) ** 2 + ((Z - 45.0) / 14.5) ** 2 <= 1.0
    top = SURF + 4.0 + 5.0 * np.clip(1.0 - np.abs(dx) / 13.0, 0.0, 1.0)

    def chest_mat(gx, gy, gz, cand):
        m = np.where(gy <= SURF + 2, "polished_blackstone", PURPLE).astype(object)
        m[cand <= 0] = ""
        return m
    place_field(w, bx, foot & (Y <= top), chest_mat)
    # --- neck: narrower than the jaw, tapering upwards, dark and banded
    bx = (CX - 7, CX + 7, SURF + 3, HEAD_Y0 + 12, 40, 58)
    X, Y, Z = sub_axes(*bx)
    r = np.maximum(3.6, 5.6 - 0.13 * (Y - 40.0))
    sub = ((X - (CX + 0.5)) / r) ** 2 + ((Z - 49.5) / (r * 1.05)) ** 2 <= 1.0

    def neck_mat(gx, gy, gz, cand):
        m = np.where(((gy - (SURF + 3)) // 2) % 2 == 0, BLACK, GRAY).astype(object)
        m[cand <= 0] = ""
        return m
    place_field(w, bx, sub, neck_mat)
    # --- pylons: a tall fin and a low wing on each shoulder, trimmed in lime along the top and the front edge
    for sgn in (-1, 1):
        for (xa, xb, z0, z1, kind) in ((13, 14, 38, 56, "tall"), (18, 19, 41, 53, "wing")):
            xs = (CX + xa, CX + xb) if sgn > 0 else (CX - xb, CX - xa)
            bx = (xs[0], xs[1], SURF + 3, 78, z0 - 1, z1 + 1)
            X, Y, Z = sub_axes(*bx)
            if kind == "tall":
                ytop = 74.0 - 1.15 * (Z - 38.0)
            else:
                ytop = 52.0 + 8.0 * (1.0 - ((Z - 47.0) / 6.5) ** 2)
            sub = (X >= xs[0]) & (Z >= z0) & (Z <= z1 + 1.0) & (Y <= ytop)

            def fin_mat(gx, gy, gz, cand):
                occ = cand > 0
                air_above = np.ones_like(occ)
                air_above[:, :-1, :] = ~occ[:, 1:, :]
                air_south = np.ones_like(occ)
                air_south[:, :, :-1] = ~occ[:, :, 1:]
                m = np.where(gy < SURF + 7, BLACK, PURPLE).astype(object)
                inner = gx == (CX - xa if sgn < 0 else CX + xa)       # the column facing the head
                trim = (occ & air_above) | (occ & air_south & inner)
                m[trim & (gy >= SURF + 7)] = LIME
                m[~occ] = ""
                return m
            place_field(w, bx, sub, fin_mat)
    giant_upper(w)
    hand(w, CX, BRIDGE_Y, SHIELD_Z, False)


def giant_lights(w):
    """Light for the shoulders and pylons so the giant's shape shows when the lights come on: lamp bars set into the inner
    faces of the tall fins (they also rake the sides of the head), and a few hidden light blocks over the collar and under the jaw.
    Built after the giant so that the stage previews of the bare giant do not carry them."""
    for sgn in (-1, 1):
        lx = CX + sgn * 13 if sgn > 0 else CX - 13
        for y in (58, 62, 66):
            lamp(w, lx, y, 44)
        for z in (46, 50):                       # (56 was inside the raised forearm)
            CAGE_LIGHTS.append((CX + sgn * 12, 44, z, bs("light", level=12)))
    CAGE_LIGHTS.append((CX, 46, 58, bs("light", level=12)))
    for sgn in (-1, 1):
        CAGE_LIGHTS.append((CX + sgn * 16, 44, 46, bs("light", level=11)))

# ================================================================================================ letters on walls
FONT = {
    "0": ("###", "# #", "# #", "# #", "###"), "1": (" # ", "## ", " # ", " # ", "###"), "2": ("###", "  #", "###", "#  ", "###"),
    "3": ("###", "  #", "###", "  #", "###"), "4": ("# #", "# #", "###", "  #", "  #"), "5": ("###", "#  ", "###", "  #", "###"),
    "6": ("###", "#  ", "###", "# #", "###"), "7": ("###", "  #", "  #", " # ", " # "), "8": ("###", "# #", "###", "# #", "###"),
    "9": ("###", "# #", "###", "  #", "###"), "A": ("###", "# #", "###", "# #", "# #"), "B": ("## ", "# #", "## ", "# #", "## "),
    "C": ("###", "#  ", "#  ", "#  ", "###"), "D": ("## ", "# #", "# #", "# #", "## "), "E": ("###", "#  ", "###", "#  ", "###"),
    "F": ("###", "#  ", "###", "#  ", "#  "), "G": ("###", "#  ", "# #", "# #", "###"), "H": ("# #", "# #", "###", "# #", "# #"),
    "I": ("###", " # ", " # ", " # ", "###"), "K": ("# #", "# #", "## ", "# #", "# #"), "L": ("#  ", "#  ", "#  ", "#  ", "###"),
    "N": ("###", "# #", "# #", "# #", "# #"), "O": ("###", "# #", "# #", "# #", "###"), "P": ("###", "# #", "###", "#  ", "#  "),
    "R": ("## ", "# #", "## ", "# #", "# #"), "S": ("###", "#  ", "###", "  #", "###"), "T": ("###", " # ", " # ", " # ", " # "),
    "U": ("# #", "# #", "# #", "# #", "###"), "X": ("# #", "# #", " # ", "# #", "# #"), "Y": ("# #", "# #", " # ", " # ", " # "),
    "Z": ("###", "  #", " # ", "#  ", "###"), "-": ("   ", "   ", "###", "   ", "   "), " ": ("   ",) * 5,
}


def stencil(w, text, plane, u0, v0, axis, step, scale, block, solid_only=False):
    """Write text on a wall.  axis 'x': the wall plane is x == plane and text runs along z; axis 'z': plane is a z and text runs along x.
    step is +1/-1, the direction u moves from one letter to the next as seen reading left to right."""
    u = u0
    for ch in text:
        g = FONT.get(ch)
        if g is not None:
            for r, row in enumerate(g):
                for c, pix in enumerate(row):
                    if pix != "#":
                        continue
                    for sy in range(scale):
                        for su in range(scale):
                            uu = u + step * (c * scale + su)
                            vv = v0 + (4 - r) * scale + sy
                            cell = (plane, vv, uu) if axis == "x" else (uu, vv, plane)
                            if solid_only and w.get(*cell) in (AIR, None):
                                continue                 # a numeral must stay on the wall: never float in the room beside it
                            w.set(*cell, block)
        u += step * 4 * scale


def lamp(w, x, y, z, on=LAMP_ON, group=None):
    """A main cage light: built OFF, listed in CAGE_LIGHTS with the block to use when on."""
    w.set(x, y, z, LAMP_OFF)
    CAGE_LIGHTS.append((x, y, z, on))
    if group is not None:
        group.append((x, y, z, on))


def hazard(u, v):
    """Yellow and dark-grey hazard stripes.  (The dark stripe used to be black concrete, which is pure black in any light and
    left half of every deck and wall band invisible.)"""
    return YELLOW if ((u + v) // 2) % 2 == 0 else "gray_concrete"


def emergency_lamp(w, x, y, z, hidden):
    """Red lamp that stays on: a red glass block with a hidden light block (level EMERGENCY_LEVEL) at `hidden`, which must be open
    air - if it is not, no lamp is built.  True if built."""
    if w.get(hidden[0], hidden[1], hidden[2]) != AIR:
        return False
    w.set(x, y, z, "red_stained_glass")
    w.set(hidden[0], hidden[1], hidden[2], bs("light", level=EMERGENCY_LEVEL))
    EMERGENCY.append((x, y, z))
    return True


# ================================================================================================ THE CAGE
CAGE = dict(x1=64, x2=128, z1=24, z2=137, y1=6, y2=111)       # interior
WALLM = "polished_blackstone"
WALLP = "deepslate_tiles"


def build_cage(w):
    c = CAGE
    X1, X2, Z1, Z2, Y1, Y2 = c["x1"], c["x2"], c["z1"], c["z2"], c["y1"], c["y2"]
    # ---------------- shell and interior
    box(w, X1 - 4, 2, Z1 - 4, X2 + 4, Y2 + 4, Z2 + 4, WALLM)
    carve(w, X1, Y1, Z1, X2, Y2, Z2)
    box(w, X1, 5, Z1, X2, 5, Z2, "gray_concrete")
    # ---------------- wall plating, ribs, warning bands, numerals
    for y in range(Y1, Y2 + 1):
        for u in range(Z1, Z2 + 1):
            for plane, inner in ((X1 - 1, X1), (X2 + 1, X2)):
                panel = ((u - Z1) % 12 == 0) or (y % 14 == 0)
                b = "chiseled_polished_blackstone" if (y % 14 == 7 and (u - Z1) % 12 == 6) else (WALLP if panel else WALLM)
                if y in (SURF + 1, SURF + 2) or y in (Y2 - 1, Y2):
                    b = hazard(u, y)
                w.set(plane, y, u, b)
                if (u - Z1) % 16 == 8 and y > SURF:
                    w.set(inner, y, u, "gray_concrete")
        for u in range(X1, X2 + 1):
            for plane, inner in ((Z1 - 1, Z1), (Z2 + 1, Z2)):
                panel = ((u - X1) % 12 == 0) or (y % 14 == 0)
                b = WALLP if panel else WALLM
                if y in (SURF + 1, SURF + 2) or y in (Y2 - 1, Y2):
                    b = hazard(u, y)
                w.set(u, y, plane, b)
                if (u - X1) % 16 == 8 and y > SURF:
                    w.set(u, y, inner, "gray_concrete")
    # numerals: big stencils on the side walls and the north wall
    stencil(w, "03", X1 - 1, 124, 74, "x", -1, 3, "white_concrete")
    stencil(w, "03", X2 + 1, 28, 74, "x", 1, 3, "white_concrete")
    stencil(w, "A-07", X1 - 1, 80, 90, "x", -1, 2, ORANGE)
    stencil(w, "A-07", X2 + 1, 70, 90, "x", 1, 2, ORANGE)
    pass
    stencil(w, "01", Z1 - 1, 86, 96, "z", 1, 4, "white_concrete")
    stencil(w, "01", Z2 + 1, 112, 80, "z", -1, 4, "white_concrete")
    pass
    # ---------------- coolant: tinted glass over a magma bed
    box(w, X1, FLOOR_C, Z1, X2, FLOOR_C, Z2, LIQUID_BED)
    box(w, X1, FLOOR_C + 1, Z1, X2, SURF, Z2, LIQUID)
    # ---------------- the giant
    giant_full(w)
    giant_lights(w)
    # ---------------- restraint arms from the walls, clamped against the shoulders
    for sgn in (-1, 1):
        wx = X1 if sgn < 0 else X2
        for zc in (40, 55):
            xs = range(X1, CX - 24) if sgn < 0 else range(CX + 25, X2 + 1)
            for x in xs:
                for z in range(zc - 1, zc + 3):
                    for y in range(SURF + 2, SURF + 6):
                        b = "gray_concrete"
                        if y == SURF + 5:
                            b = hazard(x, z)
                        w.set(x, y, z, b)
            padx = (CX - 25, CX - 24) if sgn < 0 else (CX + 24, CX + 25)
            for x in padx:
                box(w, x, SURF + 1, zc - 2, x, SURF + 7, zc + 4, IRON)
            # wall mount plate
            box(w, wx if sgn < 0 else wx, SURF, zc - 4, wx, SURF + 9, zc + 6, "polished_deepslate")
            lamp(w, X1 + 1 if sgn < 0 else X2 - 1, SURF + 7, zc + 1)
            ex = CX - 25 if sgn < 0 else CX + 25
            emergency_lamp(w, ex, SURF + 8, zc + 1, (ex, SURF + 9, zc + 1))
        # upper swing clamps from the mid catwalk, hanging over the pylons
        xs = range(X1, CX - 14) if sgn < 0 else range(CX + 15, X2 + 1)
        for x in xs:
            box(w, x, 66, 41, x, 68, 44, "gray_concrete")
        hx = CX - 15 if sgn < 0 else CX + 15
        box(w, hx, 60, 41, hx, 68, 44, IRON)
    # ---------------- umbilical bridge + side spur + supports
    build_bridge(w)
    build_catwalks(w)
    build_roof(w)
    build_booth(w)
    build_gurney_door(w)
    # ---------------- ceiling-height emergency lamps near the bridge start
    emergency_lamp(w, 92, 56, Z2, (92, 57, Z2))
    emergency_lamp(w, 100, 56, Z2, (100, 57, Z2))
    cage_lights_baseline(w)
    wall_detail(w)


BRIDGE_END = 71                # first deck row (z) at the giant's end: the deck stops one block short of the stop's feet


def build_bridge(w):
    z0, z1 = BRIDGE_END, 142
    # deck 5 wide (x 94..98), rails on 93 and 99, from the south door to the stop; it ends in a hazard lip and a clear
    # view of the giant's jaw (no end rail, no grating: from the stop's eye the deck edge is 47 degrees below the horizon,
    # under the chin tip).  Invisible barrier blocks keep walkers on the deck.
    for z in range(z0, z1 + 1):
        for x in range(94, 99):
            b = "light_gray_concrete"
            if z == z0:
                b = hazard(x, 0)
            elif x in (94, 98):
                b = hazard(z, 0)
            elif x == 96 and z % 4 < 2:
                b = YELLOW
            w.set(x, BRIDGE_Y, z, b)
        for x in (93, 99):
            w.set(x, BRIDGE_Y, z, "iron_block")
            for y in (BRIDGE_Y + 1, BRIDGE_Y + 2):
                if z <= CAGE["z2"]:
                    # the last four rows at the giant's end have an invisible rail (barrier): bars there would stand across the lines
                    # from the people on the marks (z 76.5) to the giant's left and right flank
                    w.set(x, y, z, "iron_bars" if z >= BRIDGE_END + 4 else "barrier")
    for x in range(93, 100):
        for y in (BRIDGE_Y + 1, BRIDGE_Y + 2, BRIDGE_Y + 3):
            w.set(x, y, z0 - 1, "barrier")
    # under-girder and pillars into the coolant
    box(w, 95, BRIDGE_Y - 3, z0, 97, BRIDGE_Y - 1, CAGE["z2"], "gray_concrete")
    for z in range(84, CAGE["z2"], 14):
        box(w, 95, FLOOR_C + 1, z, 97, BRIDGE_Y - 4, z + 1, "gray_concrete")
    for z in range(84, CAGE["z2"], 14):
        for k in range(1, 6):
            w.set(95 - k, BRIDGE_Y - 3 - k + 1, z, "gray_concrete")
            w.set(97 + k, BRIDGE_Y - 3 - k + 1, z, "gray_concrete")
    # lamp posts every 7 on both rails
    for z in range(81, CAGE["z2"] - 2, 7):
        for x in (93, 99):
            w.set(x, BRIDGE_Y + 3, z, "iron_bars")
            lamp(w, x, BRIDGE_Y + 4, z)
    # (the old tall flood posts here are gone: lamps at the bridge end would hang in front of the face; the face is lit
    # from hidden light blocks, see face_rigs)
    # side spur for the gurney: z GURNEY_Z..GURNEY_Z + 2, from the west wall to the bridge
    gz = GURNEY_Z
    for x in range(CAGE["x1"], 93):
        for z in range(gz, gz + 3):
            w.set(x, BRIDGE_Y, z, "light_gray_concrete" if z == gz + 1 else hazard(x, 0))
        for z in (gz - 1, gz + 3):
            w.set(x, BRIDGE_Y, z, "iron_block")
            w.set(x, BRIDGE_Y + 1, z, "iron_bars")
            w.set(x, BRIDGE_Y + 2, z, "iron_bars")
    for z in range(gz, gz + 3):      # opening in the bridge rail where the spur joins
        w.set(93, BRIDGE_Y + 1, z, AIR)
        w.set(93, BRIDGE_Y + 2, z, AIR)
        w.set(93, BRIDGE_Y + 3, z, AIR)
    box(w, 70, FLOOR_C + 1, gz, 71, BRIDGE_Y - 1, gz + 1, "gray_concrete")
    box(w, 82, FLOOR_C + 1, gz, 83, BRIDGE_Y - 1, gz + 1, "gray_concrete")
    # the door in the south wall, tunnel to the flooded chamber (z 138..142), sealed by a blast door at z 140..141
    carve(w, 94, BRIDGE_Y + 1, CAGE["z2"] + 1, 98, BRIDGE_Y + 5, 142)
    for z in range(CAGE["z2"] + 1, 143):
        for x in range(93, 100):
            w.set(x, BRIDGE_Y, z, "light_gray_concrete" if 94 <= x <= 98 else "iron_block")
        for x in (93, 99):
            for y in range(BRIDGE_Y + 1, BRIDGE_Y + 7):
                w.set(x, y, z, WALLP)
        for x in range(94, 99):
            w.set(x, BRIDGE_Y + 6, z, WALLP)
    # blast door (closed): two leaves of iron with hazard seam, centred at the middle of the tunnel
    for x in range(94, 99):
        for y in range(BRIDGE_Y + 1, BRIDGE_Y + 6):
            for z in (140, 141):
                b = IRON
                if x == 96:
                    b = hazard(y, 0)
                elif y in (BRIDGE_Y + 1, BRIDGE_Y + 5):
                    b = "gray_concrete"
                w.set(x, y, z, b)
    DOORS["cage_door"] = dict(box=(94, BRIDGE_Y + 1, 140, 98, BRIDGE_Y + 5, 141), closed=IRON)
    pass
    pass


def build_catwalks(w):
    c = CAGE
    X1, X2, Z1, Z2 = c["x1"], c["x2"], c["z1"], c["z2"]
    levels = [62, 76, 90]
    for y in levels:
        for sgn in (-1, 1):
            xs = (X1, X1 + 1, X1 + 2) if sgn < 0 else (X2 - 2, X2 - 1, X2)
            edge = X1 + 2 if sgn < 0 else X2 - 2
            for z in range(Z1 + 6, Z2 - 4):
                if y == 64 and 36 <= z <= 46 and False:
                    continue
                for x in xs:
                    w.set(x, y, z, "polished_blackstone" if x != edge else hazard(z, 0))
                for k in (1, 2):
                    w.set(edge, y + k, z, "iron_bars")
            # lamps and posts
            for z in range(Z1 + 8, Z2 - 4, 12):
                w.set(edge, y + 1, z, "gray_concrete")
                w.set(edge, y + 2, z, "gray_concrete")
                lamp(w, edge, y + 3, z)
            # supports down the wall
            for z in range(Z1 + 6, Z2 - 4, 18):
                for x in xs:
                    box(w, x, y - 3, z, x, y - 1, z, "gray_concrete")
        # end connectors along the north wall
        for x in range(X1 + 3, X2 - 2):
            w.set(x, y, Z1 + 3, "polished_blackstone")
            for k in (1, 2):
                if x % 2 == 0 or True:
                    w.set(x, y + k, Z1 + 4, "iron_bars")
        # connect
    # ladders at the north ends
    for sgn in (-1, 1):
        lx = X1 + 1 if sgn < 0 else X2 - 1
        for y in range(40, 91):
            if w.get(lx, y, Z1 + 3) in (None, "minecraft:air"):       # a ladder needs a block behind it
                w.set(lx, y, Z1 + 3, "polished_blackstone")
            w.set(lx, y, Z1 + 4, bs("ladder", facing="south"))
        # gap in the catwalk deck for the ladder is handled by leaving the first rows free
    # high cross-walk over the bridge end at y 98 would block the booth line of sight, so none


def build_roof(w):
    c = CAGE
    X1, X2, Z1, Z2 = c["x1"], c["x2"], c["z1"], c["z2"]
    # ceiling truss grid
    for z in range(Z1, Z2 + 1, 12):
        box(w, X1, 110, z, X2, 111, z, "gray_concrete")
    for x in range(X1, X2 + 1, 16):
        box(w, x, 110, Z1, x, 111, Z2, "gray_concrete")
    # ceiling light rigs: 3 x 3 panels in the truss squares (off by default)
    for x in (76, 96, 116):
        for z in range(32, 136, 14):
            for dx in (-1, 0, 1):
                for dz in (-1, 0, 1):
                    lamp(w, x + dx, 109, z + dz)
            box(w, x - 2, 109, z - 2, x + 2, 109, z - 2, BLACK)
            box(w, x - 2, 109, z + 2, x + 2, 109, z + 2, BLACK)
            box(w, x - 2, 109, z - 1, x - 2, 109, z + 1, BLACK)
            box(w, x + 2, 109, z - 1, x + 2, 109, z + 1, BLACK)
    # hanging rigs on chains, lower in the room (these actually reach the bridge and the head): a black rim and a top plate round the
    # 2 x 2 lamps, so that the lamps face down and show from below (they used to sit on a black plate that hid them)
    for z in range(72, 134, 12):
        for x in (88, 104):
            for y in range(87, 109):
                w.set(x, y, z, bs("iron_chain", axis="y"))
            box(w, x - 2, 86, z - 1, x + 2, 86, z + 2, BLACK)
            box(w, x - 2, 85, z - 1, x + 2, 85, z + 2, BLACK)
            for dx in (0, 1):
                for dz in (0, 1):
                    lamp(w, x + dx - (1 if x < CX else 0), 85, z + dz)
    for z in (40, 52):                         # rigs over the giant's shoulders (the east ones clear of the booth)
        for x in (82, 103):
            for y in range(77, 109):
                w.set(x, y, z, bs("iron_chain", axis="y"))
            box(w, x - 1, 76, z - 1, x + 2, 76, z + 2, BLACK)
            box(w, x - 1, 75, z - 1, x + 2, 75, z + 2, BLACK)
            for dx in (0, 1):
                for dz in (0, 1):
                    lamp(w, x + dx, 75, z + dz)
    # overhead cranes: wall rails, bridge girders, trolleys, chains and hooks
    for z in (60, 100):
        box(w, X1, 103, z, X2, 106, z + 2, "gray_concrete")
        for x in range(X1, X2 + 1):
            w.set(x, 107, z, hazard(x, 0))
            w.set(x, 107, z + 2, hazard(x, 0))
        tx = 84 if z == 60 else 80          # (the hook over the east shoulder would stand in the line from the bridge to the booth)
        box(w, tx - 2, 100, z - 1, tx + 2, 102, z + 3, "iron_block")
        for y in range(80 if z == 100 else 86, 100):
            w.set(tx, y, z + 1, bs("iron_chain", axis="y"))
        box(w, tx - 1, 78 if z == 100 else 84, z, tx + 1, 79 if z == 100 else 85, z + 2, "gray_concrete")
        w.set(tx, 77 if z == 100 else 83, z + 1, bs("iron_chain", axis="y"))
    for z in (60, 100):
        for sgn in (-1, 1):
            xx = X1 if sgn < 0 else X2
            box(w, xx, 103, z - 1, xx, 108, z + 3, "iron_block")
    # cable bundles on the side walls and sagging chains between the girders
    rng = random.Random(RNG_SEED)
    for zc in (30, 48, 70, 92, 118):
        for xx in (X1, X2 - 1):
            for y in range(SURF + 3, 108):
                col = "black_concrete" if (y // 5) % 2 == 0 else "gray_concrete"
                box(w, xx, y, zc, xx + 1, y, zc + 1, col)
                if y % 11 == 5:
                    box(w, xx, y, zc, xx + 1, y, zc + 1, ORANGE)
    for z in (36, 84, 124):
        for x in range(X1 + 3, X2 - 2):
            sag = int(3 * (1 - ((x - CX) / 30.0) ** 2)) if abs(x - CX) <= 30 else 0
            w.set(x, 104 - sag, z, bs("iron_chain", axis="x"))
    # debris racks: three hanging pipe bundles over the bridge, each in a cradle just under the roof
    for dz in (66 + ZS, 71 + ZS, 77 + ZS):
        box(w, 94, 107, dz - 1, 98, 109, dz + 1, "gray_concrete")
        for x in range(94, 99):
            w.set(x, 106, dz, "copper_block" if x % 2 else "gray_concrete")
        box(w, 94, 110, dz - 1, 98, 110, dz + 1, hazard(dz, 0))
        box(w, 94, 105, dz - 1, 98, 105, dz - 1, "iron_bars")
        box(w, 94, 105, dz + 1, 98, 105, dz + 1, "iron_bars")


# The commander's booth: an OPEN command balcony hanging beside the giant's right cheek (east of the head), its floor level with
# the east wall catwalk (y 62) and joined to it by a short gangway.  No glass anywhere: a dark cantilevered platform, a solid
# one-block parapet along the front (it hides his legs from the stop below: the stop looks up at him at 23 to 27 degrees, so a
# one-block parapet hides everything under about 1.8 blocks of a figure standing 1.25 behind it), a dark back wall with a few dim
# amber instrument lights, side walls and a roof plate, and eight blocks of headroom for a figure shown at scale 2.0 (3.6 blocks).
# He is lit by hidden light blocks above and in front of him (BOOTH_LIGHTS), so with the booth lit he is a bright figure against
# darkness and with it off the balcony is a dark shape.  From the stop (13.5 from the face plane) he is 23 blocks away, 23 to 27
# degrees up and 28 degrees to the right of straight ahead: face and booth are in one view.
BOOTH = dict(x1=105, x2=114, z1=49, z2=54, y0=62)
BOOTH_STAND = (107.0, 53.75)      # where the commander stands (x, z), feet on the floor row Y0 + 1, 1.25 behind the parapet's front face (z 55)
BOOTH_H = 8                       # clear height under the roof plate (rows Y0 + 1 .. Y0 + 8)
BOOTH_SCALE = 2.0                 # the story shows him at twice human size: 3.6 blocks tall, 1.8 wide with the arms
INSTRUMENTS = ((107, 66), (108, 67), (110, 66), (111, 67), (112, 66), (113, 65), (109, 65))   # (x, y) of the dim amber instrument lights


def build_booth(w):
    X1b, X2b, Zb1, Zb2, Y0 = BOOTH["x1"], BOOTH["x2"], BOOTH["z1"], BOOTH["z2"], BOOTH["y0"]
    H = BOOTH_H
    roof = Y0 + H + 1
    DARK, MID = "polished_blackstone", "gray_concrete"
    # floor plate, a hazard lip on its front edge, cross beams and chains hanging it from the roof truss
    box(w, X1b, Y0, Zb1, X2b, Y0, Zb2, DARK)
    for x in range(X1b, X2b + 1):
        w.set(x, Y0, Zb2, MID if x % 2 else "black_concrete")
    for x in range(X1b, X2b + 1, 3):
        box(w, x, Y0 - 1, Zb1, x, Y0 - 1, Zb2, MID)
    box(w, X1b, Y0 - 1, Zb2, X2b, Y0 - 1, Zb2, MID)
    # the parapet (front), side walls and the back wall, two thick so that the instrument pockets have a back
    box(w, X1b, Y0 + 1, Zb2, X2b, Y0 + 1, Zb2, MID)
    box(w, X1b, Y0 + 1, Zb1, X1b, Y0 + H, Zb2 - 2, DARK)                     # west wall (towards the head: keeps its floodlight off the balcony); stops 2 short of
    box(w, X1b, Y0 + 1, Zb2 - 1, X1b, Y0 + 1, Zb2, MID)                      # the front, so that the stop sees his left shoulder over the parapet
    box(w, X2b, Y0 + 1, Zb1, X2b, Y0 + H, Zb2, DARK)                         # east wall
    box(w, X1b, Y0 + 1, Zb1, X2b, Y0 + H, Zb1 + 1, DARK)                     # back wall z 49..50
    box(w, X1b, Y0 + H + 1, Zb1, X2b, Y0 + H + 1, Zb2, MID)                  # roof plate
    for x in range(X1b, X2b + 1):                                            # its front lip: a dark hazard band
        w.set(x, Y0 + H + 1, Zb2, MID if (x // 2) % 2 else "black_concrete")
    # a low console along the back wall (the instruments stand above it)
    box(w, X1b + 2, Y0 + 1, Zb1 + 2, X2b - 2, Y0 + 2, Zb1 + 3, MID)
    box(w, X1b + 2, Y0 + 3, Zb1 + 2, X2b - 2, Y0 + 3, Zb1 + 3, "black_concrete")
    # amber instrument lights: a pocket in the back wall holds a hidden light block, a glass pane (dark until lit) stands in front of it
    for (x, y) in INSTRUMENTS:
        w.set(x, y, Zb1 + 1, AIR)
        w.set(x, y, Zb1 + 2, "black_stained_glass")
        BOOTH_LIGHTS.append((x, y, Zb1 + 1, bs("light", level=8)))
        BOOTH_LIGHTS.append((x, y, Zb1 + 2, "orange_stained_glass"))
    # the key light on him: hidden light blocks above and in front of the standing place (the figure stands at BOOTH_STAND, feet y0 + 1,
    # 3.6 tall: up to y0 + 4.6), the strongest above-front, a softer fill from the side and low
    sx = int(BOOTH_STAND[0])
    for (x, y, z, lvl) in ((sx, Y0 + 7, Zb2 + 1, 15), (sx - 1, Y0 + 6, Zb2 + 1, 15), (sx + 1, Y0 + 6, Zb2 + 1, 15), (sx, Y0 + 4, Zb2, 15), (sx, Y0 + 3, Zb2, 15), (sx + 1, Y0 + 5, Zb2, 15),
                           (sx + 2, Y0 + 7, Zb2, 14), (sx - 1, Y0 + 7, Zb2 - 2, 14), (sx + 1, Y0 + 7, Zb2 - 2, 14), (sx, Y0 + 8, Zb2 - 3, 13),
                           (sx + 2, Y0 + 3, Zb2 - 1, 12), (sx - 1, Y0 + 3, Zb2 - 1, 12)):
        BOOTH_LIGHTS.append((x, y, z, bs("light", level=lvl)))
    for l in BOOTH_LIGHTS:
        CAGE_LIGHTS.append(l)
    # door in the east wall onto a short gangway to the catwalk at x 126..128 (its rail has a gap there)
    carve(w, X2b, Y0 + 1, 51, X2b, Y0 + 3, 53)
    for x in range(X2b + 1, 126):
        for z in (51, 52, 53):
            w.set(x, Y0, z, "gray_concrete" if z == 52 else hazard(x, 0))
        for z in (50, 54):
            w.set(x, Y0, z, "iron_block")
            w.set(x, Y0 + 1, z, "iron_bars")
            w.set(x, Y0 + 2, z, "iron_bars")
    for z in (51, 52, 53):
        for y in (Y0 + 1, Y0 + 2):
            w.set(126, y, z, AIR)
    # hangers: chains from the roof truss to the roof plate's corners, and two braces under the gangway down into the east wall
    for (x, z) in ((X1b, Zb1), (X2b, Zb1), (X1b, Zb2), (X2b, Zb2)):
        for y in range(Y0 + H + 2, 109):
            w.set(x, y, z, bs("iron_chain", axis="y"))
    for z in (50, 54):
        for x in range(X2b + 1, 129):
            w.set(x, Y0 - 1 - int(round(5.0 * (x - X2b - 1) / (128 - X2b - 1))), z, MID)
    ddx, ddz = BOOTH_STAND[0] - 96.5, FACE_Z - BOOTH_STAND[1]                     # he faces the stop on the bridge and looks down at it
    yaw = math.degrees(math.atan2(ddx, ddz))
    pitch = math.degrees(math.atan2(Y0 + 1 + 1.62 * BOOTH_SCALE - (BRIDGE_Y + 1 + 1.62), math.hypot(ddx, ddz)))
    w.anchor("booth", BOOTH_STAND[0], Y0 + 1, BOOTH_STAND[1], yaw=round(yaw, 1), pitch=round(pitch, 1))


def build_gurney_door(w):
    X1 = CAGE["x1"]
    # passage through the 4 thick wall, and a small hospital vestibule behind it
    gz = GURNEY_Z
    carve(w, X1 - 4, BRIDGE_Y + 1, gz, X1 - 1, BRIDGE_Y + 4, gz + 2)
    hollow(w, X1 - 12, BRIDGE_Y + 1, gz - 6, X1 - 5, BRIDGE_Y + 5, gz + 8, "gray_concrete")
    carve(w, X1 - 5, BRIDGE_Y + 1, gz, X1 - 4, BRIDGE_Y + 4, gz + 2)
    for z in range(gz - 6, gz + 9):
        for x in range(X1 - 12, X1 - 4):
            w.set(x, BRIDGE_Y, z, "light_gray_concrete")
    for z in (gz, gz + 1, gz + 2):
        w.set(X1 - 1, BRIDGE_Y + 5, z, IRON)
    for y in range(BRIDGE_Y + 1, BRIDGE_Y + 5):
        for z in (gz - 1, gz + 3):
            w.set(X1 - 1, y, z, IRON)
    # a hospital sign: white cross on red
    box(w, X1 - 12, BRIDGE_Y + 2, gz, X1 - 12, BRIDGE_Y + 4, gz + 2, "red_concrete")
    box(w, X1 - 12, BRIDGE_Y + 3, gz, X1 - 12, BRIDGE_Y + 3, gz + 2, WHITE)
    box(w, X1 - 12, BRIDGE_Y + 2, gz + 1, X1 - 12, BRIDGE_Y + 4, gz + 1, WHITE)
    w.set(X1 - 8, BRIDGE_Y + 4, gz + 1, LAMP_OFF)
    CAGE_LIGHTS.append((X1 - 8, BRIDGE_Y + 4, gz + 1, LAMP_ON))
    for (x, z) in ((X1 - 10, gz - 3), (X1 - 10, gz + 5), (X1 - 7, gz + 1)):       # the vestibule is never dark
        hlight(w, x, BRIDGE_Y + 3, z, 12)


def cage_anchors(w):
    w.anchor("bridge_start", 96.5, BRIDGE_Y + 1, CAGE["z2"] - 1.5, yaw=YAW["north"])
    # the stop is STOP_DIST (13.5) blocks from the face plane; a little up-pitch centres the head in the view
    w.anchor("face", 96.5, BRIDGE_Y + 1, FACE_Z, yaw=YAW["north"], pitch=-10.0)
    w.anchor("captain_mark", 94.5, BRIDGE_Y + 1, FACE_Z + 4.0, yaw=YAW["north"])
    w.anchor("scientist_mark", 98.5, BRIDGE_Y + 1, FACE_Z + 4.0, yaw=YAW["north"])
    w.anchor("gurney_in", 62.5, BRIDGE_Y + 1, GURNEY_Z + 1.5, yaw=YAW["east"])
    w.anchor("gurney_mark", 96.5, BRIDGE_Y + 1, GURNEY_Z + 1.5, yaw=YAW["east"])
    w.anchor("shield", 96.5, BRIDGE_Y + 1, SHIELD_Z + 0.5, yaw=YAW["north"])
    for i, z in enumerate((66.5 + ZS, 71.5 + ZS, 77.5 + ZS)):
        w.anchor("debris_%d" % (i + 1), 96.5, 105.0, z)


# ================================================================================================ B: THE FLOODED CHAMBER
B = dict(x1=9, x2=150, z1=143, z2=186, y1=33, y2=79)
LAKE_Y = 50


def build_flood(w):
    b = B
    X1, X2, Z1, Z2, Y1, Y2 = b["x1"], b["x2"], b["z1"], b["z2"], b["y1"], b["y2"]
    box(w, X1 - 1, Y1 - 3, Z1 - 1, X2 + 1, Y2 + 4, Z2 + 1, WALLM)
    carve(w, X1, Y1, Z1, X2, Y2, Z2)
    box(w, X1, Y1 - 1, Z1, X2, Y1 - 1, Z2, "gray_concrete")
    # walls: plating with ribs and hazard bands
    for y in range(Y1, Y2 + 1):
        for x in range(X1, X2 + 1):
            for plane, inner in ((Z2 + 1, Z2), (Z1 - 1, Z1)):
                if plane == Z1 - 1 and 93 <= x <= 99 and y >= BRIDGE_Y:
                    continue
                panel = (x % 12 == 0) or (y % 14 == 0)
                bb = WALLP if panel else WALLM
                if y in (LAKE_Y + 1, LAKE_Y + 2):
                    bb = hazard(x, y)
                w.set(x, y, plane, bb)
                if x % 16 == 8 and y > LAKE_Y:
                    w.set(x, y, inner, "gray_concrete")
        for z in range(Z1, Z2 + 1):
            for plane in (X1 - 1, X2 + 1):
                panel = (z % 12 == 0) or (y % 14 == 0)
                bb = WALLP if panel else WALLM
                if y in (LAKE_Y + 1, LAKE_Y + 2):
                    bb = hazard(z, y)
                w.set(plane, y, z, bb)
    # the lake: magma bed under tinted glass
    box(w, X1, Y1, Z1, X2, Y1, Z2, LIQUID_BED)
    box(w, X1, Y1 + 1, Z1, X2, LAKE_Y, Z2, LIQUID)
    # dock platform (west), level with the catwalk
    box(w, X1, Y1 + 1, 154, 22, BRIDGE_Y - 1, 166, "gray_concrete")
    for x in range(X1, 23):
        for z in range(154, 167):
            edge = x == 22 or z in (154, 166)
            w.set(x, BRIDGE_Y, z, hazard(x + z, 0) if edge else "light_gray_concrete")
    for z in range(154, 167):
        for y in (BRIDGE_Y + 1, BRIDGE_Y + 2):
            pass
    for x in range(X1 + 2, 22):
        for z in (154, 166):
            w.set(x, BRIDGE_Y + 1, z, "iron_bars")
            w.set(x, BRIDGE_Y + 2, z, "iron_bars")
    # a raft moored at the dock (decor)
    box(w, 14, LAKE_Y + 1, 168, 20, LAKE_Y + 1, 171, "dark_oak_planks")
    box(w, 14, LAKE_Y + 1, 168, 14, LAKE_Y + 3, 168, "dark_oak_fence")
    box(w, 20, LAKE_Y + 1, 171, 20, LAKE_Y + 3, 171, "dark_oak_fence")
    # catwalk: east along z 159..161 to x 97, then north along x 95..97 to the cage door at z 143
    def deck(x, z):
        w.set(x, BRIDGE_Y, z, "gray_concrete")
    for x in range(23, 98):
        for z in (159, 160, 161):
            w.set(x, BRIDGE_Y, z, hazard(x, 0) if z != 160 else ("light_gray_concrete" if x % 4 > 1 else YELLOW))
        for z in (158, 162):
            w.set(x, BRIDGE_Y, z, "iron_block")
            w.set(x, BRIDGE_Y + 1, z, "iron_bars")
            w.set(x, BRIDGE_Y + 2, z, "iron_bars")
    for z in range(143, 159):
        for x in (95, 96, 97):
            w.set(x, BRIDGE_Y, z, hazard(z, 0) if x != 96 else ("light_gray_concrete" if z % 4 > 1 else YELLOW))
        for x in (94, 98):
            w.set(x, BRIDGE_Y, z, "iron_block")
            w.set(x, BRIDGE_Y + 1, z, "iron_bars")
            w.set(x, BRIDGE_Y + 2, z, "iron_bars")
    for x in (94, 98):          # close the corner rails
        w.set(x, BRIDGE_Y + 1, 162, "iron_bars")
    for x in range(98, 99):
        for z in (158, 162):
            w.set(x, BRIDGE_Y, z, "iron_block")
    w.set(98, BRIDGE_Y + 1, 159, "iron_bars"); w.set(98, BRIDGE_Y + 2, 159, "iron_bars")
    w.set(98, BRIDGE_Y + 1, 160, "iron_bars"); w.set(98, BRIDGE_Y + 2, 160, "iron_bars")
    w.set(98, BRIDGE_Y + 1, 161, "iron_bars"); w.set(98, BRIDGE_Y + 2, 161, "iron_bars")
    for x in range(94, 98):         # open the rail along z=158 where the north arm leaves
        pass
    # fix the corner: the north arm leaves the east-west catwalk at x 95..97, z 158 -> clear those rail cells
    for x in (95, 96, 97):
        w.set(x, BRIDGE_Y, 158, "light_gray_concrete")
        w.set(x, BRIDGE_Y + 1, 158, AIR)
        w.set(x, BRIDGE_Y + 2, 158, AIR)
    for x in (94, 98):
        w.set(x, BRIDGE_Y, 158, "iron_block")
        w.set(x, BRIDGE_Y + 1, 158, "iron_bars")
        w.set(x, BRIDGE_Y + 2, 158, "iron_bars")
    # supports into the lake, every 12 blocks, with red emergency lamps on the rail posts
    for x in range(26, 97, 12):
        box(w, x, Y1 + 1, 158, x + 1, BRIDGE_Y - 1, 159, "gray_concrete")
        box(w, x, Y1 + 1, 161, x + 1, BRIDGE_Y - 1, 162, "gray_concrete")
        for z in (158, 162):
            w.set(x, BRIDGE_Y + 3, z, "gray_concrete")
        emergency_lamp(w, x, BRIDGE_Y + 4, 158, (x, BRIDGE_Y + 5, 158))
    for z in range(146, 158, 6):
        box(w, 94, Y1 + 1, z, 94, BRIDGE_Y - 1, z, "gray_concrete")
        box(w, 98, Y1 + 1, z, 98, BRIDGE_Y - 1, z, "gray_concrete")
    # a sealed door at the end: the blast door was built with the cage tunnel; frame it on this side
    for x in range(92, 101):
        for y in range(BRIDGE_Y, BRIDGE_Y + 8):
            if 94 <= x <= 98 and BRIDGE_Y < y <= BRIDGE_Y + 5:
                continue
            w.set(x, y, Z1, hazard(x, y) if (x in (92, 100) or y == BRIDGE_Y + 7 or x in (93, 99)) else WALLP)
    # great pillars from lake to roof with hazard bands, ring lights dead
    for x in (36, 62, 124, 138):
        for z in (150, 180):
            box(w, x, Y1 + 1, z, x + 2, Y2 + 4, z + 2, "gray_concrete")
            for y in range(LAKE_Y + 2, Y2, 9):
                for xx in range(x, x + 3):
                    for zz in range(z, z + 3):
                        if xx in (x, x + 2) or zz in (z, z + 2):
                            w.set(xx, y, zz, hazard(xx + zz, y))
            for y in range(LAKE_Y + 10, Y2, 14):
                lamp(w, x + 1, y, z - 1)
                lamp(w, x + 1, y, z + 3)
    # overhead pipework along the roof
    for z in (152, 166, 180):
        box(w, X1, Y2 - 3, z, X2, Y2 - 2, z + 1, "weathered_copper")
        for x in range(X1, X2, 10):
            box(w, x, Y2 - 4, z, x, Y2 - 1, z + 1, IRON)
    for x in range(X1 + 6, X2, 18):
        for y in range(Y2 - 12, Y2 - 3):
            w.set(x, y, 150, bs("iron_chain", axis="y"))
            w.set(x, y, 176, bs("iron_chain", axis="y"))
        lamp(w, x, Y2 - 13, 150)
        lamp(w, x, Y2 - 13, 176)
    # dim red emergency lamps on the long walls
    for x in range(20, 140, 24):
        emergency_lamp(w, x, 63, Z2 + 1, (x, 63, Z2))
    for x in (36, 62, 124, 138):
        for z in (150, 180):
            emergency_lamp(w, x + 1, 58, z - 1, (x + 1, 59, z - 1))
    flood_lights(w)
    w.anchor("dock", 15.5, BRIDGE_Y + 1, 160.5, yaw=YAW["east"])
    w.anchor("crossing", 60.5, BRIDGE_Y + 1, 160.5, yaw=YAW["east"])
    w.anchor("cage_door", 96.5, BRIDGE_Y + 1, 145.0, yaw=YAW["north"])


# ================================================================================================ A: THE CORRIDORS
UY = 130                 # upper level floor block row (feet 131)
LY = 106                 # lower level floor block row (feet 107)
ZA = 160                 # centre line of the route
WALL_A = "white_concrete"                # clean pale walls: at light level 12+ the game's block light is neutral white, so the cool
DADO_A = "light_gray_concrete"           # comes from the blue band and the blue plates, not from the lighting
BAND_A = "light_blue_concrete"
RIB_A = "light_gray_concrete"
FLOOR_A = "light_gray_concrete"
CEIL_A = "white_concrete"
STRIP_A = "sea_lantern"
ROOMS_A = []             # (x1, y1, z1, x2, y2, z2)
# "loop_door": 6.5 blocks from the orange door, in the east end of the ring's north leg, facing it (it was 1.5 blocks away: a flat
# orange wall filled the view)
LOOP_DOOR_AT = (109.5, 154.5, round(math.degrees(math.atan2(109.5 - 103.5, 157.0 - 154.5)), 1))


def room(x1, y1, z1, x2, y2, z2):
    ROOMS_A.append((x1, y1, z1, x2, y2, z2))


def plate(w, text, plane, u0, v0, axis, step, bg="light_blue_concrete", fg=WHITE, pad=1):
    """A wall sign: a coloured plate with block letters, set flush in the wall plane."""
    wd = 4 * len(text) - 1
    for i in range(-pad, wd + pad):
        for j in range(-pad, 5 + pad):
            u = u0 + step * i
            if axis == "x":
                w.set(plane, v0 + j, u, bg)
            else:
                w.set(u, v0 + j, plane, bg)
    stencil(w, text, plane, u0, v0, axis, step, 1, fg)


def decorate_room(w, r):
    """Pale metal wall plating, dado, ribs, floor and ceiling for one carved box (only touches plain wall cells)."""
    x1, y1, z1, x2, y2, z2 = r
    H = y2 - y1 + 1
    base = w._id(WALL_A)
    fl = w._id(WALL_A)

    def paint(plane_cells):
        pass

    def wallcell(x, y, z, u):
        if w.a[x, y, z] != base:
            return
        dy = y - y1
        if dy <= 1:
            b = DADO_A
        elif dy == 2:
            b = IRON if u % 3 else DADO_A
        elif dy >= H - 2:
            b = BAND_A
        else:
            b = WALL_A
        if u % 8 == 0 and dy < H - 2:
            b = RIB_A if dy > 1 else IRON
        elif u % 8 == 1 and dy > 2 and dy < H - 1:
            b = WALL_A
        w.set(x, y, z, b)

    for y in range(y1, y2 + 1):
        for x in range(x1, x2 + 1):
            wallcell(x, y, z1 - 1, x)
            wallcell(x, y, z2 + 1, x)
        for z in range(z1, z2 + 1):
            wallcell(x1 - 1, y, z, z)
            wallcell(x2 + 1, y, z, z)
    # floor and ceiling
    for x in range(x1, x2 + 1):
        for z in range(z1, z2 + 1):
            if w.a[x, y1 - 1, z] == base:
                w.set(x, y1 - 1, z, FLOOR_A if (x + z) % 7 else "polished_andesite")
            if w.a[x, y2 + 1, z] == base:
                w.set(x, y2 + 1, z, CEIL_A)


def ceiling_strips(w, r, every=4, along="x", rows=None):
    x1, y1, z1, x2, y2, z2 = r
    if along == "x":
        zs = rows if rows else [(z1 + z2) // 2]
        for z in zs:
            for x in range(x1 + 1, x2, every):
                for k in (0, 1):
                    if w.get(x + k, y2 + 1, z) in ("minecraft:" + WALL_A, "minecraft:" + CEIL_A):
                        w.set(x + k, y2 + 1, z, STRIP_A)
    else:
        xs = rows if rows else [(x1 + x2) // 2]
        for x in xs:
            for z in range(z1 + 1, z2, every):
                for k in (0, 1):
                    if w.get(x, y2 + 1, z + k) in ("minecraft:" + WALL_A, "minecraft:" + CEIL_A):
                        w.set(x, y2 + 1, z + k, STRIP_A)


def floor_line(w, y, x1, x2, z, block, axis="x"):
    for i in range(x1, x2 + 1):
        if axis == "x":
            w.set(i, y, z, block)
        else:
            w.set(z, y, i, block)


def bulkhead_door(w, x, z, side, number, y0=131):
    """A numbered bulkhead door in the north (side=-1) or south (side=+1) wall of an east-west corridor; x is its west cell."""
    pz = z
    for dx in (0, 1):
        for dy in range(3):
            w.set(x + dx, y0 + dy, pz, bs("iron_door", facing="south" if side < 0 else "north", half="lower" if dy == 0 else "upper",
                                          hinge="left" if dx == 0 else "right", open="false", powered="false") if dy < 2 else IRON)
    for dx in (-1, 2):
        for dy in range(4):
            w.set(x + dx, y0 + dy, pz, IRON)
    for dx in range(-1, 3):
        w.set(x + dx, y0 + 3, pz, IRON if dx in (-1, 2) else "gray_concrete")
    # number plate beside the door
    pass
    stencil(w, number[-2:], pz, x + (4 if side < 0 else -4), y0 + 1, "z", 1 if side < 0 else -1, 1, BLACK, solid_only=True)


def build_corridors(w):
    ROOMS_A.clear()
    room(170, 131, 151, 183, 139, 169)       # lobby
    room(152, 131, 158, 169, 136, 162)       # C1
    room(122, 131, 153, 151, 138, 167)       # moving walkway hall
    room(110, 131, 158, 121, 136, 162)       # C2
    room(95, 131, 152, 111, 136, 168)        # the loop ring
    room(101, 131, 169, 105, 136, 176)       # dead end
    room(90, 131, 158, 94, 136, 162)         # connector to the escalator hall
    room(22, 100, 150, 89, 149, 170)         # escalator hall (tall void)
    room(15, 107, 158, 21, 112, 162)         # lower corridor
    room(8, 107, 154, 14, 113, 166)          # elevator lobby
    # shells first, then all carves, so crossings stay open
    for (x1, y1, z1, x2, y2, z2) in ROOMS_A:
        box(w, x1 - 1, y1 - 1, z1 - 1, x2 + 1, y2 + 1, z2 + 1, WALL_A)
    for (x1, y1, z1, x2, y2, z2) in ROOMS_A:
        carve(w, x1, y1, z1, x2, y2, z2)
    # the ring's core is solid
    box(w, 100, 131, 157, 106, 136, 163, WALL_A)
    box(w, 100, 130, 157, 106, 137, 163, WALL_A)
    for r in ROOMS_A:
        decorate_room(w, r)
    # ------------- lobby ------------------------------------------------------------------------
    lob = (170, 131, 151, 183, 139, 169)
    # the big door (east wall, x 184..185): a closed vault door with hazard frame
    for z in range(154, 167):
        for y in range(131, 139):
            for x in (184, 185):
                b = IRON
                if z in (154, 166) or y == 138:
                    b = hazard(z, y)
                elif z == ZA:
                    b = "gray_concrete"
                elif y in (134, 135) and z % 3 == 0:
                    b = "gray_concrete"
                w.set(x, y, z, b)
    for y in range(133, 137):
        for x in (183,):
            pass
    pass
    pass
    # reception desk and benches
    for (za, zb) in ((154, 158), (162, 166)):                # two reception desks: white body, a lit blue front, quartz top
        box(w, 175, 131, za, 176, 132, zb, "white_concrete")
        box(w, 175, 131, za, 175, 131, zb, "light_gray_concrete")
        for z in range(za, zb + 1):
            w.set(175, 132, z, "sea_lantern" if z % 2 == 0 else "light_blue_concrete")
        box(w, 175, 133, za, 176, 133, zb, "smooth_quartz")
        box(w, 177, 131, za, 177, 131, zb, "light_gray_concrete")                    # kick step
        for z in (za + 1, zb - 1):
            w.set(176, 134, z, "gray_concrete")
            w.set(176, 135, z, "cyan_concrete")
    for z in range(152, 169, 2):
        w.set(171, 131, z, "smooth_quartz") if z not in (158, 159, 160, 161, 162) else None
    # big wall sign and a map plate
    pass
    pass
    plate(w, "A-12", 170 - 1, 163, 135, "x", -1, bg="light_blue_concrete", fg=WHITE)
    # floor guide stripes through the lobby and everywhere on the route
    for x in range(152, 183):
        w.set(x, UY, ZA - 1, YELLOW)
        w.set(x, UY, ZA + 1, "light_blue_concrete")
    for z in (151, 169):
        pass
    # --------- ceiling strips -------------------------------------------------------------------
    for r in ROOMS_A:
        x1, y1, z1, x2, y2, z2 = r
        if r[0] == 22 and r[1] == 100:
            continue
        if x2 - x1 >= z2 - z1 and (z2 - z1) < 8:
            ceiling_strips(w, r, 3, "x", [(z1 + z2) // 2])
        elif r[0] in (170, 122):
            ceiling_strips(w, r, 3, "x", [z1 + 3, (z1 + z2) // 2, z2 - 3])
        else:
            ceiling_strips(w, r, 3, "x", [(z1 + z2) // 2])
    # ring: strips in each leg
    for x in range(96, 111, 4):
        for z in (154, 166):
            w.set(x, 137, z, STRIP_A)
            w.set(x + 1, 137, z, STRIP_A)
    for z in range(153, 168, 4):
        for x in (97, 109):
            w.set(x, 137, z, STRIP_A)
            w.set(x, 137, z + 1, STRIP_A)
    # ------------- C1: doors, signs --------------------------------------------------------------
    nums = iter(["101", "102", "103", "104", "105", "106", "107", "108", "109", "110", "111", "112", "113", "114", "115", "116", "117", "118", "119", "120"])
    for x in (154, 160, 164):
        bulkhead_door(w, x, 157, -1, next(nums))
    for x in (156, 162):
        bulkhead_door(w, x, 163, 1, next(nums))
    pass
    # ------------- moving walkway hall -----------------------------------------------------------
    for x in range(122, 152):
        for z in range(157, 164):
            edge = z in (157, 163)
            w.set(x, UY, z, YELLOW if edge else "gray_concrete")
        for z in (156, 164):
            w.set(x, UY, z, "iron_block")
            for k in (1,):
                w.set(x, UY + k, z, "iron_bars")
            w.set(x, UY + 2, z, "cyan_concrete")
    for x0 in range(124, 150, 6):             # chevrons pointing west
        for k in range(4):
            for z in (ZA - k, ZA + k):
                w.set(x0 + k, UY, z, YELLOW)
    for z in (156, 164):                       # leave gaps in the handrail at both ends
        for x in (122, 123, 150, 151):
            for k in (1, 2):
                w.set(x, UY + k, z, AIR)
    for x in range(124, 150, 12):             # pillars
        for z in (154, 166):
            box(w, x, 131, z, x + 1, 137, z, "white_concrete")
    pass
    plate(w, "B-3", 153, 126, 134, "z", 1, bg="light_blue_concrete")
    plate(w, "B-3", 167, 146, 134, "z", -1, bg="light_blue_concrete")
    plate(w, "LIFT", 153, 140, 134, "z", 1, bg="light_blue_concrete")
    # ------------- C2 ----------------------------------------------------------------------------
    bulkhead_door(w, 114, 157, -1, "201")
    bulkhead_door(w, 118, 163, 1, "202")
    # ------------- the loop ring -----------------------------------------------------------------
    # stripes on the ring floor
    for x in range(96, 111):
        w.set(x, UY, 153, YELLOW); w.set(x, UY, 167, YELLOW)
    # the distinctive door D: orange hatch with a black seven, hazard frame, two amber beacons
    for x in range(100, 107):
        for y in range(131, 137):
            w.set(x, y, 157, hazard(x, y))
    for x in range(101, 106):
        for y in range(131, 136):
            w.set(x, y, 157, ORANGE)
    stencil(w, "7", 157, 102, 131, "z", -1, 1, BLACK)       # viewed from the north corridor facing south: reading runs west
    for y in (133, 134):
        w.set(100, y, 157, "shroomlight")
        w.set(106, y, 157, "shroomlight")
    for x in (101, 105):
        w.set(x, 136, 157, "red_concrete")
    # a blue cart and a stack of crates against the north wall, only on the north leg
    box(w, 108, 131, 152, 109, 132, 152, "light_blue_concrete")
    box(w, 97, 131, 152, 97, 133, 152, "brown_concrete")
    # distinctive scuff/paint: a big orange arrow stripe on the floor ahead of the door
    for x in range(98, 109):
        w.set(x, UY, 155, ORANGE) if (x % 2 == 0) else None
    # ring doors and exits
    pass
    pass
    plate(w, "A-12", 151, 96, 134, "z", 1, bg="light_blue_concrete")
    plate(w, "A-12", 169, 110, 134, "z", -1, bg="light_blue_concrete")
    # dead end
    for y in range(131, 136):
        for x in range(101, 106):
            w.set(x, y, 177, hazard(x, y) if (x in (101, 105) or y == 135) else IRON)
    pass
    pass
    # connector doors
    bulkhead_door(w, 91, 157, -1, "401")
    # ------------- escalator hall ----------------------------------------------------------------
    build_escalator_hall(w)
    # ------------- lower corridor and elevator lobby ---------------------------------------------
    for x in range(15, 22):
        w.set(x, LY, ZA - 1, YELLOW)
        w.set(x, LY, ZA + 1, "light_blue_concrete")
    bulkhead_door(w, 17, 157, -1, "501", y0=107)
    bulkhead_door(w, 19, 163, 1, "502", y0=107)
    build_elevator_lobby(w)
    corridor_lights(w)
    hall_lights(w)
    # route anchors
    w.anchor("start", 180.5, UY + 1, ZA + 0.5, yaw=YAW["west"])
    w.anchor("corr_1", 160.5, UY + 1, ZA + 0.5, yaw=YAW["west"])
    w.anchor("corr_2", 136.5, UY + 1, ZA + 0.5, yaw=YAW["west"])
    w.anchor("corr_3", 116.5, UY + 1, ZA + 0.5, yaw=YAW["west"])
    w.anchor("loop_door", LOOP_DOOR_AT[0], UY + 1, LOOP_DOOR_AT[1], yaw=LOOP_DOOR_AT[2])
    w.anchor("corr_4", 97.5, UY + 1, 165.5, yaw=YAW["south"])
    w.anchor("corr_5", 85.5, UY + 1, ZA + 0.5, yaw=YAW["west"])
    w.anchor("corr_6", 26.5, LY + 1, ZA + 0.5, yaw=YAW["west"])


def build_escalator_hall(w):
    X1, X2, Z1, Z2 = 22, 89, 150, 170
    PIT = 100
    # lower landing and upper landing plinths
    box(w, 22, PIT, Z1, 31, LY, Z2, "gray_concrete")
    box(w, 80, PIT, Z1, 89, UY, Z2, "gray_concrete")
    for x in range(22, 32):
        for z in range(Z1, Z2 + 1):
            w.set(x, LY, z, FLOOR_A if (x + z) % 7 else "polished_andesite")
    for x in range(80, 90):
        for z in range(Z1, Z2 + 1):
            w.set(x, UY, z, FLOOR_A if (x + z) % 7 else "polished_andesite")
    for x in range(80, 90):
        w.set(x, UY, ZA - 1, YELLOW)
        w.set(x, UY, ZA + 1, "light_blue_concrete")
    for x in range(22, 32):
        w.set(x, LY, ZA - 1, YELLOW)
        w.set(x, LY, ZA + 1, "light_blue_concrete")
    # hazard edges of the plinths
    for z in range(Z1, Z2 + 1):
        w.set(80, UY, z, hazard(z, 0)) if (z < 157 or z > 163) else None
        w.set(31, LY, z, hazard(z, 0)) if (z < 157 or z > 163) else None
    # the escalator: 1 up per 2 along, 48 long, west from x 79 (feet 131) to x 32 (feet 107)
    rails = []
    for i in range(48):
        x = 79 - i
        s = 131 - 0.5 * (i + 1)
        if i % 2 == 0:
            y = int(s)                         # bottom slab, top at s (x.5)
            top = y + 0.5
            for z in range(ZA - 2, ZA + 3):
                w.set(x, y, z, bs("smooth_stone_slab", type="bottom") if z != ZA else bs("polished_andesite_slab", type="bottom"))
            body_top = y - 1
        else:
            y = int(s) - 1
            top = y + 1
            for z in range(ZA - 2, ZA + 3):
                w.set(x, y, z, "gray_concrete" if z != ZA else "light_gray_concrete")
            body_top = y - 1
        for z in range(ZA - 2, ZA + 3):
            for yy in range(body_top, body_top - 3, -1):
                w.set(x, yy, z, "gray_concrete")
        yc = int(math.ceil(top))
        for zz in (ZA - 3, ZA + 3):
            w.set(x, yc, zz, "iron_bars")
            w.set(x, yc + 1, zz, "iron_bars")
            w.set(x, yc + 2, zz, "cyan_concrete" if x % 4 < 2 else "light_gray_concrete")
            w.set(x, yc - 1, zz, "light_gray_concrete")
            w.set(x, yc - 2, zz, "light_gray_concrete")
    # truss under the run
    for x in range(34, 79, 8):
        s = 131 - 0.5 * (79 - x + 1)
        for z in (ZA - 2, ZA + 2):
            box(w, x, PIT + 1, z, x, int(s) - 4, z, "gray_concrete")
        box(w, x, PIT + 1, ZA - 2, x, PIT + 1, ZA + 2, "gray_concrete")
    # pillars along the hall walls, ring bands, gantries with railings
    for x in range(26, 88, 12):
        for z in (151, 169):
            box(w, x, PIT + 1, z, x + 1, 149, z, "white_concrete")
    for y in (112, 124):
        for x in range(32, 80):
            for z in (151, 152, 168, 169):
                w.set(x, y, z, "polished_blackstone" if z in (151, 169) else hazard(x, 0))
            for z in (153, 167):
                w.set(x, y + 1, z, "iron_bars")
        for z in range(151, 170):
            pass
    # wall lights at several heights (always on)
    for x in range(26, 88, 8):
        for y in (104, 116, 128, 140):
            for z in (150, 170):
                w.set(x, y, z, STRIP_A)
                w.set(x + 1, y, z, STRIP_A)
    for x in range(26, 88, 6):
        for z in (156, 164):
            w.set(x, 149, z, STRIP_A)
            w.set(x + 1, 149, z, STRIP_A)
    # hanging cable bundles and a big stencilled level number on the far wall
    for x in range(36, 80, 10):
        for y in range(135, 149):
            w.set(x, y, 160 + (x % 3) - 1, bs("iron_chain", axis="y"))
    pass
    stencil(w, "B3", 171, 60, 118, "z", -1, 4, BAND_A)
    stencil(w, "B3", 149, 40, 118, "z", 1, 4, BAND_A)


def build_elevator_lobby(w):
    # lobby interior x 8..14, z 154..166, y 107..113; car at x 4..6, shaft x 3..7
    box(w, 2, 105, 157, 7, 111, 163, "gray_concrete")           # shaft shell round the upper car
    carve(w, 4, 107, 159, 6, 109, 161)                          # the car
    box(w, 3, LY, 158, 7, LY, 162, "gray_concrete")
    for x in range(3, 8):                                       # car roof and floor
        for z in range(158, 163):
            w.set(x, 110, z, "gray_concrete")
    # open door on the lobby side: x=7 wall cells z 159..161, y 107..109 open
    carve(w, 7, 107, 159, 7, 109, 161)
    for z in (158, 162):
        for y in range(107, 111):
            w.set(7, y, z, IRON)
    for z in range(159, 162):
        w.set(7, 110, z, IRON)
    # car interior: pale panels, a light strip, buttons
    for y in range(107, 110):
        for z in range(159, 162):
            w.set(3, y, z, "light_gray_concrete")
    for z in (158, 162):
        for x in range(3, 8):
            for y in range(107, 110):
                w.set(x, y, z, "light_gray_concrete")
    w.set(3, 108, 160, "gray_concrete"); w.set(3, 109, 160, "lime_concrete"); w.set(3, 107, 160, "red_concrete")
    for x in (4, 5, 6):
        w.set(x, 110, 160, STRIP_A)
    for x in range(4, 7):
        for z in range(159, 162):
            w.set(x, LY, z, "polished_andesite")
    # the hoistway below: a 5 x 5 shaft from y 58 up to the car floor with guide rails
    carve(w, 3, 58, 158, 7, LY - 1, 162)
    pass
    for y in range(58, LY):
        for (x, z) in ((3, 158), (7, 158), (3, 162), (7, 162)):
            w.set(x, y, z, "iron_block")
        if y % 8 == 0:
            for x in range(3, 8):
                w.set(x, y, 158, STRIP_A) if x in (4, 6) else None
    # hoistway walls (z 157, 163 and x 2, 8) from y 57 to 105
    box(w, 2, 57, 157, 8, LY - 1, 157, "polished_blackstone")
    box(w, 2, 57, 163, 8, LY - 1, 163, "polished_blackstone")
    box(w, 2, 57, 157, 2, LY - 1, 163, "polished_blackstone")
    box(w, 8, 57, 157, 8, LY - 1, 163, "polished_blackstone")
    # the lower stop: car at y 54..56 with a door onto the dock
    box(w, 2, 52, 157, 8, 57, 163, "gray_concrete")
    carve(w, 4, 54, 159, 6, 56, 161)
    carve(w, 7, 54, 159, 8, 56, 161)
    box(w, 3, 53, 158, 7, 53, 162, "gray_concrete")
    for x in range(4, 7):
        for z in range(159, 162):
            w.set(x, 53, z, "polished_andesite")
    for x in (4, 5, 6):
        w.set(x, 57, 160, STRIP_A)
    for z in range(159, 162):
        w.set(3, 54, z, "light_gray_concrete")
    # lobby: seating, sign, floor stripes
    for z in (155, 165):
        box(w, 10, 107, z, 12, 107, z, "gray_concrete")
    plate(w, "LIFT", 153, 9, 110, "z", 1, bg="light_blue_concrete")
    plate(w, "LIFT", 167, 13, 110, "z", -1, bg="light_blue_concrete")
    for z in range(159, 162):
        w.set(8, LY, z, YELLOW)
    for x in range(8, 15):
        w.set(x, LY, ZA - 1, YELLOW)
        w.set(x, LY, ZA + 1, "light_blue_concrete")
    for x in (10, 12):
        for z in (156, 164):
            w.set(x, 114, z, STRIP_A)
    w.anchor("elevator", 9.5, LY + 1, ZA + 0.5, yaw=YAW["east"])
    w.anchor("elevator_in", 5.5, LY + 1, ZA + 0.5, yaw=YAW["east"])


# ================================================================================================ D: THE PLUG AND THE SHAFT
PLUG = dict(cx=30, floor=9, z1=6, z2=14)          # interior x 27..33 (3 wide at floor and ceiling, 5 at the belly), y 10..14, z 6..14
SHAFT = dict(x1=2, x2=15, z1=2, z2=15, floor=3, top=156)


def build_plug(w):
    cx, fy, z1, z2 = PLUG["cx"], PLUG["floor"], PLUG["z1"], PLUG["z2"]
    box(w, cx - 6, fy - 1, z1 - 3, cx + 6, fy + 7, z2 + 3, "white_concrete")      # solid outer mass: x 24..36, y 8..16, z 3..17
    widths = [3, 5, 5, 5, 3]
    for r, wd in enumerate(widths):
        h = wd // 2
        y = fy + 1 + r
        carve(w, cx - h, y, z1, cx + h, y, z2)
        for z in range(z1, z2 + 1):
            # wall cells, one beyond the opening
            for sgn in (-1, 1):
                x = cx + sgn * (h + 1)
                disp = 1 <= r <= 3 and z1 + 1 <= z <= z2 - 4
                b = "smooth_quartz" if (z % 3) else IRON
                if disp:
                    b = BLACK if (z + r) % 4 else "cyan_concrete"
                    if r == 2 and z % 5 == 0:
                        b = "sea_lantern"
                w.set(x, y, z, b)
    # floor, ceiling, forward wall (the display), rear hatch
    for x in range(cx - 1, cx + 2):
        for z in range(z1, z2 + 1):
            w.set(x, fy, z, "light_gray_concrete" if x != cx else IRON)
    for x in range(cx - 1, cx + 2):
        for z in range(z1, z2 + 1):
            w.set(x, fy + 6, z, "white_concrete")
        for z in range(z1 + 1, z2, 3):
            w.set(x, fy + 6, z, "sea_lantern") if x == cx else None
    for x in range(cx - 2, cx + 3):
        for y in range(fy + 1, fy + 6):
            if abs(x - cx) <= {fy + 1: 1, fy + 5: 1}.get(y, 2):
                z = z1 - 1
                b = BLACK
                if (x + y) % 3 == 0:
                    b = "cyan_concrete"
                if y == fy + 3 and x == cx:
                    b = "sea_lantern"
                w.set(x, y, z, b)
    for x in range(cx - 2, cx + 3):                          # rear hatch
        for y in range(fy + 1, fy + 6):
            if abs(x - cx) <= {fy + 1: 1, fy + 5: 1}.get(y, 2):
                w.set(x, y, z2 + 1, IRON if (x, y) != (cx, fy + 3) else "gray_concrete")
    # seat and grips
    box(w, cx - 1, fy + 1, 11, cx + 1, fy + 1, 12, BLACK)
    box(w, cx - 1, fy + 2, 11, cx + 1, fy + 2, 11, "light_gray_concrete")
    box(w, cx - 1, fy + 2, 13, cx + 1, fy + 4, 13, "gray_concrete")
    box(w, cx, fy + 5, 13, cx, fy + 5, 13, BLACK)
    for dx in (-1, 1):
        box(w, cx + dx, fy + 1, 9, cx + dx, fy + 2, 9, "gray_concrete")
        w.set(cx + dx, fy + 3, 9, bs("lightning_rod", facing="north"))
        pass
    for z in range(z1 + 1, z2):
        pass
    w.anchor("plug_seat", cx + 0.5, fy + 3, 11.5, yaw=YAW["north"])


def build_shaft(w):
    s = SHAFT
    X1, X2, Z1, Z2, F, T = s["x1"], s["x2"], s["z1"], s["z2"], s["floor"], s["top"]
    box(w, 0, 0, 0, X2 + 2, 159, Z2 + 2, "gray_concrete")
    carve(w, X1, F + 1, Z1, X2, T, Z2)
    # pad: a disc of iron with a hazard ring
    cxs = (X1 + X2 + 1) / 2.0
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            d = math.hypot(x + 0.5 - cxs, z + 0.5 - cxs)
            b = "gray_concrete"
            if d < 4.2:
                b = IRON
            elif d < 5.4:
                b = hazard(x + z, 0)
            elif d < 6.2:
                b = BLACK
            w.set(x, F, z, b)
    box(w, X1, 0, Z1, X2, F - 1, Z2, "polished_blackstone")
    # walls: plating, vertical guide rails (two on each side), hazard band, depth numerals
    for y in range(F + 1, T + 1):
        for u in range(X1, X2 + 1):
            for plane in (Z1 - 1, Z2 + 1):
                b = WALLM if y % 8 else WALLP
                if y % 8 == 0:
                    b = "sea_lantern"                       # ring lights every 8
                elif y % 24 in (1, 2) or y <= F + 3:
                    b = hazard(u, y)
                w.set(u, y, plane, b)
                w.set(u, y, plane, b) if True else None
            for plane in (X1 - 1, X2 + 1):
                b = WALLM if y % 8 else WALLP
                if y % 8 == 0:
                    b = "sea_lantern"
                elif y % 24 in (1, 2) or y <= F + 3:
                    b = hazard(u, y)
                w.set(plane, y, u, b)
        # guide rails: 2 blocks proud on every wall at 1/4 and 3/4
        for off in (5, 12):
            for (x, z) in ((off, Z1), (off, Z2), (X1, off), (X2, off)):
                w.set(x, y, z, IRON)
    # lights are ring blocks; make the corners solid too
    for y in range(F + 1, T + 1):
        for (x, z) in ((X1 - 1, Z1 - 1), (X2 + 1, Z1 - 1), (X1 - 1, Z2 + 1), (X2 + 1, Z2 + 1)):
            w.set(x, y, z, WALLM)
    for k, yy in enumerate(range(16, T, 24)):
        pass
        stencil(w, "L%d" % (k + 1), Z2 + 1, 12, yy + 4, "z", -1, 1, WHITE)
    # top: gantry ring at y 148, roof hatch with ring
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            if x <= X1 + 1 or x >= X2 - 1 or z <= Z1 + 1 or z >= Z2 - 1:
                w.set(x, 148, z, "polished_blackstone" if (x + z) % 5 else hazard(x, z))
    for x in range(X1 + 2, X2 - 1):
        for z in (Z1 + 2, Z2 - 2):
            w.set(x, 149, z, "iron_bars")
    for z in range(Z1 + 2, Z2 - 1):
        for x in (X1 + 2, X2 - 2):
            w.set(x, 149, z, "iron_bars")
    for x in range(X1, X2 + 1):
        for z in range(Z1, Z2 + 1):
            d = math.hypot(x + 0.5 - cxs, z + 0.5 - cxs)
            if d < 6.0:
                w.set(x, T + 1, z, IRON if d > 2.0 else "gray_concrete")
            w.set(x, T + 1, z, hazard(x, z)) if (6.0 <= d < 7.0) else None
    w.anchor("pad", cxs, F + 1, cxs, yaw=YAW["south"])
    w.anchor("shaft_top", cxs, 150.0, cxs, yaw=YAW["north"])
    w.anchor("shaft_top_gantry", X1 + 1.5, 149.0, cxs, yaw=YAW["east"])


# ================================================================================================ LIGHT
# Everything below is permanent light (it is in the canvas from the start, unlike CAGE_LIGHTS): hidden light blocks, run-lights
# and emergency lamps.  Minecraft block light falls 1 level per block; at the default gamma a surface needs about 7 to read
# clearly and 3 to 5 to show as a silhouette, and dim block light is tinted orange (it is neutral only near 14-15).
RUN_LIGHTS = []               # (x, y, z) amber run-lights in rail bases, deck lips and catwalk edges (always on)


def hlight(w, x, y, z, level):
    """A permanent hidden light block, only into open air.  True if placed."""
    if w.get(x, y, z) == AIR:
        w.set(x, y, z, bs("light", level=level))
        return True
    return False


def runlight(w, x, y, z, glass="orange_stained_glass", level=12):
    """A low amber lamp: stained glass set into a rail-base cell, with a hidden light block in the open air under it."""
    if w.get(x, y - 1, z) != AIR:
        return False
    w.set(x, y, z, glass)
    w.set(x, y - 1, z, bs("light", level=level))
    RUN_LIGHTS.append((x, y, z))
    return True


def corridor_lights(w):
    """Bright, even, clean light in every corridor and lobby.  Block light is only neutral white near level 14-15 (dim light is
    tinted orange), so the surfaces people see have to be within a block or two of a source: hidden level-15 blocks on the floor
    cells (every 3 along, every 2 across) light the floor and the lower walls, a second layer under the ceiling every 4 x 4 lights
    the upper walls and the ceiling.  (Before: strips only, 6 on the lobby floor, and the night sky did the rest.)"""
    n = 0
    for (x1, y1, z1, x2, y2, z2) in ROOMS_A:
        if x1 == 22 and y1 == 100:
            continue
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if x % 3 == 0 and z % 2 == 0:
                    n += hlight(w, x, y1, z, 15)
                if x % 4 == 2 and z % 4 == 2:
                    n += hlight(w, x, y2 - 1, z, 15)
                if (x in (x1, x2) or z in (z1, z2)) and (x + z) % 3 == 0:        # along the walls, at 1, 4, 7 above the floor
                    for y in range(y1 + 1, y2, 3):
                        n += hlight(w, x, y, z, 15)
    return n


def hall_lights(w):
    """The escalator hall: a lattice of hidden lights through the long void, dense over both landings and the pit floor."""
    n = 0
    for y in (102, 108, 116, 124, 132, 138, 146):
        for x in range(24, 89, 6):
            for z in (152, 160, 168):
                n += hlight(w, x, y, z, 15)
    for x in range(81, 89, 4):                     # over the upper landing
        for z in (153, 160, 167):
            n += hlight(w, x, 135, z, 15)
    for x in range(23, 31, 4):                     # over the lower landing
        for z in (153, 160, 167):
            n += hlight(w, x, 111, z, 15)
    return n


def flood_lights(w):
    """The flooded chamber: dark but readable.  A line of amber run-lights along the catwalk and its north arm, lamp bollards on
    the dock, a glow under the lake, more and stronger red emergency lamps on the walls and pillars."""
    b = B
    X1, X2, Z1, Z2, Y1 = b["x1"], b["x2"], b["z1"], b["z2"], b["y1"]
    for x in range(24, 98, 4):                                      # east-west catwalk rails z 158 and 162
        for z in (158, 162):
            runlight(w, x, BRIDGE_Y, z)
    for z in range(145, 158, 4):                                    # north arm rails x 94 and 98
        for x in (94, 98):
            runlight(w, x, BRIDGE_Y, z)
    for z in range(155, 166, 5):                                    # the dock's hazard lip
        runlight(w, 22, BRIDGE_Y, z)
    for x in (12, 17, 21):                                          # dock bollards: iron post, amber lamp, hidden light over it
        for z in (155, 165):
            w.set(x, BRIDGE_Y + 1, z, IRON)
            w.set(x, BRIDGE_Y + 2, z, IRON)
            w.set(x, BRIDGE_Y + 3, z, "orange_stained_glass")
            hlight(w, x, BRIDGE_Y + 4, z, 13)
            RUN_LIGHTS.append((x, BRIDGE_Y + 3, z))
    for x in (13, 18):                                              # over the middle of the dock
        hlight(w, x, BRIDGE_Y + 4, 160, 13)
    for x in range(14, 148, 10):                                    # the lake glows: hidden light under the glass top
        for z in range(148, 186, 10):
            if w.get(x, LAKE_Y - 1, z) == "minecraft:" + LIQUID:
                w.set(x, LAKE_Y - 1, z, bs("light", level=9))
    # emergency lamps: walls, both long walls and both ends, and three heights on every pillar
    for x in range(16, 146, 12):
        for y in (58, 66):
            emergency_lamp(w, x, y, Z2 + 1, (x, y, Z2))
            if not (88 <= x <= 104):
                emergency_lamp(w, x, y, Z1 - 1, (x, y, Z1))
    for z in range(150, 182, 12):
        for y in (58, 66):
            emergency_lamp(w, X1 - 1, y, z, (X1, y, z))
            emergency_lamp(w, X2 + 1, y, z, (X2, y, z))
    for x in (36, 62, 124, 138):
        for z in (150, 180):
            for y in (64, 70):
                emergency_lamp(w, x + 1, y, z - 1, (x + 1, y + 1, z - 1))
                emergency_lamp(w, x + 1, y, z + 3, (x + 1, y + 1, z + 3))
            emergency_lamp(w, x + 1, 58, z + 3, (x + 1, 59, z + 3))


def cage_lights_baseline(w):
    """The cage with the lights off: dark but readable.  Amber run-lights along the bridge rails and all three wall catwalks, a glow
    under the coolant that lights the walls and the giant's shoulders from below, and a faint red rim round the head from
    emergency lamps on the pylon tops and hidden lights beside the cheeks.  Nothing hangs in front of the face."""
    c = CAGE
    X1, X2, Z1, Z2 = c["x1"], c["x2"], c["z1"], c["z2"]
    for z in range(76, Z2 - 1, 4):                                   # bridge rails
        for x in (93, 99):
            runlight(w, x, BRIDGE_Y, z, level=12)
    for x in range(66, 92, 4):                                       # the gurney spur
        for z in (GURNEY_Z - 1, GURNEY_Z + 3):
            runlight(w, x, BRIDGE_Y, z, level=12)
    for z in (138, 139):                                             # the tunnel behind the south wall
        hlight(w, CX, BRIDGE_Y + 4, z, 12)
    for y in (62, 76, 90):                                           # wall catwalks: lamps in the hazard edge, light under
        for edge in (X1 + 2, X2 - 2):
            for z in range(Z1 + 9, Z2 - 4, 6):
                runlight(w, edge, y, z, level=10)
    for x in range(66, 127, 8):                                      # the coolant glows (hidden light 2 under the top)
        for z in range(28, 135, 8):
            if w.get(x, SURF - 1, z) == "minecraft:" + LIQUID:
                w.set(x, SURF - 1, z, bs("light", level=10))
    # giant's rim: emergency lamps on the tops of the tall pylons, hidden lights over them and beside the cheeks
    for sgn in (-1, 1):
        xi = CX + sgn * 13
        for z in (40, 44, 48):
            ytop = None
            for y in range(90, 30, -1):
                if w.get(xi, y, z) not in (None, AIR):
                    ytop = y
                    break
            if ytop is not None:
                emergency_lamp(w, xi, ytop + 1, z, (xi, ytop + 2, z))
        # a faint rim beside the cheeks and over the crown: low levels, and behind the face plane, so that the front of the face stays
        # at 4 or less with the lights off (the floodlight must have something to do) while the head still reads against the red wall
        for (dx, y, z, lvl) in ((11, 54, 56, 8), (11, 60, 56, 8), (11, 66, 56, 8), (9, 52, 56, 6), (6, 72, 55, 6), (9, 69, 55, 5)):
            hlight(w, CX + sgn * dx, y, z, lvl)
    # a dim wash on the front of the face from far in front of it (6 to 8 blocks): 2 to 4 on the plate, the lights-off reading
    for (x, y, z, lvl) in FACE_WASH:
        hlight(w, x, y, z, lvl)
    # red emergency lamps along the north wall behind the giant: the head stands against a faintly lit wall and reads as a shape
    for x in range(72, 121, 6):
        for y in (50, 58, 66, 74):
            emergency_lamp(w, x, y, Z1 - 1, (x, y, Z1))
    # a shaded light over the stop and the deck lip so that the player's own feet and the edge read
    for (x, y, z) in ((CX, BRIDGE_Y + 5, 73), (CX, BRIDGE_Y + 5, 77), (CX, BRIDGE_Y + 5, 89)):
        hlight(w, x, y, z, 11)


def wall_detail(w):
    """Industrial depth on both side walls at the player's eye level near the bridge (y 40..61, z 28..134): three pipe runs with
    collars, cable trays, control cabinets, warning plates and stencilled numbers, each with a red lamp beside it."""
    c = CAGE
    X1, X2, Z1, Z2 = c["x1"], c["x2"], c["z1"], c["z2"]
    for sgn in (-1, 1):
        xp = X1 + 1 if sgn < 0 else X2 - 1                       # pipes stand one block off the wall
        xw = X1 - 1 if sgn < 0 else X2 + 1                       # the wall plane (plates are set flush in it)
        step = -1 if sgn < 0 else 1
        for z in range(Z1 + 3, Z2 - 3):
            for (y, blk) in ((44, "weathered_copper"), (47, "gray_concrete"), (50, "copper_block")):
                if w.get(xp, y, z) == AIR:
                    w.set(xp, y, z, blk if z % 8 else IRON)        # an iron collar every 8
            if z % 8 == 0:
                for y in (45, 46, 48, 49):
                    if w.get(xp, y, z) == AIR:
                        w.set(xp, y, z, IRON)
            if w.get(xp, 52, z) == AIR:                            # a cable tray with an orange stripe
                w.set(xp, 52, z, "black_concrete" if z % 12 else ORANGE)
        # warning plates and stencils, flush in the wall plane
        for k, zc in enumerate((66, 96, 114, 132)):         # (clear of the gurney door at z 79..81)
            u0 = zc + (3 if sgn < 0 else -3)
            if k % 2 == 0:
                plate(w, "HOT", xw, u0, 56, "x", step, bg=YELLOW, fg=BLACK)
            else:
                plate(w, "A-%02d" % (7 + k), xw, u0, 56, "x", step, bg="gray_concrete", fg=WHITE)
            lx = xp
            emergency_lamp(w, lx, 55, zc + 6 * (1 if sgn > 0 else -1), (lx + (1 if sgn < 0 else -1), 55, zc + 6 * (1 if sgn > 0 else -1)))
        stencil(w, "L%d" % (3 if sgn < 0 else 4), xw, 57 if sgn < 0 else 42, 50, "x", step, 2, "white_concrete")
        # control cabinets at the foot of the wall: a body against the wall, a face with a screen and two indicators
        xb = X1 if sgn < 0 else X2
        for zc in (84, 104, 124):
            for dz in range(3):
                for y in range(39, 43):
                    if w.get(xb, y, zc + dz) in (AIR, "minecraft:gray_concrete"):
                        w.set(xb, y, zc + dz, "gray_concrete")
                    if w.get(xp, y, zc + dz) == AIR:
                        w.set(xp, y, zc + dz, "light_gray_concrete" if y in (39, 42) else ("cyan_concrete" if y == 41 else "gray_concrete"))
            if w.get(xp, 40, zc) == "minecraft:gray_concrete":
                w.set(xp, 40, zc, "red_concrete")
            if w.get(xp, 40, zc + 2) == "minecraft:gray_concrete":
                w.set(xp, 40, zc + 2, "lime_concrete")


# ================================================================================================ assembly
# ================================================================================================ FLOODLIGHT
# "The lights come up".  Block light falls one level per block and a surface takes the level of the air cell it looks at, so a
# sculpture is floodlit by hidden `light` blocks in the air a block or two in front of its surfaces; the visible lamp banks (masts,
# gantry) are the believable source, the hidden blocks do the lighting.  Everything here is in CAGE_LIGHTS: air (or the dead lamp
# panel) when the lights are off, lit by the story bank by bank.  tools/story/hq_cage.py (copied in story_banks) sorts them: the
# lights of the cage with z <= 66, y <= 70 and |x - 96| <= 26 are the LAST bank, so every light in FLOOD_FACE (and the masts' lamps)
# switches on in one step together; FLOOD_CROWN (above y 70: the crown and the horn) and everything farther away come first.
# FLOOD_FACE / FLOOD_CROWN are baked by `python hq.py --design` (a greedy cover of the visible surfaces of the giant, see design_floods);
# verify() measures the result, so a change of the head or the shoulders shows up there.
# <<FLOOD-DATA
FACE_WASH = [
    (84, 52, 60, 15), (84, 60, 60, 13), (84, 68, 60, 11), (86, 48, 60, 14), (86, 58, 62, 13), (86, 62, 62, 13), (88, 50, 62, 13),
    (88, 54, 62, 14), (92, 70, 62, 10), (92, 72, 60, 8), (94, 58, 60, 4), (94, 60, 62, 6), (94, 62, 62, 7), (94, 66, 62, 7),
    (94, 68, 60, 6), (96, 48, 62, 5), (96, 58, 62, 5), (96, 66, 62, 7), (96, 70, 60, 5), (98, 48, 60, 6), (98, 58, 68, 12),
    (98, 60, 60, 4), (98, 62, 62, 7), (98, 66, 62, 7), (98, 68, 60, 6), (98, 72, 60, 6), (100, 50, 62, 9), (100, 52, 60, 7),
    (100, 70, 62, 10), (102, 54, 60, 10), (102, 60, 60, 7), (104, 62, 62, 11), (104, 68, 60, 7), (106, 58, 62, 13),
]
FLOOD_FACE = [
    (73, 57, 51), (75, 57, 43), (76, 50, 53), (77, 42, 54), (77, 43, 54), (79, 46, 47), (79, 48, 52), (79, 54, 51), (79, 55, 46),
    (79, 58, 48), (80, 47, 57), (80, 59, 51), (81, 55, 53), (81, 64, 45), (81, 70, 40), (82, 53, 56), (82, 61, 49), (82, 68, 43),
    (83, 40, 33), (83, 41, 37), (83, 49, 57), (83, 57, 52), (83, 61, 49), (83, 63, 47), (83, 70, 41), (84, 41, 36), (84, 41, 38),
    (84, 41, 39), (84, 41, 40), (84, 41, 44), (84, 41, 49), (84, 41, 50), (84, 43, 44), (84, 43, 49), (84, 44, 41), (84, 44, 46),
    (84, 44, 51), (84, 44, 53), (84, 46, 38), (84, 46, 46), (84, 46, 51), (84, 47, 43), (84, 47, 48), (84, 47, 53), (84, 47, 55),
    (84, 49, 40), (84, 49, 48), (84, 50, 45), (84, 50, 50), (84, 50, 52), (84, 51, 54), (84, 51, 57), (84, 52, 38), (84, 52, 42),
    (84, 53, 47), (84, 53, 49), (84, 54, 50), (84, 54, 51), (84, 54, 54), (84, 55, 40), (84, 55, 44), (84, 56, 44), (84, 57, 48),
    (84, 58, 38), (84, 58, 43), (84, 59, 41), (84, 59, 50), (84, 60, 46), (84, 61, 40), (84, 63, 40), (84, 63, 43), (84, 64, 38),
    (84, 64, 39), (84, 64, 43), (84, 67, 41), (84, 69, 38), (84, 70, 38), (85, 41, 34), (85, 41, 47), (86, 40, 58), (86, 41, 44),
    (86, 41, 53), (86, 41, 54), (86, 42, 33), (86, 42, 42), (86, 42, 43), (87, 42, 37), (87, 42, 40), (88, 42, 46), (88, 42, 48),
    (88, 42, 51), (88, 42, 53), (88, 42, 56), (89, 41, 59), (89, 62, 54), (89, 63, 56), (89, 65, 58), (89, 66, 59), (89, 68, 59),
    (90, 43, 57), (90, 44, 50), (90, 54, 49), (90, 57, 55), (90, 58, 53), (90, 59, 56), (90, 62, 57), (90, 62, 58), (90, 64, 59),
    (90, 64, 60), (90, 67, 60), (90, 70, 51), (90, 70, 53), (91, 43, 53), (91, 43, 60), (91, 44, 54), (91, 50, 53), (91, 57, 53),
    (91, 58, 56), (91, 59, 59), (91, 60, 58), (91, 65, 61), (91, 69, 57), (92, 44, 59), (92, 45, 53), (92, 49, 52), (92, 53, 58),
    (92, 54, 53), (92, 55, 56), (92, 56, 59), (92, 57, 59), (92, 61, 59), (92, 63, 59), (92, 63, 60), (92, 66, 60), (92, 67, 59),
    (92, 68, 59), (92, 69, 56), (92, 70, 54), (93, 44, 57), (93, 51, 58), (93, 54, 57), (93, 59, 60), (93, 60, 60), (93, 64, 61),
    (93, 68, 58), (93, 70, 58), (94, 50, 59), (94, 53, 59), (94, 55, 58), (94, 57, 60), (94, 62, 60), (94, 64, 61), (94, 66, 60),
    (94, 69, 57), (94, 70, 55), (95, 42, 60), (95, 46, 62), (95, 47, 62), (95, 50, 60), (95, 54, 60), (95, 56, 59), (95, 57, 59),
    (95, 59, 60), (95, 61, 59), (95, 67, 59), (95, 68, 59), (95, 70, 59), (96, 45, 59), (96, 48, 61), (96, 50, 61), (96, 52, 60),
    (96, 55, 59), (96, 57, 61), (96, 60, 61), (96, 63, 61), (96, 65, 60), (97, 44, 59), (97, 46, 61), (97, 50, 60), (97, 55, 59),
    (97, 56, 60), (97, 57, 60), (97, 58, 59), (97, 60, 60), (97, 61, 59), (97, 62, 59), (97, 66, 59), (97, 69, 59), (98, 42, 60),
    (98, 44, 54), (98, 50, 59), (98, 53, 59), (98, 62, 60), (98, 64, 61), (98, 66, 60), (98, 69, 57), (98, 69, 58), (98, 70, 55),
    (99, 44, 57), (99, 48, 53), (99, 51, 58), (99, 54, 58), (99, 55, 58), (99, 58, 60), (99, 59, 60), (99, 63, 59), (99, 67, 59),
    (99, 68, 58), (100, 45, 53), (100, 49, 52), (100, 53, 48), (100, 54, 53), (100, 55, 56), (100, 56, 59), (100, 57, 59),
    (100, 58, 59), (100, 61, 59), (100, 63, 60), (100, 65, 61), (100, 66, 61), (100, 67, 60), (100, 69, 56), (100, 70, 54),
    (101, 43, 53), (101, 43, 55), (101, 43, 58), (101, 57, 53), (101, 57, 56), (101, 57, 57), (101, 60, 58), (101, 61, 58),
    (101, 64, 59), (101, 68, 59), (101, 69, 57), (101, 70, 53), (102, 44, 50), (102, 58, 53), (102, 58, 55), (102, 59, 56),
    (102, 62, 57), (102, 66, 60), (102, 69, 52), (103, 41, 59), (103, 42, 39), (103, 66, 59), (104, 42, 46), (104, 42, 48),
    (104, 42, 51), (104, 42, 53), (104, 42, 56), (105, 42, 32), (105, 42, 37), (105, 42, 42), (106, 39, 58), (106, 41, 36),
    (106, 41, 41), (106, 41, 46), (106, 41, 51), (106, 41, 57), (106, 43, 38), (106, 47, 52), (106, 52, 52), (106, 60, 43),
    (106, 62, 38), (107, 41, 34), (107, 42, 43), (107, 42, 48), (107, 42, 53), (107, 45, 45), (107, 45, 50), (107, 48, 47),
    (107, 50, 50), (107, 57, 38), (108, 41, 39), (108, 41, 44), (108, 41, 49), (108, 41, 54), (108, 44, 41), (108, 44, 46),
    (108, 44, 51), (108, 44, 56), (108, 46, 38), (108, 46, 54), (108, 47, 43), (108, 47, 48), (108, 48, 55), (108, 49, 40),
    (108, 49, 51), (108, 50, 45), (108, 51, 54), (108, 52, 38), (108, 52, 42), (108, 52, 48), (108, 53, 46), (108, 53, 55),
    (108, 54, 51), (108, 55, 40), (108, 55, 45), (108, 55, 51), (108, 56, 43), (108, 57, 48), (108, 59, 41), (108, 59, 50),
    (108, 60, 39), (108, 60, 46), (108, 60, 49), (108, 61, 41), (109, 38, 57), (109, 40, 33), (109, 40, 35), (109, 41, 57),
    (109, 44, 57), (109, 47, 57), (109, 50, 57), (109, 57, 52), (110, 53, 56), (110, 55, 54), (110, 60, 50), (111, 53, 42),
    (112, 47, 46), (113, 38, 55), (113, 42, 54), (113, 48, 52), (113, 53, 48), (113, 56, 46), (113, 58, 48), (114, 55, 52),
    (115, 49, 54),
]
FLOOD_CROWN = [
    (82, 74, 39), (83, 74, 39), (94, 74, 58), (97, 74, 50),
]
# FLOOD-DATA>>
_DESIGN = [False]                            # True while design_floods builds the set without the baked lights
EYES_VIEW = ((96.5, 55.62, 72.5), (94.5, 55.62, 76.5), (98.5, 55.62, 76.5), (96.5, 55.62, 85.0), (96.5, 55.62, 110.0))   # where the face is seen from


def flood_mast(w, mx, mz=65):
    """A flood mast standing in the coolant at (mx, mz): a post up to y 64 and a bank of 3 x 4 lamps (dead gray panels) on its north
    face under a black hood, beside the shoulders, outside the lines from the stop to the face."""
    for y in range(FLOOR_C + 1, 65):
        w.set(mx, y, mz, "gray_concrete" if (y // 5) % 2 else "black_concrete")
    box(w, mx - 2, 65, mz - 1, mx + 2, 65, mz, "black_concrete")                      # cradle
    box(w, mx - 2, 70, mz - 2, mx + 2, 70, mz, "black_concrete")                      # hood, overhanging the lamps
    box(w, mx - 1, 66, mz, mx + 1, 69, mz, "black_concrete")                          # back plate
    for sx in (-2, 2):
        box(w, mx + sx, 66, mz - 1, mx + sx, 69, mz, "black_concrete")                # cheeks
    for dx in (-1, 0, 1):
        for y in range(66, 70):
            lamp(w, mx + dx, y, mz - 1)


def flood_gantry(w):
    """An overhead gantry over the giant's head (y 82, z 61..63) on two chains from the roof truss, with five lamp panels (3 x 2) hung
    under it.  Far above the lines from the stop to the face (they pass z 62 at y 70)."""
    box(w, 80, 82, 61, 112, 82, 63, "gray_concrete")
    for x in range(80, 113):
        w.set(x, 83, 61, hazard(x, 0) if x % 2 else "gray_concrete")
    for x in (80, 112):
        for y in range(83, 109):
            w.set(x, y, 62, bs("iron_chain", axis="y"))
    for cx in (84, 90, 96, 102, 108):
        box(w, cx - 2, 81, 61, cx + 2, 81, 63, "black_concrete") if False else None
        box(w, cx - 2, 79, 61, cx - 2, 81, 63, "black_concrete")
        box(w, cx + 2, 79, 61, cx + 2, 81, 63, "black_concrete")
        for dx in (-1, 0, 1):
            for y in (80, 81):
                lamp(w, cx + dx, y, 62)
        box(w, cx - 1, 80, 61, cx + 1, 81, 61, "black_concrete")
        box(w, cx - 1, 80, 63, cx + 1, 81, 63, "black_concrete")


def deck_floods():
    """The bridge deck: a hidden light at head height over the middle every 4 blocks from the stop to the door puts 10 on every deck cell."""
    for z in range(73, 138, 4):
        CAGE_LIGHTS.append((CX, BRIDGE_Y + 2, z, bs("light", level=15)))


def wall_floods(w):
    """The cage walls and catwalks, 10 to 13: hidden light blocks in the air against the wall on a perfect diamond lattice (every wall cell
    within 4 blocks of one: 11 or better), side walls z 28..135, y 40..104, and the north wall except the lower middle behind the giant (that stays
    dark, so that the lights on it do not land in the face bank: the giant stands against a lit upper wall and a dark lower one)."""
    c = CAGE
    X1, X2, Z1, Z2 = c["x1"], c["x2"], c["z1"], c["z2"]

    def put(cands):
        for (x, y, z) in cands:
            if w.get(x, y, z) == AIR:
                CAGE_LIGHTS.append((x, y, z, bs("light", level=15)))
                return True
        return False
    for xa, off, step in ((X1, 0, 1), (X2, 7, -1)):
        for y in range(40, 105):
            for z in range(28, 136):
                if (z + 9 * y + off) % 41 == 0:
                    put([(xa, y, z), (xa + step, y, z), (xa, y + 1, z), (xa, y - 1, z), (xa, y, z + 1), (xa, y, z - 1), (xa + 2 * step, y, z)])
    for y in range(40, 105):
        for x in range(X1 + 2, X2 - 1):
            if (x + 9 * y + 3) % 41 == 0 and not (abs(x - CX) <= 26 and y <= 70):
                put([(x, y, Z1), (x, y, Z1 + 1), (x, y + 1, Z1), (x, y - 1, Z1)])


def cage_floods(w):
    """All the floodlight of the cage (see the comment above)."""
    flood_mast(w, CX - 23, 62)
    flood_mast(w, CX + 23, 62)
    flood_gantry(w)
    if not _DESIGN[0]:
        for (x, y, z) in FLOOD_FACE + FLOOD_CROWN:
            CAGE_LIGHTS.append((x, y, z, bs("light", level=15)))
    deck_floods()
    wall_floods(w)
    # under the raised hand (it is placed by the story over the shield column; its palm is at y 61, z 74..80)
    for (x, y, z) in ((CX - 3, 60, 76), (CX + 3, 60, 76), (CX, 60, 79), (CX - 4, 60, 82), (CX + 4, 60, 82), (CX, 60, 85),
                      (CX - 6, 60, 79), (CX + 6, 60, 79)):
        CAGE_LIGHTS.append((x, y, z, bs("light", level=15)))
    # the eyes' own glow, to be set with the eyes: on the brow and the bridge end
    for (x, y, z, lvl) in ((CX - 4, 60, 60, 12), (CX + 4, 60, 60, 12), (CX, 57, 61, 12), (CX - 5, 56, 67, 11), (CX + 5, 56, 67, 11),
                           (CX, 58, 68, 11), (CX - 9, 66, 60, 11), (CX + 9, 66, 60, 11)):
        EYE_GLOW.append((x, y, z, bs("light", level=lvl)))
    seen, uniq = set(), []                      # one entry per cell (the story switches cells; a repeated cell would count twice in its banks)
    for l in CAGE_LIGHTS:
        if (l[0], l[1], l[2]) not in seen:
            seen.add((l[0], l[1], l[2]))
            uniq.append(l)
    CAGE_LIGHTS[:] = uniq


def build(w):
    EYES_LEFT.clear(); EYES_RIGHT.clear(); CAGE_LIGHTS.clear(); BOOTH_LIGHTS.clear(); EMERGENCY.clear(); DOORS.clear()
    EYE_GLOW.clear(); RUN_LIGHTS.clear()
    build_flood(w)
    build_cage(w)
    cage_floods(w)
    build_corridors(w)
    build_plug(w)
    build_shaft(w)
    cage_anchors(w)
    w.anchor("loop_door", LOOP_DOOR_AT[0], UY + 1, LOOP_DOOR_AT[1], yaw=LOOP_DOOR_AT[2])
    seal_skylight(w)
    HAND["lowered"] = hand_bbox(False)
    HAND["raised"] = hand_bbox(True)


# ================================================================================================ checks
def _local(w, name):
    a = w.anchors[name]
    return (a["x"] - w.origin[0], a["y"] - w.origin[1], a["z"] - w.origin[2])


def walk_passable(w, tab):
    rgb, kind, alpha, emit = tab
    ok = np.zeros(len(w.palette), bool)
    for i, b in enumerate(w.palette):
        if b is None:
            continue
        nm = b.split("[")[0].replace("minecraft:", "")
        ok[i] = nm in ("air", "light", "ladder", "iron_chain", "redstone_torch")
    return ok[w.a]


def walk_bfs(w, start, goal=None, clear_boxes=(), tab=None, drop=3):
    """BFS for a 1 wide, 2 tall walker (step up 1, drop up to `drop`).  Returns the set of reached feet cells."""
    tab = tab or tables(w)
    pas = walk_passable(w, tab)
    for (x1, y1, z1, x2, y2, z2) in clear_boxes:
        pas[x1:x2 + 1, y1:y2 + 1, z1:z2 + 1] = True
    solid = ~pas
    # slabs count as floor (solid) for feet purposes; bars, glass etc. are solid for walking
    sx, sy, sz = pas.shape
    s = tuple(int(math.floor(v)) for v in start)
    if not (pas[s] and pas[s[0], s[1] + 1, s[2]] and solid[s[0], s[1] - 1, s[2]]):
        return None, "start not standable %s (%s / %s / below %s)" % (s, w.get(*s), w.get(s[0], s[1] + 1, s[2]), w.get(s[0], s[1] - 1, s[2]))
    seen = {s}
    todo = [s]
    gl = None if goal is None else tuple(int(math.floor(v)) for v in goal)
    while todo:
        x, y, z = todo.pop()
        for dx, dz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, nz = x + dx, z + dz
            if not (0 <= nx < sx and 0 <= nz < sz):
                continue
            for ny in (y + 1, y, y - 1, y - 2, y - 3)[: 3 + drop - 1]:
                if ny < 1 or ny + 1 >= sy:
                    continue
                if not (pas[nx, ny, nz] and pas[nx, ny + 1, nz] and solid[nx, ny - 1, nz]):
                    continue
                if ny == y + 1 and not pas[x, y + 2, z]:
                    continue
                if ny < y:
                    if not all(pas[nx, yy, nz] for yy in range(ny, y + 2)):
                        continue
                if (nx, ny, nz) not in seen:
                    seen.add((nx, ny, nz))
                    todo.append((nx, ny, nz))
                break
    return seen, None


def reaches(seen, p, slack=1):
    if seen is None:
        return False
    px, py, pz = (int(math.floor(v)) for v in p)
    for dy in range(-slack, slack + 1):
        if (px, py + dy, pz) in seen:
            return True
    return False


def leak_check(w, tab=None):
    """Air-like cells next to untouched cells or the box boundary: a hole to the void."""
    tab = tab or tables(w)
    rgb, kind, alpha, emit = tab
    air = (kind[w.a] == 0) & (w.a != 0)
    void = w.a == 0
    pad = np.pad(void, 1, constant_values=True)
    near_void = np.zeros_like(void)
    for ax in range(3):
        for sh in (1, -1):
            sl = [slice(1, -1)] * 3
            sl[ax] = slice(1 + sh, w.a.shape[ax] + 1 + sh)
            near_void |= pad[tuple(sl)]
    leaks = np.argwhere(air & near_void)
    return leaks


_SKY_OPEN = ("barrier", "iron_bars", "door", "grate", "ladder", "chain", "torch", "fence", "rod", "pane", "button", "lever", "carpet",
             "_slab", "_stairs", "_wall", "bulb")        # (bulbs and walls are not all clear in the game; assuming clear is the safe side)


def sky_opaque(w):
    """Bool grid: cells that stop skylight - full opaque cubes (tinted glass stops it too; clear glass, bars, doors, grates,
    slabs, stairs, light blocks and air let it through, so they are treated as open)."""
    op = np.zeros(len(w.palette), bool)
    for i, b in enumerate(w.palette):
        if not b:
            continue
        nm = b.split("[")[0].replace("minecraft:", "")
        if nm == "air":
            continue
        if nm == "tinted_glass":
            op[i] = True
        elif "glass" in nm or nm == "light":
            op[i] = False
        elif nm in ("sea_lantern", "shroomlight", "magma_block", "redstone_lamp"):
            op[i] = True
        elif "lantern" in nm:
            op[i] = False
        else:
            op[i] = not any(t in nm for t in _SKY_OPEN)
    return op[w.a]


def skylight_flood(w):
    """Skylight 0..15 over the whole canvas, as the game computes it if everything outside the box is open sky (it is: the
    set stands in a void world).  Returns (S, opaque, interior) where interior = cells that were drawn and are not opaque."""
    opq = sky_opaque(w)
    P = np.pad(opq, 1, constant_values=False)
    above = np.cumsum(P[:, ::-1, :], axis=1)[:, ::-1, :]          # opaque cells at or above each cell
    S = np.where((above == 0) & ~P, 15, 0).astype(np.int8)
    for _ in range(16):
        m = S.copy()
        for ax in range(3):
            for sh in (1, -1):
                m = np.maximum(m, (np.roll(S, sh, axis=ax) - 1).clip(0))
        S2 = np.where(~P, m, 0).astype(np.int8)
        if (S2 == S).all():
            break
        S = S2
    S = S[1:-1, 1:-1, 1:-1]
    return S, opq, (w.a != 0) & ~opq


def skylight_check(w):
    """No skylight may reach any drawn, non-opaque cell (air, glass, bars, slabs ...).  Also the plain per-column rule: scanning
    down from the top of the box, the first drawn cell must be an opaque cube, never air or a see-through block above one.
    Returns (n_flood_cells, n_column_cells, sample cells)."""
    S, opq, inner = skylight_flood(w)
    flood = inner & (S > 0)
    first_op = np.where(opq.any(axis=1), opq.shape[1] - 1 - np.argmax(opq[:, ::-1, :], axis=1), -1)       # highest opaque cell per column
    ys = np.arange(w.a.shape[1])[None, :, None]
    col = inner & (ys > first_op[:, None, :])
    both = flood | col
    return int(flood.sum()), int(col.sum()), [tuple(int(v) for v in p) for p in np.argwhere(both)[:10]]


def light_report(w, tab, out=print):
    """Block light (0..15) in the feet cell of every walkable cell of each stretch of the route: minimum, 5th percentile, median;
    lights as built (everything the story has not switched on is off) and with every cage light on."""
    A = lambda n: _local(w, n)
    door = [DOORS["cage_door"]["box"]]
    seen, _ = walk_bfs(w, A("start"), tab=tab)
    seen2, _ = walk_bfs(w, A("dock"), clear_boxes=door, tab=tab)
    w_on = lights_on(w)
    Ls = {"off": light_map(w, tab), "on": light_map(w_on, tables(w_on))}
    stretches = [
        ("corridors + lobby (y 131)", [c for c in seen if c[1] == 131]),
        ("escalator + lower corridor", [c for c in seen if c[1] < 131]),
        ("dock", [c for c in seen2 if c[0] <= 22 and c[1] == 54 and c[2] > 150]),
        ("catwalk (east-west)", [c for c in seen2 if 23 <= c[0] <= 93 and c[1] == 54 and c[2] > 150]),
        ("catwalk north arm", [c for c in seen2 if 94 <= c[0] <= 98 and c[1] == 54 and 143 <= c[2] <= 157]),
        ("bridge z 72..137", [c for c in seen2 if 93 <= c[0] <= 99 and c[1] == 54 and 72 <= c[2] <= 137]),
        ("gurney spur", [c for c in seen2 if c[0] < 93 and c[1] == 54 and 78 <= c[2] <= 82]),
    ]
    rep = {}
    for nm, cells in stretches:
        for mode, L in Ls.items():
            v = np.array([L[c] for c in cells]) if cells else np.array([0])
            rep["%s/%s" % (nm, mode)] = (int(v.min()), float(np.percentile(v, 5)), float(np.median(v)))
        a, b = rep["%s/off" % nm], rep["%s/on" % nm]
        out("  light %-28s n=%4d  as built: min %2d p5 %4.1f median %4.1f   cage lights on: min %2d p5 %4.1f median %4.1f" % (
            nm, len(cells), a[0], a[1], a[2], b[0], b[1], b[2]))
    return rep


def verify_light(w, out=print):
    """The floodlight acceptance: the light levels on the giant in the story's three states, the order of the banks, the eyes, the deck,
    the walls and the commander.  Returns a dict of measures and of pass / fail flags."""
    res = {}
    tab = tables(w)
    pm = partial_masks(w)
    states = light_states(w)
    groups, booth = story_banks()
    out("floodlight: CAGE_LIGHTS %d (booth %d), banks %s" % (len(CAGE_LIGHTS), len(booth), [len(g) for g in groups]))
    out("  FACE_WASH (permanent, lights-off) %d, FLOOD_FACE %d, FLOOD_CROWN %d" % (len(FACE_WASH), len(FLOOD_FACE), len(FLOOD_CROWN)))
    m = measure_face(w, out, states)
    on, off = m["on"]["head south faces"], m["off"]["head south faces"]
    res["on_median"], res["on_min"], res["off_max"] = float(np.median(on)), int(on.min()), int(off.max())
    res["on_vis_min"] = int(m["on"]["head faces seen from the stop"].min())
    res["floodlight_ok"] = res["on_median"] >= 13 and res["on_min"] >= 10 and res["off_max"] <= 4
    out("  lights on: median %.0f (want >= 13), minimum %d (want >= 10); lights off: maximum %d (want <= 4): %s" % (
        res["on_median"], res["on_min"], res["off_max"], res["floodlight_ok"]))
    # the last bank is the face
    last = {(l[0], l[1], l[2]) for l in groups[-1]}
    flood = {c for c in FLOOD_FACE}
    res["flood_in_last_bank"] = flood <= last
    early = [c for c in FLOOD_CROWN]
    where = sorted({i for i, g in enumerate(groups[:-1]) for l in g if (l[0], l[1], l[2]) in set(early)})
    out("  last bank: %d lights, of them %d FLOOD_FACE (all of FLOOD_FACE in it: %s), the masts' lamps and the fin lamps; the %d FLOOD_CROWN lights (y > 70) are in "
        "bank(s) %s; no wall, deck or gantry light is in it: %s" % (
            len(last), len(flood & last), res["flood_in_last_bank"], len(early), where,
            not any(c[1] > 70 or c[2] > 66 or abs(c[0] - 96) > 26 for c in last)))
    # the eyes: their front faces seen from the stop
    pts, per = [], []
    for cells in (EYES_LEFT, EYES_RIGHT):
        for (x, y, z) in cells:
            ps = [(x + (i + 0.5) / 5, y + (j + 0.5) / 5, z + 1.02) for i in range(5) for j in range(5)]
            v = visible_points(w, tab, EYES_VIEW[0], ps, strict=True)
            per.append(float(v.mean()))
    res["eye_visible_fraction"] = (min(per), float(np.mean(per)))
    out("  eyes: the front face of each eye cell is seen from the stop (strict line of sight, 25 samples): min %.0f%%, mean %.0f%% of the face" % (
        100 * min(per), 100 * float(np.mean(per))))
    # strict lines from the stop: nothing but the head itself may stand between the stop and the face, the eyes or the commander
    fs = face_sets(w)
    head_cells = {f[0] for f in fs["head_vis"]} | {f[0] for f in fs["head_south"]}
    pts = [(c[0] + 0.5 + n[0] * 0.52, c[1] + 0.5 + n[1] * 0.52, c[2] + 0.5 + n[2] * 0.52) for c, n in fs["head_vis"]]
    bad = []
    for e in EYES_VIEW[:3]:
        for p in pts:
            ok, blk = sees(w.a, tab, e, p, masks=pm, transparent_kinds=(0,))
            if not ok and blk is not None and tuple(int(v) for v in blk) not in head_cells:
                b = tuple(int(v) for v in blk)
                if b[1] > BRIDGE_Y and not (HEAD_X0 <= b[0] <= HEAD_X0 + 20 and HEAD_Y0 <= b[1] <= HEAD_Y0 + 40 and HEAD_ZF - 27 <= b[2] <= HEAD_ZF):
                    bad.append((e, b, w.get(*b)))     # (the deck itself hides the chin from below: not a crossing)
    res["sightline_blockers"] = len(bad)
    out("  strict lines from the stop, the captain's and the scientist's marks to every seen face of the head: blocked by anything but the head: %d%s" % (
        len(bad), "" if not bad else "  e.g. %s" % bad[:3]))
    # the deck and the walls
    L = states["on"][2]
    deck = [L[x, BRIDGE_Y + 1, z] for x in range(94, 99) for z in range(73, CAGE["z2"] + 1)]
    res["deck_min"] = int(min(deck))
    out("  bridge deck (feet cells z 73..137), all on: min %d median %.0f (want >= 10)" % (min(deck), np.median(deck)))
    for nm, xw, xa in (("west wall", CAGE["x1"] - 1, CAGE["x1"]), ("east wall", CAGE["x2"] + 1, CAGE["x2"])):
        v = [int(L[xa, y, z]) for y in range(40, 105) for z in range(28, 136) if w.get(xw, y, z) not in (None, AIR) and w.get(xa, y, z) in (AIR,) + ("minecraft:light[level=15]",)]
        res[nm] = (min(v), float(np.median(v)))
        out("  %s (y 40..104, z 28..135) faces: %s (want 10..13 near the lights)" % (nm, stats(v)))
    v = [int(L[x, y, CAGE["z1"]]) for y in range(71, 105) for x in range(66, 127) if w.get(x, y, CAGE["z1"] - 1) not in (None, AIR) and w.get(x, y, CAGE["z1"]) == AIR]
    out("  north wall above y 70: %s" % stats(v))
    # the commander
    sx, sz = int(BOOTH_STAND[0]), int(BOOTH_STAND[1])
    fig = [(sx, BOOTH["y0"] + 1 + k, sz) for k in range(4)]
    Lb = states["on_booth"][2]
    res["booth_lit"] = [int(Lb[c]) for c in fig]
    res["booth_dark"] = [int(L[c]) for c in fig]
    out("  commander's cells (feet to head): banks on, booth off %s; booth on %s; all off %s" % (res["booth_dark"], res["booth_lit"], [int(states["off"][2][c]) for c in fig]))
    # emergency lamps still there
    gone = [c for c in EMERGENCY if 56 <= c[0] <= 136 and 18 <= c[2] <= 146 and w.get(*c) != "minecraft:red_stained_glass"]     # (the cage; lamps elsewhere are not this module's business here)
    res["emergency_ok"] = not gone
    out("  emergency lamps all in place: %s %s" % (not gone, gone[:4]))
    return res


def seal_skylight(w):
    """Back every drawn see-through cell (doors, emergency-lamp glass, bars ...) that touches untouched space with one dark opaque
    block, so the open sky of the void world cannot shine in through it."""
    opq = sky_opaque(w)
    open_ = (w.a != 0) & ~opq
    near = np.zeros(open_.shape, bool)
    for ax in range(3):
        for sh in (1, -1):
            s_ = np.roll(open_, sh, axis=ax)
            sl = [slice(None)] * 3
            sl[ax] = slice(0, 1) if sh == 1 else slice(-1, None)
            s_[tuple(sl)] = False
            near |= s_
    cells = (w.a == 0) & near
    w.a[cells] = w._id(WALLM)
    return int(cells.sum())


def verify(w, out=print):
    res = {}
    tab = tables(w)
    bad = validate_palette(w)
    res["bad_blocks"] = bad
    out("palette: %d entries, invalid: %s" % (len(w.palette) - 2, bad if bad else "none"))
    door = [DOORS["cage_door"]["box"]]
    A = lambda n: _local(w, n)
    seen, err = walk_bfs(w, A("start"), tab=tab)
    res["start_to_elevator"] = reaches(seen, A("elevator"))
    res["start_to_elevator_in"] = reaches(seen, A("elevator_in"))
    for n in ("corr_1", "corr_2", "corr_3", "loop_door", "corr_4", "corr_5", "corr_6"):
        res["walk_" + n] = reaches(seen, A(n))
    out("walk start -> elevator: %s (err %s), -> elevator_in %s; waypoints %s" % (
        res["start_to_elevator"], err, res["start_to_elevator_in"],
        {n: res["walk_" + n] for n in ("corr_1", "corr_2", "corr_3", "loop_door", "corr_4", "corr_5", "corr_6")}))
    seen2, err2 = walk_bfs(w, A("dock"), clear_boxes=door, tab=tab)
    for n in ("crossing", "cage_door", "bridge_start", "face", "captain_mark", "scientist_mark", "shield", "gurney_mark", "gurney_in"):
        res["dock_" + n] = reaches(seen2, A(n))
    out("walk dock -> face (door box cleared): %s (err %s); %s" % (res["dock_face"], err2, {k: v for k, v in res.items() if k.startswith("dock_")}))
    seen3, err3 = walk_bfs(w, A("plug_seat"), tab=tab)
    out("plug seat standable: %s" % (err3 is None))
    seen4, err4 = walk_bfs(w, A("pad"), tab=tab)
    out("shaft pad standable: %s, gantry anchor standable: %s" % (err4 is None, walk_bfs(w, A("shaft_top_gantry"), tab=tab)[1] is None))
    leaks = leak_check(w, tab)
    res["leaks"] = len(leaks)
    out("enclosure: %d air cells touch the void/boundary" % len(leaks))
    if len(leaks):
        out("   first leaks: %s" % [tuple(int(v) for v in p) for p in leaks[:12]])
    # ---- every light position must hold its dead lamp or plain air: a hidden light block must never replace part of the giant
    bad_l = []
    for (x, y, z, b) in CAGE_LIGHTS:
        cur = w.get(x, y, z)
        if cur not in ("minecraft:" + LAMP_OFF.replace("minecraft:", ""), AIR, None, "minecraft:black_stained_glass"):
            bad_l.append(((x, y, z), cur))
    hand_all = set(hand_cells(True, (CX, BRIDGE_Y, SHIELD_Z))) | set(hand_cells(False, (CX, BRIDGE_Y, SHIELD_Z)))
    in_hand = [(x, y, z) for (x, y, z, b) in CAGE_LIGHTS + EYE_GLOW if (x, y, z) in hand_all]
    if in_hand:
        bad_l += [(c, "inside a hand version") for c in in_hand]
    res["light_cells_clean"] = not bad_l
    out("light positions all dead lamps or open air: %s%s" % (not bad_l, "" if not bad_l else "  " + str(bad_l[:6])))
    # ---- the head: dimensions, where it stands, what the stop sees of it
    hs = head_stats()
    res["head"] = hs
    pm = partial_masks(w)
    fx, fy, fz = A("face")
    eye = (fx, fy + 1.62, fz)
    out("head: face %d wide x %d tall (chin tip to crown, horn excluded), horn tip %d above the chin, head %d deep; eyes %.1f..%.1f above the stop's eye; "
        "face plane %.1f from the stop" % (hs["width"], hs["height"], hs["height_horn"], hs["depth"], hs["eye_lo"] - eye[1], hs["eye_hi"] - eye[1], fz - FACE_PLANE_Z))
    chin = (96.5, HEAD_Y0, HEAD_ZF + 1 - 2.0)
    tip = (96.5, HEAD_Y0 + hs["height_horn"], HEAD_ZF + 1 - 3.0)

    def elev(p):
        return math.degrees(math.atan2(p[1] - eye[1], eye[2] - p[2]))
    res["span_deg"] = elev(tip) - elev(chin)
    out("vertical angle from the stop's eye: chin tip %.1f deg, horn tip %+.1f deg, span %.1f deg (the anchor pitches %.0f deg up)" % (
        elev(chin), elev(tip), res["span_deg"], -w.anchors["face"]["pitch"]))
    eyes_ok = []
    for cells in (EYES_LEFT, EYES_RIGHT):
        for (x, y, z) in cells:
            okk = False
            for fx_, fy_ in ((0.5, 0.5), (0.25, 0.25), (0.75, 0.25), (0.25, 0.75), (0.75, 0.75)):
                ok, blk = sees(w.a, tab, eye, (x + fx_, y + fy_, z + 0.97), masks=pm)
                okk = okk or ok
            eyes_ok.append(okk)
    res["eyes_visible"] = (sum(eyes_ok), len(eyes_ok))
    out("eyes in line of sight from face: %d of %d cells" % res["eyes_visible"])
    # ---- the commander, shown at BOOTH_SCALE (3.6 tall, 1.8 wide with the arms): clear lines from the stop and the marks to his waist, chest
    # and head, each at three sideways offsets.  STRICT: only air and light blocks let a line through - a chain, a bar or a pane is a
    # crossing (the plain `sees` lets thin things through).
    bx_, by_, bz_ = A("booth")
    res["booth"] = {}
    parts = []
    heights = (("waist", 0.53 * 3.6), ("chest", 0.67 * 3.6), ("head", 0.92 * 3.6))
    for nm in ("face", "captain_mark", "scientist_mark", "shield"):
        a = A(nm)
        e = (a[0], a[1] + 1.62, a[2])
        for lab, dy in heights:
            for off in (-0.6, 0.0, 0.6):
                ok, blk = sees(w.a, tab, e, (bx_ + off, by_ + dy, bz_), masks=pm, transparent_kinds=(0,))
                res["booth"]["%s_%s_%+.1f" % (nm, lab, off)] = ok
                if not ok:
                    parts.append("%s->%s%+.1f blocked by %s at %s" % (nm, lab, off, w.get(*blk) if blk else None, blk))
    out("commander (waist, chest, head; 3 offsets) in strict line of sight from face / captain_mark / scientist_mark / shield: %s%s" % (
        all(res["booth"].values()), "" if all(res["booth"].values()) else "  " + "; ".join(parts[:6])))
    # the booth's place in the view from the stop: distance, elevation, bearing from straight ahead (north), to the middle of the figure
    hd = (bx_, by_ + 0.5 * 3.6, bz_)
    dx_, dy_, dz_ = hd[0] - eye[0], hd[1] - eye[1], eye[2] - hd[2]
    res["booth_dist"] = math.sqrt(dx_ * dx_ + dy_ * dy_ + dz_ * dz_)
    res["booth_elev"] = math.degrees(math.atan2(dy_, math.hypot(dx_, dz_)))
    res["booth_bearing"] = math.degrees(math.atan2(dx_, dz_))
    out("commander from the stop: %.1f blocks line of sight, %.1f deg above the horizontal, %.1f deg to the right of straight ahead "
        "(want 18..24 blocks, 20..30 deg up, <= 30 deg)" % (res["booth_dist"], res["booth_elev"], res["booth_bearing"]))
    res["booth_dist_ok"] = 18.0 <= res["booth_dist"] <= 24.0 and 20.0 <= res["booth_elev"] <= 30.0 and res["booth_bearing"] <= 30.0
    out("booth distance / elevation / bearing within the brief: %s" % res["booth_dist_ok"])
    w_r = hand_swapped(w, True)
    ok_r = all(sees(w_r.a, tab, (A(n)[0], A(n)[1] + 1.62, A(n)[2]), (bx_ + off, by_ + dy, bz_), masks=pm, transparent_kinds=(0,))[0]
               for n in ("face", "captain_mark", "shield") for _, dy in heights for off in (-0.6, 0.0, 0.6))
    res["booth_raised_hand"] = ok_r
    out("... and with the hand raised: %s" % ok_r)
    # how much of him the stop sees over the parapet: samples over the figure's whole body, strict
    vis = []
    for dy in np.arange(0.2, 3.6, 0.2):
        for off in (-0.8, -0.4, 0.0, 0.4, 0.8):
            vis.append(sees(w.a, tab, eye, (bx_ + off, by_ + dy, bz_), masks=pm, transparent_kinds=(0,))[0])
    vis = np.array(vis).reshape(-1, 5).any(axis=1)
    first = next((round(float(d), 1) for d, v in zip(np.arange(0.2, 3.6, 0.2), vis) if v), None)
    res["booth_first_visible"] = first
    out("seen from the stop he is visible from %.1f blocks above his feet upwards (the parapet hides his legs; a 3.6 figure has hips at 1.4)" % (first if first is not None else -1))
    # ---- nothing may stand across the face from the stop: every sample on the face (chin to brow, 12 wide) must be in clear view,
    # or hidden only by the head's own relief (nose ridge, chin prow, brow overhang)
    fv, other = [], []
    for x in np.arange(HEAD_X0 + 4.5, HEAD_X0 + 16.6, 1.0):
        for y in np.arange(HEAD_Y0 + 0.5, HEAD_Y0 + 21.0, 1.5):
            ok, blk = sees(w.a, tab, eye, (x, y, FACE_PLANE_Z - 0.3), masks=pm)
            fv.append(ok)
            if not ok and not (HEAD_X0 <= blk[0] <= HEAD_X0 + 20 and HEAD_Y0 <= blk[1] <= HEAD_Y0 + 40 and HEAD_ZF - 27 <= blk[2] <= HEAD_ZF):
                other.append((round(float(x), 1), round(float(y), 1), blk, w.get(*blk)))
    res["face_clear"] = (sum(fv), len(fv))
    res["face_blocked_by_other"] = len(other)
    out("face samples in clear view from the stop: %d of %d; blocked by anything other than the head's own relief: %d%s" % (
        sum(fv), len(fv), len(other), "" if not other else "  e.g. %s" % other[:4]))
    # ---- skylight: nothing under the open sky of the void world may light the inside
    nf, nc, smp = skylight_check(w)
    res["skylight_flood"], res["skylight_column"] = nf, nc
    out("skylight cap: %d interior cells would receive sky light in a full flood; %d interior cells lie above the first opaque cube "
        "of their (x, z) column (both must be 0)%s" % (nf, nc, "" if not (nf or nc) else "  e.g. %s" % smp))
    sh = SHAFT
    lid = [w.get(x, sh["top"] + 1, z) for x in range(sh["x1"], sh["x2"] + 1) for z in range(sh["z1"], sh["z2"] + 1)]
    res["shaft_lid_opaque"] = all(b not in (None, AIR) for b in lid)
    out("launch shaft lid (y %d) fully filled with solid blocks: %s" % (sh["top"] + 1, res["shaft_lid_opaque"]))
    # ---- block light on the walked route, lights off (as built) and cage lights on
    res["light"] = light_report(w, tab, out)
    res["floodlight"] = verify_light(w, out)
    return res

# ================================================================================================ LIGHT SIMULATION AND MEASURES
N_BANKS = 8                                  # the story's number of banks (tools/story/hq_cage.py)
EYE_POS = (96.5, 55.6, 72.5)                 # the player's eyes at the stop, the distance the story sorts the banks by


def story_banks():
    """The banks as tools/story/hq_cage.py forms them (its Cage._lights, copied): the lights of the cage (x 64..128, z 24..137) that
    are not booth lights; those with z <= 66, y <= 70 and |x - 96| <= 26 are the LAST bank (the face); the rest sorted by distance
    from the stop, farthest first, are cut into N_BANKS - 1 equal banks.  Returns (groups, booth_lights)."""
    booth = {(x, y, z) for (x, y, z, b) in BOOTH_LIGHTS}
    cage = [l for l in CAGE_LIGHTS if (l[0], l[1], l[2]) not in booth and 64 <= l[0] <= 128 and 24 <= l[2] <= 137]
    face = [l for l in cage if l[2] <= 66 and l[1] <= 70 and abs(l[0] - 96) <= 26]
    rest = [l for l in cage if l not in face]
    rest.sort(key=lambda l: -math.dist((l[0] + .5, l[1] + .5, l[2] + .5), EYE_POS))
    per = int(math.ceil(len(rest) / float(N_BANKS - 1)))
    groups = [rest[i * per:(i + 1) * per] for i in range(N_BANKS - 1)] + [face]
    return groups, list(BOOTH_LIGHTS)


def canvas_with(w, lights=(), eyes=False, eye_block=None):
    """A copy of the canvas with the given (x, y, z, block) entries set (and the eye cells lit when eyes)."""
    w2 = World("x", w.origin, w.size)
    w2.a = w.a.copy()
    w2.palette = list(w.palette)
    w2._ix = dict(w._ix)
    for (x, y, z, b) in lights:
        w2.set(x, y, z, b)
    if eyes:
        for (x, y, z) in EYES_LEFT + EYES_RIGHT:
            w2.set(x, y, z, eye_block or EYE_ON)
    return w2


def light_states(w, eyes=True):
    """{'off', 'but_last', 'on', 'on_booth'}: (canvas, tables, block light) as the story will leave the set: nothing on; every bank but the
    last (the face); every bank (the booth stays off); every bank and the booth.  The eyes are lit only in the last two."""
    groups, booth = story_banks()
    first = [l for g in groups[:-1] for l in g]
    allc = first + groups[-1]
    out = {}
    for nm, lights, ey in (("off", [], False), ("but_last", first, False), ("on", allc, False), ("on_eyes", allc, True),
                           ("on_booth", allc + booth, eyes)):
        c = canvas_with(w, lights, ey)
        t = tables(c)
        out[nm] = (c, t, light_map(c, t))
    return out


def giant_faces(w, tab=None, eyes=(), part="head", normals=None):
    """The exposed block faces of the giant that can face the bridge: [(cell, (nx, ny, nz))] for the faces with the given normals (default
    south, up, down and the two sides) that look at open air.  part 'head': the cells of the head (the eye cells left out); 'body':
    the neck, chest and shoulders above the coolant and the pylon fins."""
    tab = tab or tables(w)
    rgb, kind, alpha, emit = tab
    names, _, _ = head_blocks()
    head = {(HEAD_X0 + ix, HEAD_Y0 + iy, HEAD_ZF - iz) for ix, iy, iz in zip(*np.nonzero(names != ""))}
    head -= set(eyes)
    opq = (kind[w.a] == 1)
    if part == "head":
        cells = head
    else:                                          # the neck, chest, shoulders and fins: the sculpture alone (a bare stage), above the coolant
        hand_all = set(hand_cells(True)) | set(hand_cells(False))
        stage = head_stage(True)
        cells = {(int(x), int(y), int(z)) for x, y, z in np.argwhere(stage.a[:, SURF + 1:, :] > 1) if True}
        cells = {(x, y + SURF + 1, z) for (x, y, z) in cells}
        cells -= head
        cells -= hand_all
        cells = {c for c in cells if opq[c]}
    normals = normals or ((0, 0, 1), (0, 1, 0), (0, -1, 0), (1, 0, 0), (-1, 0, 0))
    out = []
    for (x, y, z) in sorted(cells):
        for n in normals:
            q = (x + n[0], y + n[1], z + n[2])
            if q in cells or not w.inside(*q):
                continue
            if w.a[q] != 0 and not opq[q]:
                out.append(((x, y, z), n))
    return out


def visible_points(w, tab, eye, pts, step=0.12, strict=False):
    """Vectorised line of sight from `eye` to each point of pts (n, 3): False where a solid cube (or the filled part of a slab or stair)
    stands between.  Glass, bars and chains count as clear (as in `sees`) unless `strict`: then only air and light blocks are clear."""
    rgb, kind, alpha, emit = tab
    M = partial_masks(w)
    pts = np.asarray(pts, float)
    eye = np.asarray(eye, float)
    d = pts - eye
    L = np.linalg.norm(d, axis=1)
    ok = np.ones(len(pts), bool)
    nmax = int(L.max() / step)
    for i in range(1, nmax):
        t = (i * step) / L
        live = (t < 1.0 - 0.03 / np.maximum(L, 1e-6)) & ok
        if not live.any():
            break
        p = eye + d * t[:, None]
        c = np.floor(p).astype(int)
        c = np.clip(c, 0, np.array(w.a.shape) - 1)
        ids = w.a[c[:, 0], c[:, 1], c[:, 2]]
        solid = ((kind[ids] != 0) if strict else (kind[ids] == 1)) | (ids == 0)
        if solid.any():
            sub = np.clip(np.floor((p - c) * 2).astype(int), 0, 1)
            filled = M[ids, sub[:, 0], sub[:, 1], sub[:, 2]]
            solid &= filled | (ids == 0) | (kind[ids] != 1)
        ok &= ~(live & solid)
    return ok


def visible_faces(w, tab, faces, eyes=EYES_VIEW):
    """The faces (cell, normal) that at least one of `eyes` sees: the point just in front of the face centre must be in line of sight."""
    if not faces:
        return []
    pts = np.array([(c[0] + 0.5 + n[0] * 0.52, c[1] + 0.5 + n[1] * 0.52, c[2] + 0.5 + n[2] * 0.52) for c, n in faces])
    vis = np.zeros(len(faces), bool)
    for e in eyes:
        vis |= visible_points(w, tab, e, pts)
    return [f for f, v in zip(faces, vis) if v]


def face_levels(L, faces):
    """Block light level of each face: the level of the air cell it looks at (for slabs and stairs also the block's own)."""
    return np.array([int(L[c[0] + n[0], c[1] + n[1], c[2] + n[2]]) for c, n in faces], np.int32)


def stats(v):
    v = np.asarray(v)
    if v.size == 0:
        return "n=0"
    return "n=%4d min %2d p5 %4.1f median %4.1f mean %4.1f max %2d" % (v.size, v.min(), np.percentile(v, 5), np.median(v), v.mean(), v.max())


_FACE_SETS = {}


def face_sets(w):
    """The surfaces the story's switch-on is measured on (cached): head_south (every south-facing face of the head), head_vis (every face
    of the head the stop's eyes can see), body_vis (the same for the neck, chest, shoulders and fins)."""
    key = id(w)
    if key not in _FACE_SETS:
        tab = tables(w)
        eyes = EYES_LEFT + EYES_RIGHT
        head_all = giant_faces(w, tab, eyes, "head")
        _FACE_SETS.clear()
        _FACE_SETS[key] = dict(head_south=[f for f in head_all if f[1] == (0, 0, 1)], head_vis=visible_faces(w, tab, head_all),
                               body_vis=visible_faces(w, tab, giant_faces(w, tab, (), "body")))
    return _FACE_SETS[key]


def measure_face(w, out=print, states=None, tag=""):
    """Light levels on the giant's bridge-facing surfaces in each state of the story's switch-on (see light_states)."""
    states = states or light_states(w)
    fs = face_sets(w)
    res = {}
    low = [f for f in fs["head_south"] if f[0][1] <= 70]
    sets = (("head south faces", fs["head_south"]), ("  ... y <= 70 (brow and below)", low), ("head faces seen from the stop", fs["head_vis"]),
            ("neck, chest, fins seen", fs["body_vis"]))
    for nm in ("off", "but_last", "on"):
        L = states[nm][2]
        res[nm] = {}
        for lab, fl in sets:
            v = face_levels(L, fl)
            res[nm][lab.strip()] = v
            out("  %-9s %-32s %s" % (nm, lab, stats(v)))
    return res


def design_wash(w, cap=4, out=print):
    """Choose FACE_WASH: permanent hidden lights (the lights-off light on the face) so that every face of the head the stop sees
    gets as much as `cap` (4) and no more.  Greedy: each candidate cell (a lattice in the air 1 to 8 blocks in front of the head)
    carries the level that puts its nearest face at `cap`; the next one added is the one that lifts the most faces.  `w` must be built
    with _DESIGN[0] and an empty FACE_WASH."""
    import heapq
    from collections import deque
    tab = tables(w)
    rgb, kind, alpha, emit = tab
    fs = face_sets(w)
    faces = {}
    for (c, n) in fs["head_vis"] + fs["head_south"]:
        faces[(c[0] + n[0], c[1] + n[1], c[2] + n[2])] = 1
    qs = list(faces)
    pas = ((kind[w.a] != 1) | partial_flags(w)[w.a]) & (w.a != 0)
    Lw = light_map(w, tab)
    cur = {q: int(Lw[q]) for q in qs}
    cands = [(x, y, z) for x in range(CX - 12, CX + 13, 2) for y in range(46, 74, 2) for z in range(60, 69, 2) if w.get(x, y, z) == AIR]
    cover = {}
    for c in cands:
        dist = {c: 0}
        dq = deque([c])
        while dq:
            p_ = dq.popleft()
            d0 = dist[p_]
            if d0 >= 13:
                continue
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (p_[0] + dx, p_[1] + dy, p_[2] + dz)
                if q not in dist and w.inside(*q) and pas[q]:
                    dist[q] = d0 + 1
                    dq.append(q)
        near = {q: dist[q] for q in qs if q in dist}
        if not near:
            continue
        lvl = min(near.values()) + cap                       # the nearest face gets exactly `cap`
        if lvl > 15:
            continue
        lv = {q: lvl - d for q, d in near.items() if lvl - d > 0}
        if lv:
            cover[c] = (lvl, lv)
    chosen = []
    def gain(c):
        lvl, lv = cover[c]
        return sum(min(v, cap) - min(cur[q], cap) for q, v in lv.items() if v > cur[q] and cur[q] < cap)
    heap = [(-gain(c), c) for c in cover]
    heapq.heapify(heap)
    while heap and len(chosen) < 70:
        g, c = heapq.heappop(heap)
        gg = gain(c)
        if gg <= 2:
            continue
        if heap and gg < -heap[0][0]:
            heapq.heappush(heap, (-gg, c))
            continue
        lvl, lv = cover[c]
        for q, v in lv.items():
            if v > cur[q]:
                cur[q] = v
        chosen.append((c[0], c[1], c[2], lvl))
    vals = np.array([cur[q] for q in qs])
    out("wash: %d lights; the %d faces seen: %s" % (len(chosen), len(qs), stats(vals)))
    return sorted(chosen)


def near_booth(c, reach=10):
    """True for a cell in or close to the commander's balcony: floodlight placed there would light him when only the banks are on."""
    sx, sz = BOOTH_STAND
    return (BOOTH["x1"] - 1 <= c[0] <= BOOTH["x2"] + 1 and BOOTH["y0"] <= c[1] <= BOOTH["y0"] + BOOTH_H + 2 and BOOTH["z1"] - 1 <= c[2] <= BOOTH["z2"] + 1) \
        or abs(c[0] - sx) + abs(c[1] - (BOOTH["y0"] + 3)) + abs(c[2] - sz) <= reach


def design_floods(w, req_head=14, req_inner=13, req_outer=11, req_crown=10, out=print):
    """Choose FLOOD_FACE and FLOOD_CROWN: hidden level-15 light blocks, a greedy cover of every visible face of the giant (head: level
    req_head; neck and inner shoulders |x - 96| <= 14: req_inner; the rest of the shoulders: req_outer) by air cells within reach
    (15 - req blocks through open cells).  `w` must be built with _DESIGN[0] set (no baked lights).  Light already given by the last
    bank's other members (masts, fin lamps) counts.  Returns (face_list, crown_list)."""
    import heapq
    from collections import deque
    tab = tables(w)
    rgb, kind, alpha, emit = tab
    hand_all = set(hand_cells(True, (CX, BRIDGE_Y, SHIELD_Z))) | set(hand_cells(False, (CX, BRIDGE_Y, SHIELD_Z)))
    head = visible_faces(w, tab, giant_faces(w, tab, EYES_LEFT + EYES_RIGHT, "head"))
    body = visible_faces(w, tab, giant_faces(w, tab, (), "body"))
    need = {}
    for (c, n) in giant_faces(w, tab, EYES_LEFT + EYES_RIGHT, "head", normals=((0, 0, 1),)):       # every south face, seen or not: 10
        q = (c[0], c[1], c[2] + 1)
        need[q] = max(need.get(q, 0), req_crown)
    for (c, n) in head:
        q = (c[0] + n[0], c[1] + n[1], c[2] + n[2])
        need[q] = max(need.get(q, 0), req_head if c[1] <= 70 else req_crown)
    for (c, n) in body:
        q = (c[0] + n[0], c[1] + n[1], c[2] + n[2])
        need[q] = max(need.get(q, 0), req_inner if abs(c[0] - CX) <= 14 else req_outer)
    groups, _ = story_banks()
    wl = canvas_with(w, groups[-1])
    L0 = light_map(wl, tables(wl))
    todo = {q: r for q, r in need.items() if L0[q] < r}
    out("design: %d head faces and %d body faces seen, %d air cells to light, %d of them short of their level" % (len(head), len(body), len(need), len(todo)))
    pas = ((kind[w.a] != 1) | partial_flags(w)[w.a]) & (w.a != 0)
    stops = np.array([bool(b) and b.split("[")[0].endswith("tinted_glass") for b in w.palette])
    pas &= ~stops[w.a] | partial_flags(w)[w.a]
    reach = 15 - min(todo.values())
    dil = set()
    for q in todo:
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                for dz in range(-reach, reach + 1):
                    if abs(dx) + abs(dy) + abs(dz) <= reach:
                        dil.add((q[0] + dx, q[1] + dy, q[2] + dz))
    # candidates: the face bank's region (y <= 70) or well above it (y >= 74: the crown bank; lower ones would light the brow early)
    cands = [c for c in dil if w.get(*c) == AIR and abs(c[0] - CX) <= 26 and SURF < c[1] <= 84 and (c[1] <= 70 or c[1] >= 74)
             and 28 <= c[2] <= 66 and c not in hand_all and not near_booth(c)]
    cover = {}
    for c in cands:
        dist = {c: 0}
        dq = deque([c])
        while dq:
            p_ = dq.popleft()
            d0 = dist[p_]
            if d0 >= reach:
                continue
            for dx, dy, dz in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
                q = (p_[0] + dx, p_[1] + dy, p_[2] + dz)
                if q not in dist and w.inside(*q) and pas[q]:
                    dist[q] = d0 + 1
                    dq.append(q)
        cv = {q for q, d in dist.items() if q in todo and d <= 15 - todo[q]}
        if cv:
            cover[c] = cv
    out("design: %d candidate cells, %d of them cover something" % (len(cands), len(cover)))
    uncovered = set(todo)
    chosen = []
    heap = [(-len(v) * (1.0 if (c[1] <= 70) else 0.6), c) for c, v in cover.items()]
    heapq.heapify(heap)
    while uncovered and heap:
        g, c = heapq.heappop(heap)
        gain = len(cover[c] & uncovered) * (1.0 if c[1] <= 70 else 0.6)
        if gain <= 0:
            continue
        if heap and gain < -heap[0][0] - 1e-9:
            heapq.heappush(heap, (-gain, c))
            continue
        chosen.append(c)
        uncovered -= cover[c]
    out("design: %d lights chosen, %d air cells could not be covered: %s" % (len(chosen), len(uncovered), sorted(uncovered)[:8]))
    face_l = sorted(c for c in chosen if c[1] <= 70)
    crown_l = sorted(c for c in chosen if c[1] > 70)
    return face_l, crown_l


def write_flood_data(face_l, crown_l, wash=None):
    """Rewrite the baked FACE_WASH / FLOOD_FACE / FLOOD_CROWN block of this file."""
    path = os.path.abspath(__file__)
    src = open(path, encoding="utf-8").read()
    a = src.index("# <<FLOOD-DATA")
    b = src.index("# FLOOD-DATA>>")

    def fmt(name, cells):
        lines = ["%s = [" % name]
        row = "   "
        for c in cells:
            t = " (" + ", ".join(str(v) for v in c) + "),"
            if len(row) + len(t) > 130:
                lines.append(row)
                row = "   "
            row += t
        lines.append(row)
        lines.append("]")
        return "\n".join(lines)
    wash = list(FACE_WASH) if wash is None else wash
    block = "# <<FLOOD-DATA\n" + fmt("FACE_WASH", wash) + "\n" + fmt("FLOOD_FACE", face_l) + "\n" + fmt("FLOOD_CROWN", crown_l) + "\n"
    open(path, "w", encoding="utf-8").write(src[:a] + block + src[b:])


# ================================================================================================ previews
def hand_swapped(w, raised):
    """A copy of the canvas with the other hand version cleared and this one placed (what the story does when debris falls)."""
    w2 = World("h", w.origin, w.size)
    w2.a = w.a.copy()
    w2.palette = list(w.palette)
    w2._ix = dict(w._ix)
    for rz in (False, True):
        x1, y1, z1, x2, y2, z2 = hand_bbox(rz)
        for (x, y, z) in hand_cells(rz, (CX, BRIDGE_Y, SHIELD_Z)):
            w2.set(x, y, z, "minecraft:" + LIQUID if y <= SURF else AIR)
    hand(w2, CX, BRIDGE_Y, SHIELD_Z, raised)
    return w2


def lights_on(w, eyes=True, booth=False):
    """A copy of the canvas with every cage light and the eyes switched on (what the story will do; the booth has its own switch)."""
    bl = {(x, y, z) for (x, y, z, b) in BOOTH_LIGHTS}
    return canvas_with(w, [l for l in CAGE_LIGHTS if booth or (l[0], l[1], l[2]) not in bl], eyes)


def with_standin(w):
    """A copy with a stand-in for the commander at the booth anchor: his size at BOOTH_SCALE, 1.8 wide and 3.6 tall (body 3 blocks, face 1);
    pale on purpose, so that the light on him shows (the real man wears a dark suit)."""
    w2 = canvas_with(w, [])
    sx, sz = int(BOOTH_STAND[0]), int(BOOTH_STAND[1])
    for dx in (-1, 0):
        for dy in range(3):
            w2.set(sx + dx, BOOTH["y0"] + 1 + dy, sz, "light_gray_concrete")
        w2.set(sx + dx, BOOTH["y0"] + 4, sz, "white_terracotta")
    return w2


CAGE_CROP = ((56, 0, 18), (136, 118, 146))     # the part of the set rendered at half-block resolution (stairs and slabs show)


def gaze(w, name, dist=12.0):
    """Eye position and a point straight ahead along the anchor's yaw and pitch (Minecraft: pitch > 0 looks down)."""
    a = w.anchors[name]
    p = (a["x"] - w.origin[0], a["y"] - w.origin[1] + 1.62, a["z"] - w.origin[2])
    yaw, pit = math.radians(a["yaw"]), math.radians(a["pitch"])
    d = (-math.sin(yaw) * math.cos(pit), -math.sin(pit), math.cos(yaw) * math.cos(pit))
    return p, tuple(p[i] + d[i] * dist for i in range(3))


def head_stage(full):
    """A bare coolant stage carrying only the giant (full) or only the head (head-on views of its form)."""
    ws = World("stage", (0, 0, 0), SIZE)
    if full:
        box(ws, 64, FLOOR_C, 24, 128, FLOOR_C, 100, LIQUID_BED)
        box(ws, 64, FLOOR_C + 1, 24, 128, SURF, 100, LIQUID)
        giant_full(ws)
    else:
        giant_upper(ws)
    return ws


def render_all(w, outdir, quick=False):
    os.makedirs(outdir, exist_ok=True)
    tab = tables(w)
    w_on = lights_on(w)
    tab_on = tables(w_on)
    L_off = light_map(w, tab)
    L_on = light_map(w_on, tab_on)
    A = lambda n: _local(w, n)
    done = []

    def shot(name, ww, tb, LL, eye, target, fov=85, size=(960, 540), ortho=None, ambient=0.5, sky=(0, 0, 0), fine=True):
        path = os.path.join(outdir, name + ".png")
        if fine:
            raycast_fine(ww, tb, path, eye, target, CAGE_CROP, light=LL, fov=fov, size=size, ortho=ortho, ambient=ambient, sky=sky)
        else:
            raycast(ww.a, tb, path, eye, target, fov=fov, size=size, ortho=ortho, light=LL, ambient=ambient, sky=sky)
        done.append(path)
        return path

    # ----- the head, flat shaded orthographic and perspective, on a bare coolant stage
    wh, ws = head_stage(False), head_stage(True)
    th, ts = tables(wh), tables(ws)
    cx, cy, cz = 96.5, HEAD_Y0 + 17.0, 50.0
    sky = (34, 34, 40)
    shot("head_front", wh, th, None, (cx, cy, cz + 60), (cx, cy, cz), size=(760, 760), ortho=17, sky=sky)
    shot("head_side", wh, th, None, (cx + 60, cy, cz), (cx, cy, cz), size=(760, 760), ortho=17, sky=sky)
    shot("head_threequarter", ws, ts, None, (cx + 26, cy + 4, cz + 34), (cx, cy - 2, cz + 6), fov=42, size=(760, 760), sky=sky)
    shot("head_threequarter_low", ws, ts, None, (cx - 24, cy - 10, cz + 30), (cx, cy + 2, cz + 6), fov=48, size=(760, 760), sky=sky)
    shot("head_and_giant", ws, ts, None, (cx + 40, cy + 18, cz + 62), (cx, cy - 6, cz), fov=60, size=(760, 760), sky=sky)
    # ----- the cage from the player's places, in the story's states (off / every bank but the face / all on, eyes lit; the booth on with the
    # commander's stand-in).  75 degrees vertical, as the game's client the frames were shot with
    eye, ahead = gaze(w, "face")
    st = light_states(w)
    S_off, S_bl, S_on, S_ed, S_ob = st["off"], st["but_last"], st["on_eyes"], st["on"], st["on_booth"]
    ws_ = with_standin(w)
    groups, booth_l = story_banks()
    allc = [l for g in groups for l in g]
    w_b = canvas_with(ws_, allc + booth_l, True)
    t_b = tables(w_b)
    L_b = light_map(w_b, t_b)
    w_s = with_standin(w)
    t_s = tables(w_s)
    L_s = light_map(w_s, t_s)
    bst = A("booth")
    ctr = (BOOTH_STAND[0], bst[1] + 1.8, BOOTH_STAND[1])
    for nm, (cv, tb, LL) in (("off", S_off), ("but_last", S_bl), ("on", S_on)):
        shot("cage_face_%s" % nm, cv, tb, LL, eye, ahead, fov=75)
        e_up, a_up = gaze(w, "face")
        shot("cage_face_up_%s" % nm, cv, tb, LL, e_up, (e_up[0], e_up[1] + 10 * math.sin(math.radians(35)), e_up[2] - 10 * math.cos(math.radians(35))), fov=75)
        shot("cage_bridge_start_%s" % nm, cv, tb, LL, (96.5, 55.62, 134), (96.5, 58, 60), fov=75)
    shot("cage_face_on_eyes_dark", S_ed[0], S_ed[1], S_ed[2], eye, ahead, fov=75)
    shot("cage_eyes_close_on", S_on[0], S_on[1], S_on[2], eye, (96.5, 62.5, 58.5), fov=40)
    shot("cage_booth_view_off", w_s, t_s, L_s, eye, ctr, fov=60)
    shot("cage_booth_view_banks_on", canvas_with(w_s, allc, True), tables(canvas_with(w_s, allc, True)), light_map(canvas_with(w_s, allc, True), tables(canvas_with(w_s, allc, True))), eye, ctr, fov=60)
    shot("cage_booth_view_on", w_b, t_b, L_b, eye, ctr, fov=60)
    shot("cage_booth_standin_zoom_on", w_b, t_b, L_b, eye, ctr, fov=25)
    shot("cage_face_and_booth_on", w_b, t_b, L_b, eye, (100.5, 61.0, 62.0), fov=75)
    shot("cage_booth_from_marks_on", w_b, t_b, L_b, (94.5, 55.62, 76.5), ctr, fov=60)
    shot("cage_booth_close_front", w_b, t_b, L_b, (107.0, 62.5, 69.0), (107.0, 65.0, 53.0), fov=60)
    shot("cage_booth_side", w_b, t_b, L_b, (121.0, 62.0, 72.0), (107.0, 65.0, 53.0), fov=60)
    e2, _ = gaze(w, "shield")
    shot("cage_shield_view_on", w_b, t_b, L_b, e2, ctr, fov=75)
    e3, a3 = gaze(w, "captain_mark")
    shot("cage_captain_view_on", w_b, t_b, L_b, e3, (100.0, 66.0, 50.0), fov=75)
    eg, _ = gaze(w, "gurney_mark")
    for nm, (cv, tb, LL) in (("off", S_off), ("on", S_on)):
        shot("cage_gurney_mark_head_%s" % nm, cv, tb, LL, eg, (96.5, 62.0, 50.0), fov=75)
        shot("cage_gurney_mark_east_%s" % nm, cv, tb, LL, eg, (128.0, 55.6, eg[2]), fov=75)
    shot("cage_gurney_door_on", S_on[0], S_on[1], S_on[2], (70, 55.6, GURNEY_Z + 1.5), (110, 56, GURNEY_Z + 1.5), fov=75)
    shot("cage_wall_west_lights_off", w, tab, L_off, (96.5, 55.62, 90), (64, 52, 80), fov=75)
    shot("cage_wall_east_lights_on", S_on[0], S_on[1], S_on[2], (96.5, 55.62, 90), (128, 52, 80), fov=75)
    shot("cage_lake_lights_off", w, tab, L_off, (96.5, 55.62, 80), (96.5, 36, 62), fov=75)
    shot("cage_overview_on", S_on[0], S_on[1], S_on[2], (125, 98, 134), (92, 56, 56), fov=95)
    shot("cage_overview_from_hand", S_on[0], S_on[1], S_on[2], (70, 80, 125), (100, 50, 50), fov=95)
    w_eg = canvas_with(w, list(EYE_GLOW), True)                 # only the eyes (and their optional glow) lit, cage lights off
    shot("cage_face_eyes_only_glow", w_eg, tables(w_eg), light_map(w_eg, tables(w_eg)), eye, ahead, fov=75)
    # ----- the hand, lowered and raised
    for nm, rz in (("hand_lowered", False), ("hand_raised", True)):
        wh_ = hand_swapped(w_on, rz)
        th_ = tables(wh_)
        Lh = light_map(wh_, th_)
        shot(nm + "_from_bridge", wh_, th_, Lh, (96.5, 55.62, SHIELD_Z + 17), (91, 56, SHIELD_Z - 3), fov=85)
        shot(nm + "_from_shield_up", wh_, th_, Lh, (96.5, 55.62, SHIELD_Z + 0.5), (96.5, 63, SHIELD_Z + 1.5), fov=100)
        shot(nm + "_side", wh_, th_, Lh, (124, 60, SHIELD_Z + 25), (92, 52, SHIELD_Z - 3), fov=80)
        shot(nm + "_under", wh_, th_, Lh, (96.5, 55.62, SHIELD_Z + 0.5), (96.5, 64, SHIELD_Z + 0.5), fov=100)
    # ----- B
    shot("flood_dock_view", w, tab, L_off, (15.5, 55.6, 160.5), (60, 52, 160.5), fov=100, fine=False)
    shot("flood_crossing_view", w, tab, L_off, (60.5, 55.6, 160.5), (110, 54, 150), fov=100, fine=False)
    shot("flood_door_view", w, tab, L_off, (96.5, 55.6, 156.0), (96.5, 56, 140), fov=100, fine=False)
    # ----- A
    for nm, eyes_, tgt, fv in (("corr_start", A("start"), (150, 133, 160.5), 95), ("corr_c1", A("corr_1"), (130, 133, 160.5), 95),
                               ("corr_walkway", A("corr_2"), (100, 133, 160.5), 95), ("corr_loop_door", gaze(w, "loop_door")[0], gaze(w, "loop_door")[1], 100),
                               ("corr_escalator_top", (86, 133, 160.5), (50, 120, 160.5), 100), ("corr_escalator_bottom", (28, 109, 160.5), (60, 125, 160.5), 100),
                               ("corr_elevator", (22, 109, 160.5), (6, 108, 160.5), 100)):
        shot(nm, w, tab, L_off, (eyes_[0], eyes_[1] + (1.62 if nm.startswith("corr_") and len(eyes_) == 3 and eyes_[1] in (131, 107) else 0), eyes_[2]), tgt, fov=fv, fine=False)
    # ----- D
    p = A("plug_seat")
    shot("plug_seat_view", w, tab, L_off, (p[0], p[1] + 1.0, p[2]), (p[0], p[1] + 1.2, 4), fov=100, fine=False)
    shot("plug_overview", w, tab, L_off, (30.5, 12.5, 15.0), (30.5, 11.5, 5), fov=90, fine=False)
    q = A("pad")
    shot("shaft_pad_up", w, tab, L_off, (q[0], q[1] + 1.6, q[2]), (q[0], 120, q[2] + 0.5), fov=100, fine=False)
    shot("shaft_overview", w, tab, L_off, (q[0] - 6, 100, q[2] - 6), (q[0] + 4, 60, q[2] + 4), fov=80, size=(540, 960), fine=False)
    # ----- plan views and slices through the cage
    from voxel import preview
    for nm, ax_, at in (("plan_top", "y", None), ("plan_y135_corridors", "y", 137), ("plan_y110_lower_level", "y", 113), ("plan_y56_bridge_level", "y", 56),
                       ("plan_y20_floor", "y", 20), ("plan_y100_cranes", "y", 105), ("slice_x96_bridge_axis", "x", 96), ("slice_z160_strip", "z", 160),
                       ("slice_x30_plug_row", "x", 30), ("slice_x9_shaft", "x", 9), ("slice_z%d_gurney" % (GURNEY_Z + 1), "z", GURNEY_Z + 1)):
        path = os.path.join(outdir, nm + ".png")
        preview(w, path, ax_, at)
        done.append(path)
    return done

def contact_sheet(paths, out, cols=3, tw=520):
    from PIL import Image
    ims = [Image.open(p).convert("RGB") for p in paths]
    ims = [im.resize((tw, int(im.height * tw / im.width))) for im in ims]
    rows = (len(ims) + cols - 1) // cols
    th = max(im.height for im in ims)
    sheet = Image.new("RGB", (tw * cols, th * rows))
    for i, im in enumerate(ims):
        sheet.paste(im, ((i % cols) * tw, (i // cols) * th))
    sheet.save(out)


def main():
    import layout
    quick = "--quick" in sys.argv
    o, s = layout.SETS["hq"]
    if "--design" in sys.argv:                  # bake FACE_WASH, FLOOD_FACE and FLOOD_CROWN into this file (see design_wash, design_floods)
        _DESIGN[0] = True
        FACE_WASH.clear()
        wd = World("hq", o, s)
        build(wd)
        wash = design_wash(wd)
        FACE_WASH[:] = wash
        wd = World("hq", o, s)
        build(wd)
        f_, c_ = design_floods(wd)
        write_flood_data(f_, c_, wash)
        print("baked %d wash lights, %d face lights and %d crown lights into %s" % (len(wash), len(f_), len(c_), os.path.abspath(__file__)))
        return None
    w = World("hq", o, s)
    build(w)
    res = verify(w)
    print("hand boxes (local x1,y1,z1,x2,y2,z2): lowered %s raised %s" % (HAND["lowered"], HAND["raised"]))
    print("eyes left %s" % EYES_LEFT)
    print("eyes right %s" % EYES_RIGHT)
    print("cage lights: %d blocks, booth lights %d, emergency lamps %d (level %d), run-lights %d, eye glow %d; eye cells %d + %d" % (
        len(CAGE_LIGHTS), len(BOOTH_LIGHTS), len(EMERGENCY), EMERGENCY_LEVEL, len(RUN_LIGHTS), len(EYE_GLOW), len(EYES_LEFT), len(EYES_RIGHT)))
    tab = tables(w)
    w_on = lights_on(w)
    L_off = light_map(w, tab)
    L_on = light_map(w_on, tables(w_on))
    A_ = lambda n: _local(w, n)
    cells_adj = [(x, y, z + 1) for (x, y, z) in EYES_LEFT + EYES_RIGHT]
    print("  light on the air cells in front of the eyes: off %s on %s" % (sorted(set(int(L_off[c]) for c in cells_adj)), sorted(set(int(L_on[c]) for c in cells_adj))))
    # the commander seen from along the bridge
    bst = A_("booth")
    for zz in (80, 100, 120):
        eye = (96.5, 55.62, zz)
        ok_c = all(sees(w.a, tab, eye, (bst[0], bst[1] + dy, bst[2]), transparent_kinds=(0,))[0] for dy in (1.9, 2.4, 3.3))
        print("  commander (waist, chest, head at scale 2) in strict line of sight from the bridge at z=%d: %s" % (zz, ok_c))
    for nm, pt in (("front of head", (96, 60, 61)), ("chin", (96, 54, 61)), ("bridge_start", (96, 54, 134)), ("bridge_mid", (96, 54, 100)),
                   ("face stop", (96, 54, 72)), ("booth floor", (111, 63, 55)), ("commander", (111, 64, 55)), ("chin front", (96, 50, 62)), ("shield", (96, 54, 78)), ("dock", (15, 54, 160)),
                   ("crossing", (60, 54, 160)), ("corridor", (160, 131, 160)), ("escalator mid", (55, 120, 160)), ("plug seat", (30, 12, 11)),
                   ("shaft pad", (9, 5, 9)), ("shaft mid", (9, 80, 9))):
        print("  light %-18s off %2d  on %2d" % (nm, L_off[pt], L_on[pt]))
    outdir = os.path.join(os.path.dirname(HERE), "preview", "hq")
    done = render_all(w, outdir, quick)
    print("wrote", len(done), "previews to", outdir)
    for nm, names in (("sheet_head", ["head_front", "head_side", "head_threequarter", "head_threequarter_low"]),
                      ("sheet_cage", ["cage_face_off", "cage_face_on", "cage_bridge_start_on", "cage_booth_view_on"]),
                      ("sheet_hands", ["hand_lowered_from_bridge", "hand_raised_from_bridge", "hand_lowered_side", "hand_raised_side"])):
        contact_sheet([os.path.join(outdir, n + ".png") for n in names], os.path.join(outdir, nm + ".png"), cols=2, tw=640)
    print("anchors:")
    for k in sorted(w.anchors):
        a = w.anchors[k]
        print("  %-16s local (%.1f, %.1f, %.1f) yaw %s" % (k, a["x"] - o[0], a["y"] - o[1], a["z"] - o[2], a["yaw"]))
    return w


if __name__ == "__main__":
    main()
