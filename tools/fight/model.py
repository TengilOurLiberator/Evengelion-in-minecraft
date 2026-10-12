"""The Angel: a parametric skeleton of boxes.

Units: the model is 100 units tall, feet at y = 0, x to the monster's left (east when it faces south), y up,
z forward.  `build()` makes the part list once; `pose_boxes(pose)` runs forward kinematics for a pose and returns
one entry per part: centre, half-size, rotation matrix.  The datapack generator turns those into display-entity
transformations (scaled by height/100); the previewer in preview.py draws the same boxes.

A pose is a dict  bone -> (fwd, side, twist [, dx, dy, dz])  in degrees / model units, plus a few scalar keys:
    "puff"   chest breathing (fraction, grows the chest boxes)
    "core"   core size multiplier
    "eyes"   1 when the eyes glow (only used by the generator for the eye block)
    "jawo"   jaw opening (degrees)
    "curlL" / "curlR"  finger curl in degrees (first joint; the second joint curls 1.4 times as far)
`fwd` swings the bone forward in the sagittal plane (a hanging limb moves toward +z), `side` swings it sideways
(positive = toward +x), `twist` turns it about its own long axis / the vertical.
"""
import math
import sys
import numpy as np

# ---------------------------------------------------------------- blocks used (name -> preview colour, glow)
SKIN = "minecraft:warped_planks"         # the skin: a dark teal, a little lighter and more saturated than dark_prismarine
RIM = "minecraft:white_concrete"         # pale moonlight rim on the upper edges (thin strips)
GLOW = "minecraft:red_concrete"          # emissive red around the core
VEIL = "minecraft:red_stained_glass"     # the soft red glow of the core falling on the chest and arms
ORANGE_GLASS = "minecraft:orange_stained_glass"
DARK = "minecraft:black_concrete"        # joints, hump, hands, feet, eye sockets
BONE = "minecraft:bone_block"            # shoulder plates, ribs, mask
CORE = "minecraft:red_concrete"          # the core
CORE_CRACKED = "minecraft:magma_block"
CRACK = "minecraft:white_concrete"      # the slivers of light that open across the core while it is being broken (the wrap)
EYE_OFF = "minecraft:black_concrete"
EYE_ON = "minecraft:glowstone"

# display brightness (block light, sky light) of each kind of block; a part's own `light` overrides it (an int or a pair)
BRIGHT = {SKIN: (8, 10), DARK: (5, 7), BONE: (15, 15), RIM: (8, 11)}
COLORS = {
    SKIN: (43, 105, 99), DARK: (12, 14, 18), BONE: (226, 220, 196), CORE: (235, 40, 34),
    "minecraft:glowstone": (255, 214, 120), "minecraft:magma_block": (200, 80, 20),
    "minecraft:red_stained_glass": (255, 70, 60), RIM: (207, 213, 214), GLOW: (240, 50, 40),
    ORANGE_GLASS: (255, 160, 60),
}

# ---------------------------------------------------------------- skeleton: bone -> (parent, pivot in parent frame)
BONES = {
    "root": (None, (0, 0, 0)),
    "hips": ("root", (0, 50, 0)),
    "thighL": ("hips", (6.0, -2.5, 0)), "thighR": ("hips", (-6.0, -2.5, 0)),
    "shinL": ("thighL", (0, -24, 0.0)), "shinR": ("thighR", (0, -24, 0.0)),
    "footL": ("shinL", (0, -24, 0.0)), "footR": ("shinR", (0, -24, 0.0)),
    "spine": ("hips", (0, 4, 0)),
    "chest": ("spine", (0, 10, 0)),
    "jaw": ("chest", (0, 16.4, 8.6)),
    "shoulderL": ("chest", (14.5, 21.5, 0)), "shoulderR": ("chest", (-14.5, 21.5, 0)),
    "uarmL": ("shoulderL", (1.0, -1.0, 0)), "uarmR": ("shoulderR", (-1.0, -1.0, 0)),
    "farmL": ("uarmL", (0, -26, 0)), "farmR": ("uarmR", (0, -26, 0)),
    "handL": ("farmL", (0, -30, 0)), "handR": ("farmR", (0, -30, 0)),
}
for s in ("L", "R"):
    for i, fx in enumerate((-2.0, 0.0, 2.0)):
        BONES[f"f{i}a{s}"] = (f"hand{s}", (fx, -5.0, 0.0))
        BONES[f"f{i}b{s}"] = (f"f{i}a{s}", (0, -8.5, 0))

# ---------------------------------------------------------------- the parts
# (name, bone, centre (in bone frame), size, block, rot (fwd, side, twist) of the box itself, flags)
PARTS = []


def P(name, bone, c, size, block=SKIN, rot=(0, 0, 0), tag=None, light=None):
    PARTS.append(dict(name=name, bone=bone, c=c, size=size, block=block, rot=rot, tag=tag, light=light))


def mirror(name, bone, c, size, block=SKIN, rot=(0, 0, 0), tag=None, light=None):
    """Adds a left (+x) and a right (-x) part; bone names end in L / R."""
    P(name + "L", bone + "L", c, size, block, rot, tag, light)
    P(name + "R", bone + "R", (-c[0], c[1], c[2]), size, block, (rot[0], -rot[1], -rot[2]), tag, light)


def build():
    PARTS.clear()
    # --- legs: narrow, long, digitigrade-ish knee
    P("pelvis", "hips", (0, 0, 0), (15, 8, 9), DARK)
    mirror("thigh", "thigh", (0, -12.3, 0.2), (6.4, 25.5, 7.6), SKIN)
    mirror("knee", "shin", (0, 1.2, 3.4), (3.6, 4.0, 3.0), BONE, rot=(25, 0, 0))
    mirror("shin", "shin", (0, -11.5, -0.4), (4.4, 25.0, 4.8), SKIN)
    mirror("foot", "foot", (0, -1.6, 4.2), (5.4, 3.2, 12.0), DARK)
    for i, dx in enumerate((-1.8, 0.0, 1.8)):
        P(f"toeL{i}", "footL", (dx, -1.9, 11.2), (1.5, 1.5, 4.8), BONE, rot=(-6, 0, dx * 3))
        P(f"toeR{i}", "footR", (dx, -1.9, 11.2), (1.5, 1.5, 4.8), BONE, rot=(-6, 0, dx * 3))
    # --- trunk: gaunt, taller than wide, broad at the shoulders
    P("abdomen", "spine", (0, 4.8, 0), (9.5, 10.5, 7.2), SKIN)
    for i, y in enumerate((2.5, 5.7, 8.9)):
        P(f"abrib{i}", "spine", (0, y, 3.9), (8.2 - 0.6 * i, 1.0, 1.0), BONE)
        P(f"abribL{i}", "spine", (4.5 - 0.3 * i, y, 2.6), (1.0, 1.0, 3.2), BONE)
        P(f"abribR{i}", "spine", (-4.5 + 0.3 * i, y, 2.6), (1.0, 1.0, 3.2), BONE)
    mirror("ankle", "shin", (0, -22.4, -3.6), (1.6, 1.6, 5.0), BONE, rot=(25, 0, 0))
    P("lumbar", "spine", (0, 5.0, -3.6), (3.0, 9.0, 2.4), BONE)
    P("chestLo", "chest", (0, 4.6, 0.3), (13.5, 9.6, 9.4), SKIN)
    P("chestMid", "chest", (0, 12.6, 0.4), (19.5, 8.4, 10.4), SKIN)
    P("chestHi", "chest", (0, 19.2, 0.0), (28.5, 7.2, 10.4), SKIN)
    P("hump", "chest", (0, 25.6, -3.2), (12.5, 6.4, 7.4), DARK)
    P("hump2", "chest", (0, 28.4, -4.4), (7.0, 3.6, 5.0), DARK)
    for i, (y, h) in enumerate(((16.0, 8.5), (22.0, 6.5), (27.5, 4.5))):
        P(f"spike{i}", "chest", (0, y + 2.0, -7.4 - i * 1.0), (1.6, h, 1.6), BONE, rot=(-32 - 6 * i, 0, 0))
    # --- the mask: a bird skull set into the upper chest, where a head would be
    P("skull", "chest", (0, 20.6, 6.4), (14.0, 12.4, 6.2), BONE)
    P("brow", "chest", (0, 26.6, 8.6), (15.0, 2.0, 3.0), BONE, rot=(-8, 0, 0))
    P("crown", "chest", (0, 28.2, 6.0), (8.0, 2.0, 4.6), BONE, rot=(-18, 0, 0))
    P("crest", "chest", (0, 30.2, 4.6), (2.4, 3.6, 5.6), BONE, rot=(-30, 0, 0))
    P("beak", "chest", (0, 17.4, 12.8), (5.6, 5.8, 9.5), BONE, rot=(-2, 0, 0))
    P("beakTip", "chest", (0, 15.1, 19.4), (3.0, 3.2, 5.8), BONE, rot=(-9, 0, 0))
    P("beakHook", "chest", (0, 12.8, 22.4), (1.8, 2.6, 2.6), BONE, rot=(-24, 0, 0))
    P("jaw", "jaw", (0, -1.0, 5.2), (3.8, 1.7, 9.8), BONE, rot=(0, 0, 0), tag="jaw")
    P("cheekL", "chest", (7.6, 18.2, 8.0), (1.6, 7.6, 4.2), BONE, rot=(0, 10, 0))
    P("cheekR", "chest", (-7.6, 18.2, 8.0), (1.6, 7.6, 4.2), BONE, rot=(0, -10, 0))
    P("eyeL", "chest", (3.9, 21.8, 9.55), (4.4, 5.2, 0.9), EYE_OFF, rot=(0, -20, 0), tag="eye", light=15)
    P("eyeR", "chest", (-3.9, 21.8, 9.55), (4.4, 5.2, 0.9), EYE_OFF, rot=(0, 20, 0), tag="eye", light=15)
    # --- the core: a red sphere (cubes turned against each other) in the solar plexus, in a dark socket
    cc = (0, 4.8, 6.6)
    P("coreA", "chest", cc, (5.6, 5.6, 5.6), CORE, tag="core", light=15)
    P("coreB", "chest", cc, (5.6, 5.6, 5.6), CORE, rot=(0, 45, 0), tag="core", light=15)
    P("coreC", "chest", cc, (5.6, 5.6, 5.6), CORE, rot=(45, 0, 0), tag="core", light=15)
    P("coreD", "chest", cc, (5.6, 5.6, 5.6), CORE, rot=(0, 0, 45), tag="core", light=15)
    P("coreHalo", "chest", cc, (9.0, 9.0, 3.0), "minecraft:red_stained_glass", rot=(0, 45, 0), tag="halo", light=15)
    P("socketU", "chest", (0, 9.7, 5.8), (9.0, 1.6, 2.6), DARK)
    P("socketD", "chest", (0, 1.0, 5.8), (9.0, 1.6, 2.6), DARK)
    P("socketL", "chest", (5.2, 5.4, 5.8), (1.6, 8.0, 2.6), DARK)
    P("socketR", "chest", (-5.2, 5.4, 5.8), (1.6, 8.0, 2.6), DARK)
    # --- rib plates: pale bands across the chest, either side of the mask and core
    for i, y in enumerate((3.0, 6.6, 10.2, 13.8, 17.4, 21.0)):
        w = 5.4 - 0.15 * i
        x = 9.6 - 0.2 * i
        for sgn, nm in ((1, "L"), (-1, "R")):
            P(f"rib{i}{nm}", "chest", (sgn * x, y, 4.9 - 0.15 * i), (w, 1.55, 1.7), BONE, rot=(0, 0, -sgn * 24))
    for i, y in enumerate((5.0, 11.0, 17.0)):
        for sgn, nm in ((1, "L"), (-1, "R")):
            P(f"rside{i}{nm}", "chest", (sgn * (10.4 + 0.5 * i), y, 1.2), (1.4, 1.6, 7.2), BONE, rot=(0, 0, sgn * 6))
    # --- shoulders: big pale plates, spikes
    mirror("pauld", "shoulder", (4.6, 1.4, 0.2), (14.0, 2.6, 13.0), BONE, rot=(0, -24, 0))
    mirror("pauldOut", "shoulder", (12.6, -4.2, 0.2), (7.5, 2.4, 11.5), BONE, rot=(0, -52, 0))
    mirror("pauldLip", "shoulder", (16.6, -8.4, 0.2), (3.2, 2.2, 10.0), BONE, rot=(0, -76, 0))
    mirror("pauldSp", "shoulder", (5.6, 4.8, -3.6), (2.0, 7.0, 2.0), BONE, rot=(-34, -22, 0))
    mirror("shRidge", "shoulder", (-3.4, 3.4, 5.0), (8.4, 1.6, 2.4), BONE, rot=(8, 16, 0))
    # --- arms: very long, very thin, hanging to the knees
    mirror("uarm", "uarm", (0, -13.2, 0), (3.5, 27.0, 3.9), SKIN)
    mirror("elbow", "farm", (0, 0.4, 0), (4.4, 4.4, 4.4), DARK)
    mirror("elbowSp", "farm", (0, 1.0, -3.4), (1.7, 1.7, 5.4), BONE, rot=(12, 0, 0))
    mirror("farm", "farm", (0, -15.3, 0.2), (2.8, 31.0, 3.2), SKIN)
    mirror("palm", "hand", (0, -2.5, 0), (5.6, 5.4, 2.0), DARK)
    for s in ("L", "R"):
        for i in range(3):
            P(f"f{i}a{s}", f"f{i}a{s}", (0, -4.4, 0), (1.25, 9.4, 1.25), DARK)
            P(f"f{i}b{s}", f"f{i}b{s}", (0, -4.2, 0), (1.0, 8.9, 1.0), BONE)
    # ---- night presence (added last so that the part numbers of everything above stay the same)
    # pale rim light on the upper edges: thin strips on top of the chest, the hump, the hips, and along the outer edge
    # of the arms and thighs
    P("rimChest", "chest", (0, 22.95, 0.0), (24.0, 0.45, 9.4), RIM)
    P("rimHump", "chest", (0, 28.95, -3.2), (11.8, 0.45, 6.8), RIM)
    P("rimPelvis", "hips", (0, 4.15, 0), (14.0, 0.4, 8.0), RIM)
    mirror("rimUarm", "uarm", (1.85, -13.0, 0), (0.45, 26.0, 1.3), RIM)
    mirror("rimFarm", "farm", (1.5, -15.3, 0.2), (0.4, 29.0, 1.2), RIM)
    mirror("rimThigh", "thigh", (3.35, -12.3, 0.2), (0.45, 24.5, 1.5), RIM)
    # the core lights its surroundings: a frame of emissive red strips just in front of the socket ...
    P("coreGlowU", "chest", (0, 9.4, 7.5), (8.6, 0.8, 0.9), GLOW, tag="coreglow", light=15)
    P("coreGlowD", "chest", (0, 0.4, 7.5), (8.6, 0.8, 0.9), GLOW, tag="coreglow", light=15)
    P("coreGlowL", "chest", (4.7, 4.9, 7.5), (0.8, 8.6, 0.9), GLOW, tag="coreglow", light=15)
    P("coreGlowR", "chest", (-4.7, 4.9, 7.5), (0.8, 8.6, 0.9), GLOW, tag="coreglow", light=15)
    # ... and a soft red veil of glass over the chest and on the inner side of the upper arms
    P("veilChest", "chest", (0, 8.0, 6.1), (17.5, 13.5, 0.4), VEIL, tag="veil", light=13)
    mirror("veilUarm", "uarm", (-2.0, -9.5, 0.2), (0.4, 14.0, 4.6), VEIL, tag="veil", light=11)
    # ---- the eyes blaze while it charges: bigger emissive boxes that grow with the pose key "eyeg"
    P("eyeGlowL", "chest", (3.9, 21.8, 10.1), (4.8, 5.6, 1.6), EYE_ON, rot=(0, -20, 0), tag="eyeglow", light=15)
    P("eyeGlowR", "chest", (-3.9, 21.8, 10.1), (4.8, 5.6, 1.6), EYE_ON, rot=(0, 20, 0), tag="eyeglow", light=15)
    P("eyeHaloL", "chest", (3.9, 21.8, 11.2), (7.4, 8.4, 1.0), ORANGE_GLASS, rot=(0, -20, 0), tag="eyeglow", light=15)
    P("eyeHaloR", "chest", (-3.9, 21.8, 11.2), (7.4, 8.4, 1.0), ORANGE_GLASS, rot=(0, 20, 0), tag="eyeglow", light=15)
    # ---- the gathering glow in front of the mask (pose key "gather" = its size); on the hips frame so that it
    # stays straight ahead of the mask at the height of the mask, however far the body leans
    gc = (0, 22.0, 38.0)
    P("gatherA", "hips", gc, (4.0, 4.0, 4.0), EYE_ON, tag="gather", light=15)
    P("gatherB", "hips", gc, (4.0, 4.0, 4.0), EYE_ON, rot=(0, 45, 0), tag="gather", light=15)
    P("gatherC", "hips", gc, (4.0, 4.0, 4.0), EYE_ON, rot=(45, 0, 0), tag="gather", light=15)
    P("gatherD", "hips", gc, (4.0, 4.0, 4.0), EYE_ON, rot=(0, 0, 45), tag="gather", light=15)
    P("gatherHalo", "hips", gc, (9.0, 9.0, 2.5), ORANGE_GLASS, rot=(0, 45, 0), tag="gather", light=15)
    P("gatherRing", "hips", (0, 22.0, 34.0), (15.0, 15.0, 0.6), ORANGE_GLASS, tag="gather", light=15)
    # ---- the wrap's damage stages: four white-hot slivers of light in front of the core (summoned as air; one is revealed per two landed hits)
    P("crack1", "chest", (0.4, 5.4, 12.4), (0.9, 9.0, 0.7), CRACK, rot=(0, 20, 0), tag="crack1", light=15)
    P("crack2", "chest", (-1.0, 4.2, 12.6), (0.8, 7.5, 0.7), CRACK, rot=(0, -38, 0), tag="crack2", light=15)
    P("crack3", "chest", (1.4, 3.6, 12.8), (0.8, 6.5, 0.7), CRACK, rot=(0, 72, 0), tag="crack3", light=15)
    P("crack4", "chest", (-0.9, 6.4, 13.0), (0.8, 7.0, 0.7), CRACK, rot=(0, -74, 0), tag="crack4", light=15)
    return PARTS


# ---------------------------------------------------------------- forward kinematics
def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def rot_y(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rot_z(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler(fwd, side, twist):
    """fwd positive swings a hanging limb forward (+z)."""
    d = math.radians
    return rot_y(d(twist)) @ rot_z(d(side)) @ rot_x(-d(fwd))


def box_rot(rot):
    return euler(*rot)


def _bone_world(pose):
    out = {}
    order = list(BONES)
    for b in order:
        parent, piv = BONES[b]
        p = pose.get(b, (0, 0, 0))
        R = euler(p[0], p[1], p[2])
        t = np.array(piv, float)
        if len(p) > 3:
            t = t + np.array(p[3:6], float)
        if parent is None:
            out[b] = (R, t)
        else:
            Rp, tp = out[parent]
            out[b] = (Rp @ R, tp + Rp @ t)
    return out


def finger_pose(pose):
    p = dict(pose)
    for s in ("L", "R"):
        k = pose.get("curl" + s, 12.0)
        for i in range(3):
            sp = (i - 1) * 4.0
            p.setdefault(f"f{i}a{s}", (k, sp, 0))
            p.setdefault(f"f{i}b{s}", (k * 1.4, 0, 0))
    return p


def pose_boxes(pose, ground=True):
    """List of dicts (the PARTS entries plus 'centre', 'R', 'half') for a pose."""
    if not PARTS:
        build()
    pose = finger_pose(pose)
    bw = _bone_world(pose)
    puff = pose.get("puff", 0.0)
    corek = pose.get("core", 1.0)
    jaw = pose.get("jawo", 0.0)
    out = []
    lowest = 1e9
    for part in PARTS:
        Rb, tb = bw[part["bone"]]
        if part["name"] == "jaw" and jaw:
            Rb = Rb @ euler(-jaw, 0, 0)
        Rb2 = Rb @ box_rot(part["rot"])
        centre = tb + Rb @ np.array(part["c"], float)
        size = np.array(part["size"], float)
        if part["bone"] in ("chest",) and part["name"] in ("chestLo", "chestMid", "chestHi"):
            size = size * (1 + puff)
        if part["tag"] == "core":
            size = size * corek
        if part["tag"] == "halo":
            size = size * corek
        if part["tag"] == "eyeglow":
            size = size * max(pose.get("eyeg", 0.0), 0.001)
        if part["tag"] == "gather":
            size = size * max(pose.get("gather", 0.0), 0.001)
        blk = part["block"]
        if part["tag"] == "eye" and pose.get("eyes"):
            blk = EYE_ON
        out.append(dict(part, block=blk, centre=centre, R=Rb2, half=size / 2))
    if ground:
        # stand on the ground: lowest foot-box corner at y = 0
        for e in out:
            if e["name"].startswith("foot") or e["name"].startswith("toe"):
                cs = _corners(e)
                lowest = min(lowest, cs[:, 1].min())
        dy = -lowest + pose.get("lift", 0.0)
        for e in out:
            e["centre"] = e["centre"] + np.array([0, dy, 0])
    return out


def _corners(e):
    h = e["half"]
    pts = np.array([[sx * h[0], sy * h[1], sz * h[2]] for sx in (-1, 1) for sy in (-1, 1) for sz in (-1, 1)])
    return e["centre"] + pts @ e["R"].T


# ---------------------------------------------------------------- geometry checks (used by selftest.py and the notes in README.md)
EYE_H = 25.9                 # the giant's eye height in blocks (1.62 x scale 16)
MODEL_H = 30.0               # the monster's height in the fight, blocks (FH in gen_fight)


def _rot_to_quat(m):
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        q = np.array([(m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s, 0.25 * s])
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        q = np.array([0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s, (m[2, 1] - m[1, 2]) / s])
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        q = np.array([(m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s, (m[0, 2] - m[2, 0]) / s])
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        q = np.array([(m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s, (m[1, 0] - m[0, 1]) / s])
    q = q / np.linalg.norm(q)
    return q if q[3] >= 0 else -q


def _quat_to_rot(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def _slerp(qa, qb, f):
    d = float(np.dot(qa, qb))
    if d < 0:
        qb, d = -qb, -d
    if d > 0.9995:
        q = qa + f * (qb - qa)
    else:
        th = math.acos(d)
        q = (math.sin((1 - f) * th) * qa + math.sin(f * th) * qb) / math.sin(th)
    return q / np.linalg.norm(q)


def boxes_between(pose_a, pose_b, f):
    """The boxes the client shows f (0..1) of the way through an interpolation from pose a to pose b: it lerps each display's translation
    and scale and slerps its rotation (that is what interpolation_duration does), so the boxes are not simply the average of the two."""
    A, B = pose_boxes(pose_a), pose_boxes(pose_b)
    out = []
    for a, b in zip(A, B):
        ta, tb = a["centre"] - a["R"] @ a["half"], b["centre"] - b["R"] @ b["half"]
        t = ta + f * (tb - ta)
        half = a["half"] + f * (b["half"] - a["half"])
        R = _quat_to_rot(_slerp(_rot_to_quat(a["R"]), _rot_to_quat(b["R"]), f))
        out.append(dict(a, centre=t + R @ half, R=R, half=half))
    return out


def point_box_distance(p, e):
    """Distance in model units from the point p to the oriented box e (0 inside)."""
    q = e["R"].T @ (np.asarray(p, float) - e["centre"])
    return float(np.linalg.norm(np.maximum(np.abs(q) - e["half"], 0.0)))


def min_eye_distance(boxes, d, eye_h=EYE_H, lat=0.0, shove=0.0, skip_tags=()):
    """Smallest distance in BLOCKS from the giant's eye to any visible part of the monster.  The monster stands with its feet at the origin facing
    +z; the eye is d blocks in front of it (z), `lat` blocks to its left, eye_h up.  `shove` moves the monster back (the eye moves away by that much).
    Returns (distance, part name)."""
    k = MODEL_H / 100.0
    p = np.array([lat / k, eye_h / k, (d + shove) / k])
    best = (1e9, None)
    for e in boxes:
        if e["tag"] in skip_tags or e["block"] == "minecraft:air" or float(np.max(e["half"])) < 0.02:
            continue
        dd = point_box_distance(p, e) * k
        if dd < best[0]:
            best = (dd, e["name"])
    return best


def pose_min_distance(name, ds, eye_h=EYE_H, lat=0.0, skip_tags=()):
    """(distance, part, d) of the closest approach of pose `name` over the eye distances `ds` (blocks)."""
    bx = pose_boxes(poses()[name])
    best = (1e9, None, None)
    for d in ds:
        m = min_eye_distance(bx, d, eye_h, lat, skip_tags=skip_tags)
        if m[0] < best[0]:
            best = (m[0], m[1], d)
    return best


CLOSE = (9.0, 17.0)          # blocks: the fight's normal close range, the nearest the player stands to hit the core (9) to the AI's stand-off (17)
THRUST_RANGE = (14.1, 23.1)  # blocks: where the arm thrust's 9-wide zone (18.6 ahead) reaches the giant
WRAP_D = 10.0                # blocks: where the wrapped monster stands (CFG wrap_dist)
MIN_CLEAR = 2.75             # blocks ("about 3"): the least any visible part may come to the eye


def _frange(a, b, step=0.5):
    n = int(round((b - a) / step))
    return [a + i * step for i in range(n + 1)]


def eye_clearance_table(mod=None, wrap_d=None, shove_blocks=4.8):
    """[(label, min distance in blocks, part, eye distance d where it happens, required minimum)] for every pose family, measured as the monster's display
    boxes are shown (the in-between frames of an interpolation included: the client lerps translation and scale and slerps rotation).
    `mod`: the module whose poses to measure (default this one; an older copy to get the 'before' numbers)."""
    m = mod or sys.modules[__name__]
    wd = wrap_d or WRAP_D
    m.build()
    P = m.poses()
    rows = []

    def add(label, boxes_list, ds, need, shoves=None, lats=(0.0,)):
        best = (1e9, None, None)
        for bi, bx in enumerate(boxes_list):
            for d in ds:
                for lat in lats:
                    r = min_eye_distance(bx, d, lat=lat, shove=(shoves[bi] if shoves else 0.0))
                    if r[0] < best[0]:
                        best = (r[0], r[1], d)
        rows.append((label, best[0], best[1], best[2], need))

    def pose(n):
        return m.pose_boxes(P[n])

    def between(a, b, fs):
        return [_boxes_between_mod(m, a, b, f) for f in fs]

    close = _frange(*CLOSE)
    fr = (0.25, 0.5, 0.75, 1.0)
    for n in ("idle_a", "idle_b", "walk_l", "walk_r", "windup", "stagger"):
        add(n, [pose(n)], close, MIN_CLEAR)
    add("stagger, standing much closer and off to the side (d 4 to 17, lateral 0 to 6)", [pose("stagger")], _frange(4, 17), MIN_CLEAR,
        lats=(0.0, 2.0, 4.0, 6.0))
    for a in ("idle_a", "idle_b", "windup", "walk_l", "walk_r"):
        add(f"{a} -> stagger (6 ticks, thrown back 4.8)", between(a, "stagger", fr), close, MIN_CLEAR, shoves=[shove_blocks * f for f in fr])
        add(f"{a} -> stagger (windup stagger, no shove)", between(a, "stagger", fr), close, MIN_CLEAR)
    for i in range(8):
        add(f"regen_{i}", [pose(f"regen_{i}")], close, MIN_CLEAR)
    add("idle_a -> regen_0 (the crack)", between("idle_a", "regen_0", (0.25, 0.5, 0.75, 1.0)), close, MIN_CLEAR)
    add("thrust", [pose("thrust")], _frange(*THRUST_RANGE), MIN_CLEAR)
    add("windup -> thrust (3 ticks)", between("windup", "thrust", (0.34, 0.67, 1.0)), _frange(*THRUST_RANGE), MIN_CLEAR)
    for n in ("charge", "charge_2", "charge_3"):
        add(n + " (beyond thrust range, d 24 to 60; the glow parts included)", [pose(n)], _frange(24, 60, 2), MIN_CLEAR)
    add("wrap_open (running in, d 10 to 13)", [pose("wrap_open")], _frange(wd, wd + 3), MIN_CLEAR)
    names = [n for n in ("wrap_close", "wrap_tight", "wrap_hit") if n in P]
    for n in names:
        add(f"{n} (d {wd:g})", [pose(n)], [wd], MIN_CLEAR)
    if len(names) == 3:
        fs = (0.25, 0.5, 0.75)
        for a, b in (("wrap_open", "wrap_close"), ("wrap_close", "wrap_tight"), ("wrap_close", "wrap_hit"), ("wrap_hit", "wrap_close"),
                     ("wrap_tight", "wrap_hit"), ("wrap_hit", "wrap_tight")):
            add(f"{a} -> {b} (d {wd:g})", between(a, b, fs), [wd], MIN_CLEAR)
    return rows


def _boxes_between_mod(m, a, b, f):
    """boxes_between for another module's poses (the 'before' numbers)."""
    A, B = m.pose_boxes(m.poses()[a]), m.pose_boxes(m.poses()[b])
    out = []
    for x, y in zip(A, B):
        ta, tb = x["centre"] - x["R"] @ x["half"], y["centre"] - y["R"] @ y["half"]
        t = ta + f * (tb - ta)
        half = x["half"] + f * (y["half"] - x["half"])
        R = _quat_to_rot(_slerp(_rot_to_quat(x["R"]), _rot_to_quat(y["R"]), f))
        out.append(dict(x, centre=t + R @ half, R=R, half=half))
    return out


def core_centre(pose):
    for e in pose_boxes(pose):
        if e["name"] == "coreA":
            return e["centre"]


def eye_centre(pose):
    xs = [e["centre"] for e in pose_boxes(pose) if e["tag"] == "eye"]
    return sum(xs) / len(xs)


# ---------------------------------------------------------------- poses
def mir(d):
    """Mirror a dict of left-bone entries to the right bones."""
    out = dict(d)
    for k, v in d.items():
        if k.endswith("L"):
            r = k[:-1] + "R"
            if r not in d:
                v = tuple(v)
                out[r] = (v[0], -v[1], -v[2]) + tuple(v[3:]) if len(v) <= 3 else (v[0], -v[1], -v[2], -v[3], v[4], v[5])
    return out


def pose_def():
    P = {}
    # standing, slightly hunched, weight on both legs, arms hanging forward of the body and a little out
    base = dict(
        hips=(0, 0, 0, 0, 0, 0), spine=(4, 0, 0), chest=(8, 0, 0),
        thighL=(5, 1.5, 0), shinL=(-9, 0, 0), footL=(4, 0, 0),
        thighR=(5, -1.5, 0), shinR=(-9, 0, 0), footR=(4, 0, 0),
        shoulderL=(0, 0, 0), shoulderR=(0, 0, 0),
        uarmL=(10, 5, 0), farmL=(16, -2, 0), handL=(8, 0, 0),
        uarmR=(10, -5, 0), farmR=(16, 2, 0), handR=(8, 0, 0),
        curlL=14, curlR=14, puff=0.0, core=1.0, jawo=0.0,
    )
    P["idle_a"] = dict(base)
    P["idle_b"] = dict(base, spine=(6, 1, 0), chest=(8, -1.5, 0), puff=0.035,
                       uarmL=(13, 6, 0), uarmR=(7, -4, 0), farmL=(20, -2, 0), farmR=(14, 2, 0), jawo=3, core=1.06,
                       hips=(0, 0, 0, 0.0, 0, 0))
    # hunched and damaged: folded forward, one shoulder plate hanging, the other cocked up, arms dangling; the chest
    # breathes slowly (puff over 8 key frames = 80 ticks) while the core flickers (a different size every frame)
    reg = dict(base, hips=(0, 0, 0, 0, 0, -9.0), spine=(-18, 0, 0), chest=(-26, 0, 0), thighL=(18, 2, 0), shinL=(-30, 0, 0), footL=(12, 0, 0),
               thighR=(18, -2, 0), shinR=(-30, 0, 0), footR=(12, 0, 0),
               uarmL=(24, 8, 0), uarmR=(24, -8, 0), farmL=(26, -2, 0), farmR=(26, 2, 0),
               shoulderL=(-16, 10, -24), shoulderR=(12, -8, 20), curlL=24, curlR=24, jawo=6, puff=0.0, core=1.0)
    P["regen_a"] = reg
    P["regen_b"] = dict(reg, puff=0.06, core=1.22, chest=(-24, 0, 0), spine=(-17, 0, 0),
                        uarmL=(27, 10, 0), uarmR=(27, -10, 0), jawo=9)
    breath = (0.0, 0.015, 0.035, 0.055, 0.06, 0.045, 0.02, 0.005)
    flick = (1.0, 0.62, 1.28, 0.8, 1.32, 0.55, 1.2, 0.9)
    for i in range(8):
        sway = ((0, 2, 0), (1, 3, 0), (2, 4, 1), (2, 3, 2), (1, 1, 2), (0, -1, 1), (-1, -2, 0), (-1, 0, 0))[i]
        P[f"regen_{i}"] = dict(reg, puff=breath[i], core=flick[i], jawo=5 + 5 * breath[i] * 20,
                               chest=(-26 + 30 * breath[i], sway[0], sway[2]), spine=(-18 + 12 * breath[i], 0, 0),
                               shoulderL=(-16 + 4 * sway[1], 10, -24), shoulderR=(12 + 3 * sway[0], -8, 20),
                               uarmL=(24 + sway[1], 8 + sway[0], 0), uarmR=(24 + sway[0], -8 - sway[1], 0))
    # charging: leaning forward over its feet, the arms drawn back and out, the eyes blazing up and a glow gathering
    # in front of the mask; three stages (the generator plays them 0, 10 and 24 ticks into the charge)
    chg = dict(base, spine=(-8, 0, 0), chest=(-12, 0, 0), thighL=(8, 3, 0), thighR=(8, -3, 0), shinL=(-14, 0, 0),
               shinR=(-14, 0, 0), footL=(6, 0, 0), footR=(6, 0, 0),
               uarmL=(-26, 26, 0), uarmR=(-26, -26, 0), farmL=(34, -6, 0), farmR=(34, 6, 0), handL=(14, 0, 0),
               handR=(14, 0, 0), curlL=36, curlR=36, jawo=14, puff=0.05, core=1.15, eyes=1, eyeg=0.65, gather=0.35)
    P["charge"] = chg
    P["charge_2"] = dict(chg, spine=(-11, 0, 0), chest=(-16, 0, 0), uarmL=(-34, 28, 0), uarmR=(-34, -28, 0),
                         farmL=(40, -8, 0), farmR=(40, 8, 0), jawo=20, puff=0.06, core=1.28, eyeg=1.05, gather=0.8)
    P["charge_3"] = dict(chg, spine=(-14, 0, 0), chest=(-20, 0, 0), thighL=(11, 3, 0), thighR=(11, -3, 0),
                         shinL=(-20, 0, 0), shinR=(-20, 0, 0), uarmL=(-44, 32, 0), uarmR=(-44, -32, 0),
                         farmL=(46, -10, 0), farmR=(46, 10, 0), curlL=44, curlR=44, jawo=26, puff=0.07, core=1.4,
                         eyeg=1.45, gather=1.4)    # the thrust: right arm cocked back, body twisted, then arm driven straight out
    P["windup"] = dict(base, spine=(6, 0, -14), chest=(8, 0, -18), thighL=(10, 3, 0), thighR=(-4, -3, 0), shinL=(-16, 0, 0),
                       shinR=(-14, 0, 0), footL=(6, 0, 0), footR=(2, 0, 0),
                       uarmR=(-36, -8, 0), farmR=(-62, 0, 0), handR=(10, 0, 0), curlR=6,
                       uarmL=(18, 12, 0), farmL=(24, 0, 0), jawo=10, eyes=1)
    P["thrust"] = dict(base, spine=(6, 0, 16), chest=(8, 0, 22), thighL=(-6, 3, 0), thighR=(26, -3, 0), shinL=(-4, 0, 0),
                       shinR=(-26, 0, 0), footL=(2, 0, 0), footR=(10, 0, 0),
                       uarmR=(46, -3, 0), farmR=(0, 0, 0), handR=(0, 0, 0), curlR=2,
                       uarmL=(-18, 14, 0), farmL=(24, 0, 0), jawo=14, hips=(0, 0, 0, 0, 0, 3.0))
    # stagger (a core hit during the windup, and the start of every back-off): it RECOILS.  The torso is thrown back (positive = back), the arms fly up and
    # out to the sides and behind, one foot steps back and the whole body is pulled back 3.6 blocks (hips dz): no limb comes toward the giant.
    P["stagger"] = dict(base, hips=(0, 0, 0, 0, 0, -12.0), spine=(12, 0, 0), chest=(24, 0, 0),
                        thighL=(-14, 3, 0), shinL=(-4, 0, 0), footL=(12, 0, 0), thighR=(16, -3, 0), shinR=(-34, 0, 0), footR=(4, 0, 0),
                        uarmL=(-38, 125, 0), uarmR=(-38, -125, 0), farmL=(-12, 14, 0), farmR=(-12, -14, 0), handL=(10, 0, 0), handR=(10, 0, 0),
                        curlL=44, curlR=44, jawo=28, core=1.3)    # wrapping: arms flung wide open, then folded across the body around its prey
    P["wrap_open"] = dict(base, spine=(14, 0, 0), chest=(20, 0, 0), thighL=(14, 8, 0), thighR=(14, -8, 0), shinL=(-22, 0, 0),
                          shinR=(-22, 0, 0), footL=(8, 0, 0), footR=(8, 0, 0),
                          uarmL=(46, 70, 0), uarmR=(46, -70, 0), farmL=(10, -14, 0), farmR=(10, 14, 0),
                          curlL=4, curlR=4, jawo=26, eyes=1, puff=0.05)
    # wrapping (it stands WRAP_D = 10 blocks in front of the giant, which is 25.9 up): the arms come round the SIDES of the giant (elbows 5 blocks to each
    # side, hands meeting behind its back, all of it 3 blocks or more from the eyes), the torso hunched over it.  `wrap_tight` squeezes (arms
    # crossed further, torso in), `wrap_hit` is the shudder of a landed hit: the arms are flung out, the torso thrown back.
    wlean = dict(base, spine=(6, 0, 0), chest=(10, 0, 0), thighL=(10, 4, 0), thighR=(10, -4, 0), shinL=(-18, 0, 0), shinR=(-18, 0, 0),
                 footL=(8, 0, 0), footR=(8, 0, 0), jawo=16, eyes=1, puff=0.07, core=1.25, curlL=30, curlR=30)
    P["wrap_close"] = dict(wlean, uarmL=(46, 9, 0), uarmR=(46, -9, 0), farmL=(22, -36, 0), farmR=(22, 36, 0), handL=(10, -10, 0), handR=(10, 10, 0))
    P["wrap_tight"] = dict(wlean, spine=(2, 0, 0), chest=(4, 0, 0), uarmL=(52, 3, 0), uarmR=(52, -3, 0), farmL=(24, -52, 0), farmR=(24, 52, 0),
                           handL=(10, -20, 0), handR=(10, 20, 0), core=1.4, jawo=24)
    P["wrap_hit"] = dict(wlean, spine=(12, 0, 0), chest=(20, 0, 0), uarmL=(36, 36, 0), uarmR=(36, -36, 0), farmL=(12, -6, 0), farmR=(12, 6, 0),
                         core=1.6, jawo=30)    # dying: a clear collapse. The knees buckle, it drops onto both knees (shins flat behind it), then slumps
    # forward over them, mask down, arms trailing on the ground: a heap, not a standing figure
    P["die_1"] = dict(base, spine=(-8, 0, 0), chest=(-10, 0, 0), thighL=(34, 4, 0), thighR=(30, -4, 0), shinL=(-64, 0, 0),
                      shinR=(-58, 0, 0), footL=(22, 0, 0), footR=(20, 0, 0),
                      uarmL=(-6, 16, 0), uarmR=(-6, -16, 0), farmL=(8, 0, 0), farmR=(8, 0, 0), curlL=6, curlR=6, jawo=30,
                      core=0.8, eyes=0)
    P["die_2"] = dict(base, spine=(-22, 0, 0), chest=(-30, 0, 0), thighL=(6, 6, 0), thighR=(6, -6, 0), shinL=(-150, 0, 0),
                      shinR=(-150, 0, 0), footL=(60, 0, 0), footR=(60, 0, 0),
                      uarmL=(-12, 22, 0), uarmR=(-12, -22, 0), farmL=(10, 0, 0), farmR=(10, 0, 0), curlL=4, curlR=4,
                      jawo=36, core=0.6)
    P["die_3"] = dict(base, spine=(-52, 0, 0), chest=(-66, 4, 0), thighL=(6, 8, 0), thighR=(6, -8, 0), shinL=(-152, 0, 0),
                      shinR=(-152, 0, 0), footL=(60, 0, 0), footR=(60, 0, 0),
                      uarmL=(30, 24, 0), uarmR=(26, -26, 0), farmL=(24, 0, 0), farmR=(30, 0, 0), curlL=2, curlR=2,
                      jawo=40, core=0.45, shoulderL=(-14, 6, -22), shoulderR=(10, -6, 18))    # walking: two key poses, planted-forward on one leg and trailing (knee bent, lifted) on the other
    st = 21.0   # thigh swing
    def walk(sgn):
        # sgn = +1: left leg forward
        a, b = ("L", "R") if sgn > 0 else ("R", "L")
        d = dict(base, spine=(5, 0, -3 * sgn), chest=(7, 0, 5 * sgn), hips=(0, 0, 3 * sgn, 0.9 * sgn, 0, 0))
        d["thigh" + a] = (st, 2.0 * (1 if a == "L" else -1), 0)
        d["shin" + a] = (-4, 0, 0)
        d["foot" + a] = (-st + 8, 0, 0)
        d["thigh" + b] = (-st * 0.85, -2.0 * (1 if b == "L" else -1) * -1, 0)
        d["shin" + b] = (-30, 0, 0)
        d["foot" + b] = (st * 0.4, 0, 0)
        # arms swing against the legs
        d["uarm" + a] = (-14, 6 if a == "L" else -6, 0)
        d["uarm" + b] = (26, 6 if b == "L" else -6, 0)
        d["farm" + a] = (12, 0, 0)
        d["farm" + b] = (26, 0, 0)
        return d
    P["walk_l"] = walk(1)
    P["walk_r"] = walk(-1)
    return P


POSES = None


def poses():
    global POSES
    if POSES is None:
        POSES = pose_def()
    return POSES


def pose_by_name(name):
    return poses()[name]


if __name__ == "__main__":
    build()
    print(len(PARTS), "parts")
    for k in poses():
        bs = pose_boxes(poses()[k])
        ys = [b["centre"][1] for b in bs]
        print(f"{k:10s} max y {max(ys):6.1f}  core {core_centre(poses()[k]).round(1)}")






