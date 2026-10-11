"""The fortress city at night: where the giant rises out of the ground and fights the monster.

Local coordinates: x east, y up, z south.  Street surface block is y=31, standing level y=32.
Layout (all numbers are local blocks):
  city plate x,z in [32, 288); hills / mountain wall outside it; lake along the south edge.
  N-S roads (x ranges): 56-72, 112-128, 146-174 (main avenue, 28 wide), 192-208, 248-264
  E-W roads (z ranges): the same numbers.
  Plaza (arena): x,z in [112, 208) with the launch shaft at its centre (160, 160).
  Monster stands on the main avenue to the north, around (160, 50).
"""
import math
import os
import sys
from random import Random

import numpy as np

SX, SY, SZ = 320, 160, 320
ST = 32                      # standing level; street surface block is y = ST-1
CX = CZ = 160
CITY = (32, 288)
CELLS = [(32, 56), (72, 112), (128, 146), (174, 192), (208, 248), (264, 288)]
ROADS = [(56, 72), (112, 128), (146, 174), (192, 208), (248, 264)]
MAIN = (146, 174)
PLAZA = (112, 208)
SEED = 2015

# windows: lit blocks that need no power (a lit redstone_lamp switches itself off in the game when nothing powers it)
LIT_WARM = (("ochre_froglight", 6), ("glowstone", 3), ("shroomlight", 1))
LIT_COOL = (("sea_lantern", 7), ("pearlescent_froglight", 2), ("glowstone", 1))
NEON = ("sea_lantern", "shroomlight", "pearlescent_froglight", "verdant_froglight", "ochre_froglight",
        "glowstone")
SIGN_COLORS = ("magenta_concrete", "lime_concrete", "cyan_concrete", "orange_concrete", "light_blue_concrete",
               "pink_concrete", "yellow_concrete", "red_concrete", "white_concrete")
WALLS_LIGHT = ("light_gray_concrete", "white_concrete", "light_gray_terracotta", "white_terracotta", "calcite",
               "light_gray_concrete", "smooth_stone")
WALLS_APT = ("white_terracotta", "light_gray_terracotta", "orange_terracotta", "cyan_terracotta",
             "brown_terracotta", "white_concrete", "light_gray_concrete", "pink_terracotta")
TRIMS = ("gray_concrete", "black_concrete", "polished_deepslate", "gray_concrete")


# ------------------------------------------------------------------ small utilities
def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3 - 2 * t)


def pink_noise(shape, beta, seed):
    r = np.random.default_rng(seed)
    f = np.fft.fft2(r.standard_normal(shape))
    fx = np.fft.fftfreq(shape[0])[:, None]
    fz = np.fft.fftfreq(shape[1])[None, :]
    k = np.sqrt(fx ** 2 + fz ** 2)
    k[0, 0] = 1.0
    f = f / k ** beta
    f[0, 0] = 0
    out = np.real(np.fft.ifft2(f))
    out = out / (out.std() * 2.2)
    return np.clip(out, -1, 1)


class C:
    """Build context: the world, a seeded generator, a block-id cache and a few drawing shortcuts."""

    def __init__(self, w):
        self.w = w
        self.rng = Random(SEED)
        self._ids = {}
        self.lots = []
        self.roof_lights = []

    def I(self, name):
        i = self._ids.get(name)
        if i is None:
            i = self._ids[name] = self.w._id(name)
        return i

    def box(self, x0, y0, z0, x1, y1, z1, name):
        """Half-open box [x0,x1) x [y0,y1) x [z0,z1)."""
        if x1 > x0 and y1 > y0 and z1 > z0:
            self.w.fill(x0, y0, z0, x1 - 1, y1 - 1, z1 - 1, name)

    def put(self, x, y, z, name):
        self.w.set(x, y, z, name)

    def put_free(self, x, y, z, name):
        """Only where nothing is drawn yet (trees, props)."""
        w = self.w
        if w.inside(x, y, z) and w.a[x, y, z] <= 1:
            w.a[x, y, z] = self.I(name)

    def ring(self, x0, z0, x1, z1, y, name, h=1):
        for yy in range(y, y + h):
            self.w.a[x0:x1, yy, z0] = self.I(name)
            self.w.a[x0:x1, yy, z1 - 1] = self.I(name)
            self.w.a[x0, yy, z0:z1] = self.I(name)
            self.w.a[x1 - 1, yy, z0:z1] = self.I(name)

    def line(self, p, q, name):
        n = int(max(abs(q[0] - p[0]), abs(q[1] - p[1]), abs(q[2] - p[2]))) + 1
        for i in range(n + 1):
            t = i / max(1, n)
            self.put(int(round(p[0] + (q[0] - p[0]) * t)), int(round(p[1] + (q[1] - p[1]) * t)),
                     int(round(p[2] + (q[2] - p[2]) * t)), name)


def hazard_name(a, b):
    return "yellow_concrete" if ((a + b) // 2) % 2 == 0 else "black_concrete"


# ------------------------------------------------------------------ terrain
def tree_spruce(c, x, y, z, rng, tall=(12, 22)):
    ht = rng.randint(*tall)
    for i in range(ht):
        c.put(x, y + i, z, "spruce_log")
    for ly in range(3, ht + 1):
        t = (ly - 3) / max(1, ht - 3)
        r = max(0, int(round(4.2 * (1 - t))) - (1 if ly % 3 == 0 else 0))
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if dx * dx + dz * dz <= r * r + 1 and (dx or dz or ly == ht):
                    c.put_free(x + dx, y + ly, z + dz, "spruce_leaves[persistent=true]")
    c.put_free(x, y + ht, z, "spruce_leaves[persistent=true]")


def tree_round(c, x, y, z, rng, kind="oak", tall=(7, 12)):
    ht = rng.randint(*tall)
    R = rng.randint(3, 5)
    log, leaf = (kind + "_log"), (kind + "_leaves[persistent=true]")
    for i in range(ht):
        c.put(x, y + i, z, log)
    cy = y + ht - 1
    for dx in range(-R, R + 1):
        for dy in range(-R + 1, R):
            for dz in range(-R, R + 1):
                if dx * dx + dz * dz + dy * dy * 1.4 <= R * R + 1 and rng.random() < 0.93:
                    c.put_free(x + dx, cy + dy, z + dz, leaf)


RIM_CREST = 21.0      # ridge line: blocks from the city plate (rounded-square metric), so about 11 blocks in from the box edge
RIM_EDGE = 12.0       # the outer slope runs from the ridge to the box edge over this many blocks (Chebyshev inset)
RIM_FOOT = 4          # height of the outer slope where it meets the box edge (every side and corner)
SIDES = {             # (t along the side, q blocks out from the plate) -> (x, z)
    "N": lambda t, q: (t, CITY[0] - 1 - q),
    "S": lambda t, q: (t, CITY[1] + q),
    "W": lambda t, q: (CITY[0] - 1 - q, t),
    "E": lambda t, q: (CITY[1] + q, t),
}
# contour roads on the inner slopes: (side, t from, t to, road level).  The stretch behind the monster's avenue
# (x 126..194 on the north side) is left dark so the silhouette reads.
ROAD_SEGS = [("N", 56, 122, 50), ("N", 198, 262, 55), ("W", 58, 128, 47), ("W", 192, 262, 57),
             ("E", 52, 126, 56), ("E", 186, 258, 45), ("S", 34, 46, 46), ("S", 278, 288, 50)]


def rim_heights():
    """Heights (blocks) of the ground round the city: a continuous ring of mountains whose crest is about 11 blocks in
    from the box edge on all four sides and the corners, falling on the outside to RIM_FOOT at the box edge."""
    xs = np.arange(SX)[:, None] + 0.5
    zs = np.arange(SZ)[None, :] + 0.5
    dx = np.maximum(np.maximum(CITY[0] - xs, xs - CITY[1]), 0.0)
    dz = np.maximum(np.maximum(CITY[0] - zs, zs - CITY[1]), 0.0)
    dp = (dx ** 4 + dz ** 4) ** 0.25                     # rounded square distance from the plate
    e = np.minimum(np.minimum(xs, SX - xs), np.minimum(zs, SZ - zs))          # inset from the box edge
    n1 = pink_noise((SX, SZ), 2.0, 101)
    n2 = pink_noise((SX, SZ), 1.5, 102)
    nr = pink_noise((SX, SZ), 2.6, 104)
    mx = smoothstep(44, 66, xs) * smoothstep(276, 254, xs)
    crest = np.maximum(108 + 20 * nr, 98)
    crest = np.maximum(crest * (1 - 0.06 * mx * smoothstep(280, 296, zs)), 94)   # a little lower behind the lake
    inner = 32 + (crest - 32) * smoothstep(0, RIM_CREST, dp)
    outer = RIM_FOOT + (crest - RIM_FOOT) * smoothstep(0, RIM_EDGE, e)
    ring = np.minimum(inner, outer)
    te = smoothstep(0, 6, e)
    amp = np.clip((ring - 32) / 40, 0, 1)
    h = ring * (1 + 0.10 * n1 * te) + 6 * n2 * amp * te
    h = np.where(dp < RIM_CREST, np.maximum(h, 32 + 0.85 * (ring - 32)), h)
    h = np.where(e < 0.75, RIM_FOOT, h)                                      # the very edge is the same everywhere
    # the lake along the south edge
    lm = mx * smoothstep(278, 287, zs) * (1 - smoothstep(306, 312, zs))
    hl = np.interp(zs + 2.5 * n1, [287, 288, 290, 296, 300, 304, 308], [32, 30, 25, 24, 24, 40, 58])
    h = lm * np.minimum(hl, h) + (1 - lm) * h
    h = np.clip(np.round(h), 1, 150).astype(int)
    return h, dict(e=e, dp=dp, lm=lm)


def plan_rim_roads(h):
    """Flatten a 5-wide shelf along a contour of each ROAD_SEGS stretch (edits h); returns the road centres."""
    roads = []
    for (side, t0, t1, hr) in ROAD_SEGS:
        f = SIDES[side]
        ts = np.arange(t0, t1)
        qs = []
        for t in ts:
            q = None
            for qq in range(0, 24):
                x, z = f(int(t), qq)
                if h[x, z] >= hr:
                    q = qq
                    break
            qs.append(q if q is not None else (qs[-1] if qs else 10))
        qs = np.array(qs, float)
        pad = np.pad(qs, 5, mode="edge")
        qs = np.convolve(pad, np.ones(11) / 11.0, mode="valid")
        cells = []
        for t, qf in zip(ts, qs):
            qc = int(round(qf))
            for dq in range(-2, 3):
                x, z = f(int(t), qc + dq)
                h[x, z] = hr
            cells.append((int(t), qc))
        roads.append(dict(side=side, y=hr, cells=cells))
    return roads


def build_terrain(c):
    w, rng = c.w, c.rng
    h, aux = rim_heights()
    c.rim_roads = plan_rim_roads(h)
    c.rim_h = h
    e, lm = aux["e"], aux["lm"]
    roadmask = np.zeros((SX, SZ), bool)
    for rd in c.rim_roads:
        f = SIDES[rd["side"]]
        for (t, qc) in rd["cells"]:
            for dq in range(-3, 4):
                x, z = f(t, qc + dq)
                roadmask[x, z] = True
    xs = np.arange(SX)[:, None] + 0.5
    zs = np.arange(SZ)[None, :] + 0.5

    # surface material per column
    pad = np.pad(h, 1, mode="edge")
    nb = np.stack([pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]])
    lo = np.maximum(0, np.minimum(h, nb.min(axis=0)) - 3)
    slope = np.max(np.abs(nb - h[None]), axis=0)
    rr = np.random.default_rng(7).random((SX, SZ))
    rock = ["deepslate", "stone", "tuff", "deepslate", "cobbled_deepslate", "blackstone", "andesite", "deepslate"]
    n3 = pink_noise((SX, SZ), 1.3, 103)
    rk = np.clip(((n3 * 0.5 + 0.5) * len(rock) + (rr - 0.5) * 1.2).astype(int), 0, len(rock) - 1)
    outside = np.ones((SX, SZ), bool)
    outside[CITY[0]:CITY[1], CITY[0]:CITY[1]] = False
    lake = (lm > 0.03) & (zs >= 288) & (zs < 312)
    trees = []
    for i in range(SX):
        for j in range(SZ):
            if not outside[i, j]:
                continue
            hh, l = int(h[i, j]), int(lo[i, j])
            if hh < 1:
                continue
            sl = int(slope[i, j])
            if lake[i, j] and hh <= 30:       # lake bed
                top, sub = "sand", "sand"
                if rr[i, j] < 0.25:
                    top = "gravel"
            elif e[i, j] < RIM_EDGE + 1 or hh >= 98 or sl >= 4:
                top = sub = rock[rk[i, j]]
            elif hh >= 80 and sl >= 2:
                top = rock[rk[i, j]]
                sub = "stone"
            elif hh <= 33 and 288 < j < 300 and 40 < i < 280:
                top, sub = "sand", "sand"
            else:
                top = "podzol" if rr[i, j] < 0.18 else "grass_block"
                sub = "dirt"
                if (sl <= 2 and hh < 84 and rr[i, j] > 0.975 and hh > 33 and not roadmask[i, j]
                        and e[i, j] > RIM_EDGE + 3):
                    trees.append((i, hh, j))
            core = "deepslate" if hh > 70 else "stone"
            if top in ("sand", "gravel"):
                # sand and gravel fall if nothing holds them: lay them as a skin on a floor of stone that reaches
                # below the skin, so the lake bed and the beach stay where they are and the lake stays sealed
                c.box(i, min(max(l, 16), hh - 5), j, i + 1, hh - 4, j + 1, "stone")
                c.box(i, hh - 4, j, i + 1, hh - 1, j + 1, sub)
            else:
                if hh - 4 > l:
                    c.box(i, l, j, i + 1, hh - 4, j + 1, core)
                c.box(i, max(l, hh - 4), j, i + 1, hh - 1, j + 1, sub)
            c.put(i, hh - 1, j, top)
            if lake[i, j] and hh <= 29:
                c.box(i, hh, j, i + 1, 30, j + 1, "water")
    # city plate (the roads and lots are painted on y = ST-1 later)
    c.box(CITY[0], 28, CITY[0], CITY[1], ST - 1, CITY[1], "stone")
    # sea wall along the promenade
    c.box(CITY[0] + 24, 24, CITY[1] - 1, CITY[1] - 24, ST - 1, CITY[1], "stone_bricks")
    for (i, hh, j) in trees:
        tree_spruce(c, i, hh, j, rng)
    rim_life(c, h, e)
    return h


def rim_life(c, h, e):
    """Distant lights on the slopes: contour roads with lamps, a few cabins with lit windows on the inner foot of the
    hills, and lit windows scattered on the outer flanks, so the city sits in a landscape."""
    rng = Random(SEED + 77)
    lamp_heads = ("ochre_froglight", "glowstone", "ochre_froglight", "sea_lantern")
    # roads
    for rd in c.rim_roads:
        f = SIDES[rd["side"]]
        y = rd["y"] - 1
        for k, (t, qc) in enumerate(rd["cells"]):
            for dq in (-2, 2):
                x, z = f(t, qc + dq)
                c.put(x, y, z, "stone_bricks")
            for dq in (-1, 0, 1):
                x, z = f(t, qc + dq)
                nm = "black_concrete" if (k * 7 + dq * 3) % 11 == 0 else "gray_concrete"
                if dq == 0 and (k % 6) < 3:
                    nm = "yellow_concrete"
                c.put(x, y, z, nm)
            if k % 9 == 4:
                x, z = f(t, qc + 2)
                head = lamp_heads[(k // 9) % len(lamp_heads)]
                c.put(x, y + 1, z, "iron_chain[axis=y]")
                c.put(x, y + 2, z, "iron_chain[axis=y]")
                c.put(x, y + 3, z, head)

    # cabins
    used = np.zeros((SX, SZ), bool)
    for rd in c.rim_roads:
        f = SIDES[rd["side"]]
        for (t, qc) in rd["cells"]:
            for dq in range(-3, 4):
                x, z = f(t, qc + dq)
                used[x, z] = True
    placed = 0
    for _ in range(400):
        if placed >= 16:
            break
        side = rng.choice("NNWWEESS")
        t = rng.randint(40, 280)
        if side == "N" and 124 <= t <= 196:
            continue
        if side == "S" and 40 <= t <= 280:
            continue
        q = rng.randint(2, 15)
        horiz = side in "NS"
        w_, d_ = (6, 5) if horiz else (5, 6)
        x0, z0 = SIDES[side](t, q)
        x1, z1 = x0 + w_, z0 + d_
        if x0 < 2 or z0 < 2 or x1 > SX - 2 or z1 > SZ - 2:
            continue
        if CITY[0] - 2 < x0 < CITY[1] and CITY[0] - 2 < z0 < CITY[1]:
            continue
        sub = h[x0:x1, z0:z1]
        if sub.max() - sub.min() > 5 or sub.min() < 33 or used[x0 - 1:x1 + 1, z0 - 1:z1 + 1].any():
            continue
        if (e[x0:x1, z0:z1] < RIM_EDGE + 3).any():
            continue
        used[x0 - 1:x1 + 1, z0 - 1:z1 + 1] = True
        base = int(sub.max())
        wall = rng.choice(("dark_oak_planks", "spruce_planks", "stone_bricks"))
        for x in range(x0, x1):
            for z in range(z0, z1):
                hh = int(h[x, z])
                c.box(x, hh - 1, z, x + 1, base, z + 1, "stone_bricks")
        # the plate's centre is where the windows look
        for x in range(x0, x1):
            for z in range(z0, z1):
                edge = x in (x0, x1 - 1) or z in (z0, z1 - 1)
                for dy in range(0, 3):
                    if edge:
                        win = dy == 1 and (x + z) % 2 == 1 and rng.random() < 0.7
                        c.put(x, base + dy, z, rng.choice(("ochre_froglight", "ochre_froglight", "glowstone"))
                              if win else wall)
                    else:
                        c.put(x, base + dy, z, "air")
                c.put(x, base + 3, z, "deepslate_tile_slab[type=bottom]")
        placed += 1
    # lit windows on the outer flanks (seen from outside the box and from the air)
    n = 0
    for _ in range(2000):
        if n >= 46:
            break
        x, z = rng.randint(2, SX - 3), rng.randint(2, SZ - 3)
        ee = min(x, SX - 1 - x, z, SZ - 1 - z)
        if ee < 2 or ee > 9:
            continue
        hh = int(h[x, z])
        if hh < 14:
            continue
        nm = rng.choice(("ochre_froglight", "ochre_froglight", "glowstone", "sea_lantern", "ochre_froglight"))
        c.put(x, hh - 1, z, nm)

        n += 1



# ------------------------------------------------------------------ ground, roads, plaza
def dilate(m, r):
    out = m.copy()
    for s in range(1, r + 1):
        out[s:, :] |= m[:-s, :]
        out[:-s, :] |= m[s:, :]
    m2 = out.copy()
    for s in range(1, r + 1):
        out[:, s:] |= m2[:, :-s]
        out[:, :-s] |= m2[:, s:]
    return out


def paint_ground(c, lots):
    """Fills the y = ST-1 layer of the city plate: lots, sidewalks, asphalt, markings, the plaza."""
    w, I = c.w, c.I
    X = np.arange(SX)[:, None] * np.ones((1, SZ), int)
    Z = np.arange(SZ)[None, :] * np.ones((SX, 1), int)
    inrect = (X >= CITY[0]) & (X < CITY[1]) & (Z >= CITY[0]) & (Z < CITY[1])
    rx = np.zeros(SX, bool)
    rz = np.zeros(SZ, bool)
    for a, b in ROADS:
        rx[a:b] = True
        rz[a:b] = True
    road = (rx[:, None] | rz[None, :]) & inrect
    plaza = (X >= PLAZA[0]) & (X < PLAZA[1]) & (Z >= PLAZA[0]) & (Z < PLAZA[1])
    lotm = inrect & ~road & ~plaza
    side = road & dilate(lotm, 2) & ~plaza

    top = np.full((SX, SZ), I("gray_concrete"), np.uint16)
    rng = np.random.default_rng(5)
    rn = rng.random((SX, SZ))
    asphalt = np.where(rn < 0.16, I("black_concrete"), I("gray_concrete")).astype(np.uint16)
    top[road] = asphalt[road]
    top[side] = I("light_gray_concrete")
    # curb line between sidewalk and carriageway
    # lane markings
    for (a, b) in ROADS:
        main = (a, b) == MAIN
        for axis in (0, 1):
            L = np.arange(SX)
            if axis == 0:   # N-S road, x in [a,b)
                lines = []
                if main:
                    lines = [(159, "yellow_concrete", None), (160, "yellow_concrete", None)]
                    lines += [(x, "white_concrete", 4) for x in (152, 156, 164, 168)]
                else:
                    lines = [(a + 7, "yellow_concrete", None), (a + 8, "yellow_concrete", None)]
                for (xx, nm, dash) in lines:
                    zz = np.arange(CITY[0], CITY[1])
                    ok = (dash is None) | ((zz % 8) < (dash or 8))
                    sel = zz[ok]
                    msk = ~side[xx, sel] & ~plaza[xx, sel]
                    top[xx, sel[msk]] = I(nm)
            else:           # E-W road, z in [a,b)
                lines = []
                if main:
                    lines = [(159, "yellow_concrete", None), (160, "yellow_concrete", None)]
                    lines += [(x, "white_concrete", 4) for x in (152, 156, 164, 168)]
                else:
                    lines = [(a + 7, "yellow_concrete", None), (a + 8, "yellow_concrete", None)]
                for (zz0, nm, dash) in lines:
                    xx = np.arange(CITY[0], CITY[1])
                    ok = (dash is None) | ((xx % 8) < (dash or 8))
                    sel = xx[ok]
                    msk = ~side[sel, zz0] & ~plaza[sel, zz0]
                    top[sel[msk], zz0] = I(nm)
    # intersections: plain asphalt, then zebra crossings
    for (xa, xb) in ROADS:
        for (za, zb) in ROADS:
            reg = (X >= xa) & (X < xb) & (Z >= za) & (Z < zb) & ~plaza & inrect
            top[reg & ~side] = asphalt[reg & ~side]
    for (xa, xb) in ROADS:
        for (za, zb) in ROADS:
            if xa >= PLAZA[0] and xb <= PLAZA[1] and za >= PLAZA[0] and zb <= PLAZA[1]:
                continue
            for (rect, vertical) in (((xa + 2, xb - 2, za - 5, za - 2), True), ((xa + 2, xb - 2, zb + 2, zb + 5), True),
                                     ((xa - 5, xa - 2, za + 2, zb - 2), False), ((xb + 2, xb + 5, za + 2, zb - 2), False)):
                x0, x1, z0, z1 = rect
                reg = (X >= x0) & (X < x1) & (Z >= z0) & (Z < z1) & road & ~side & ~plaza
                stripe = ((X % 2) == 0) if vertical else ((Z % 2) == 0)
                top[reg & stripe] = I("white_concrete")
    # glowing cat's-eyes set into the lane lines: the roads' own light
    zz = np.arange(CITY[0], CITY[1])
    for (a, b) in ROADS:
        if (a, b) == MAIN:
            for xx, k in ((152, 0), (168, 0), (156, 6), (164, 6)):
                for t in zz[(zz % 12) == k]:
                    if not plaza[xx, t] and road[xx, t] and not side[xx, t] and top[xx, t] == I("white_concrete"):
                        top[xx, t] = I("sea_lantern")
                        top[t, xx] = I("sea_lantern") if (road[t, xx] and not side[t, xx] and not plaza[t, xx] and top[t, xx] == I("white_concrete")) else top[t, xx]
            for t in zz[(zz % 12) == 3]:
                for xx in (159,):
                    if not plaza[xx, t] and road[xx, t] and not side[xx, t] and top[xx, t] == I("yellow_concrete"):
                        top[xx, t] = I("ochre_froglight")
                    if not plaza[t, xx] and road[t, xx] and not side[t, xx] and top[t, xx] == I("yellow_concrete"):
                        top[t, xx] = I("ochre_froglight")
        else:
            for t in zz[(zz % 16) == 5]:
                xx = a + 7
                if road[xx, t] and not side[xx, t] and not plaza[xx, t] and top[xx, t] == I("yellow_concrete"):
                    top[xx, t] = I("ochre_froglight")
                if road[t, xx] and not side[t, xx] and not plaza[t, xx] and top[t, xx] == I("yellow_concrete"):
                    top[t, xx] = I("ochre_froglight")
    # manhole covers
    for k in range(40):
        a, b = ROADS[rng.integers(0, len(ROADS))]
        t = int(rng.integers(40, 280))
        if rng.random() < 0.5:
            x, z = int((a + b) // 2 + rng.integers(-3, 4)), t
        else:
            x, z = t, int((a + b) // 2 + rng.integers(-3, 4))
        if inrect[x, z] and road[x, z] and not side[x, z] and not plaza[x, z]:
            top[x, z] = I("polished_deepslate")

    # the plaza
    tile = (((X // 8) + (Z // 8)) % 2) == 0
    pz = np.where(tile, I("polished_andesite"), I("andesite")).astype(np.uint16)
    # joints
    joint = ((X % 8) == 0) | ((Z % 8) == 0)
    pz = np.where(joint & (rn < 0.5), I("smooth_stone"), pz).astype(np.uint16)
    top[plaza] = pz[plaza]
    r = np.hypot(X - 160 + 0.0, Z - 160 + 0.0)
    ring1 = plaza & (r >= 44.0) & (r < 45.5)
    top[ring1] = I("white_concrete")
    ang = np.arctan2(Z - 160.0, X - 160.0)
    dash = (np.floor(ang / (2 * math.pi) * 72) % 2) == 0
    ring2 = plaza & (r >= 30.0) & (r < 31.5) & dash
    top[ring2] = I("yellow_concrete")
    # the main avenues keep their lane lines through the plaza
    for xx in (159, 160):
        sel = (X == xx) & plaza & (r > 31.5) & (r < 44.0)
        top[sel] = I("yellow_concrete")
        sel = (Z == xx) & plaza & (r > 31.5) & (r < 44.0)
        top[sel] = I("yellow_concrete")
    # embedded floodlights
    lamp = plaza & ((X % 16) >= 7) & ((X % 16) <= 8) & ((Z % 16) >= 7) & ((Z % 16) <= 8) & (r > 22)
    top[lamp] = I("sea_lantern")

    # the launch frame and the door tracks
    fr = (X >= 150) & (X < 170) & (Z >= 150) & (Z < 170)
    top[fr] = np.where(((X + Z) // 2) % 2 == 0, I("yellow_concrete"), I("black_concrete"))[fr]
    for lx0, lx1 in ((134, 150), (170, 186)):
        reg = (X >= lx0) & (X < lx1) & (Z >= 150) & (Z < 170)
        top[reg] = I("iron_block")
        seam = reg & (((X - lx0) % 4 == 0) | (Z == 160))
        top[seam] = I("polished_deepslate")
    # parks
    for lot in lots:
        if lot["kind"] in ("park", "open"):
            x0, z0, x1, z1 = lot["rect"]
            top[x0:x1, z0:z1] = I("grass_block")
            pth = np.zeros((SX, SZ), bool)
            pth[x0:x1, z0:z1] = True
            cxm, czm = (x0 + x1) // 2, (z0 + z1) // 2
            top[cxm - 1:cxm + 1, z0:z1] = I("dirt_path")
            top[x0:x1, czm - 1:czm + 1] = I("dirt_path")
            if lot["kind"] == "open":
                top[x0:x1, z0:z1] = I("stone_bricks")
                top[x0 + 1:x1 - 1, z0 + 1:z1 - 1] = I("polished_andesite")
    sx0, sx1 = CITY
    w.a[sx0:sx1, ST - 1, sx0:sx1] = top[sx0:sx1, sx0:sx1]
    c.inrect = inrect
    c.road = road
    c.side = side
    c.plaza = plaza
    return top


# ------------------------------------------------------------------ launch complex
def build_launch(c):
    w, I = c.w, c.I
    # foundation and the carve
    c.box(146, 0, 146, 174, ST - 1, 174, "deepslate")
    c.box(153, 1, 153, 167, ST, 167, "air")
    # floor
    c.box(152, 0, 152, 168, 1, 168, "polished_deepslate")
    # wall cladding with hazard bands, lamp bars and guide rails
    for y in range(1, ST):
        band = y % 8 in (6, 7)
        lampy = y % 8 == 3
        for u in range(14):
            for (px, pz) in ((153 + u, 152), (153 + u, 167), (152, 153 + u), (167, 153 + u)):
                if band:
                    nm = hazard_name(u, y)
                elif lampy and 3 <= u <= 10:
                    nm = "sea_lantern"
                elif u in (2, 11):
                    nm = "polished_deepslate"
                else:
                    nm = "gray_concrete" if (u + y // 8) % 5 else "light_gray_concrete"
                c.put(px, y, pz, nm)
    # the rim of the opening
    for u in range(14):
        for (px, pz) in ((153 + u, 152), (153 + u, 167), (152, 153 + u), (167, 153 + u)):
            c.put(px, ST - 1, pz, hazard_name(px, pz))
    # guide rails (steel strips standing 1 block out of each wall) and chains
    for y in range(1, ST):
        nm = "iron_block" if y % 4 else "chiseled_copper"
        for u in (2, 11):
            c.put(153 + u, y, 153, nm)
            c.put(153 + u, y, 166, nm)
            c.put(153, y, 153 + u, nm)
            c.put(166, y, 153 + u, nm)
    for y in range(8, ST):
        for (px, pz) in ((153, 153), (166, 153), (153, 166), (166, 166)):
            c.put(px, y, pz, "iron_chain[axis=y]")
    # the pad: rim lights, hazard ring, clamps
    c.box(154, 0, 154, 166, 1, 166, "iron_block")
    for u in range(154, 166):
        for v in (154, 165):
            c.put(u, 0, v, hazard_name(u, v))
            c.put(v, 0, u, hazard_name(v, u))
    for u in range(157, 164):
        c.put(u, 0, 157, "sea_lantern")
        c.put(u, 0, 162, "sea_lantern")
    for (px, pz) in ((154, 154), (163, 154), (154, 163), (163, 163)):
        c.box(px, 1, pz, px + 3, 4, pz + 3, "gray_concrete")
        c.box(px, 4, pz, px + 3, 5, pz + 3, hazard_name(px, pz))
        c.put(px + 1, 5, pz + 1, "shroomlight")
    # the lift platform, raised to street level (this is where the giant stands at 'launch_top'); it rides on the
    # four wall rails, so a one-block slot of shaft remains open all the way round it
    # 10 x 10: a solid hazard-striped rim, a steel grating in the middle (so the lit shaft shows through it, and the
    # sky shows through it from below), and four brackets reaching to the wall rails.
    for x in range(155, 165):
        for z in range(155, 165):
            rim = x in (155, 164) or z in (155, 164)
            rim2 = x in (156, 163) or z in (156, 163)
            if rim:
                c.put(x, ST - 1, z, hazard_name(x, z))
                c.put(x, ST - 2, z, "gray_concrete")
                c.put(x, ST - 3, z, "iron_block")
            elif rim2:
                c.put(x, ST - 1, z, "iron_block")
                c.put(x, ST - 2, z, "gray_concrete")
            else:
                c.put(x, ST - 1, z, "copper_grate" if (x + z) % 5 else "iron_block")
    for u in (155, 156, 163, 164):
        for dz in (154, 165):
            c.put(u, ST - 2, dz, "iron_block")
            c.put(dz, ST - 2, u, "iron_block")
    for u in range(156, 164, 2):
        c.put(u, ST - 4, 155, "sea_lantern")
        c.put(u, ST - 4, 164, "sea_lantern")
        c.put(155, ST - 4, u, "sea_lantern")
        c.put(164, ST - 4, u, "sea_lantern")
    # the frame at street level: posts with amber lamps
    for (px, pz) in ((150, 150), (169, 150), (150, 169), (169, 169)):
        c.box(px, ST, pz, px + 1, ST + 3, pz + 1, "iron_block")
        c.put(px, ST + 3, pz, "shroomlight")
    # raised lip of the opening (half-blocks)
    for u in range(152, 168):
        for (px, pz) in ((u, 152), (u, 167), (152, u), (167, u)):
            c.put(px, ST, pz, "yellow_concrete_slab[type=bottom]" if ((px + pz) // 2) % 2 == 0
                  else "black_concrete_slab[type=bottom]")
    # the retracted door leaves lying beside the opening, half a block proud of the street
    for (lx0, lx1) in ((134, 150), (170, 186)):
        for x in range(lx0, lx1):
            for z in range(150, 170):
                edge = x in (lx0, lx1 - 1) or z in (150, 169)
                if edge:
                    nm = ("yellow_concrete_slab[type=bottom]" if ((x + z) // 2) % 2 == 0
                          else "black_concrete_slab[type=bottom]")
                elif (x - lx0) % 4 == 0 or z in (159, 160):
                    nm = "polished_deepslate_slab[type=bottom]"
                else:
                    nm = "gray_concrete_slab[type=bottom]"
                c.put(x, ST, z, nm)
        for z in (153, 166):
            for x in range(lx0 + 2, lx1 - 2, 4):
                c.put(x, ST - 1, z, "sea_lantern")


# ------------------------------------------------------------------ facades and roofs
def make_spec(c, rng, style, tall=False):
    cool = rng.random() < 0.45
    lit = LIT_COOL if cool else LIT_WARM
    names = [n for n, _ in lit]
    ps = np.array([p for _, p in lit], float)
    ps /= ps.sum()
    sp = dict(style=style, lit=names, litp=ps, plit=rng.uniform(0.10, 0.27), base=4, dark="tinted_glass",
              roof=rng.choice(("gray_concrete", "light_gray_concrete", "gray_concrete", "polished_andesite")))
    if style == "glass":
        sp.update(style="curtain", wall=rng.choice(("gray_concrete", "light_gray_concrete", "black_concrete")),
                  trim=rng.choice(("gray_concrete", "polished_deepslate", "light_gray_concrete")))
    elif style == "office":
        sp.update(style=rng.choice(("punched", "ribbon", "ribbon")), wall=rng.choice(WALLS_LIGHT),
                  trim=rng.choice(TRIMS))
    elif style == "apt":
        sp.update(style="apt", wall=rng.choice(WALLS_APT), trim=rng.choice(("light_gray_concrete", "gray_concrete")),
                  plit=rng.uniform(0.12, 0.30))
    elif style == "shop":
        sp.update(style=rng.choice(("ribbon", "punched")), wall=rng.choice(WALLS_APT), trim=rng.choice(TRIMS))
        sp["base"] = 4
    elif style == "warehouse":
        sp.update(style="blank", wall=rng.choice(("light_gray_concrete", "gray_concrete", "stone_bricks")),
                  trim=rng.choice(TRIMS), base=4)
    elif style == "armored":
        sp.update(style="armored", wall="gray_concrete", trim="black_concrete", roof="gray_concrete")
    else:
        sp.update(wall="light_gray_concrete", trim="gray_concrete")
    return sp


def facade_ids(c, sp, L, H, rng, tag=0):
    I = c.I
    u = np.arange(L)[:, None]
    v = np.arange(H)[None, :]
    shape = (L, H)
    st, base = sp["style"], sp["base"]
    wall = np.full(shape, I(sp["wall"]), np.uint16)
    trim = I(sp["trim"])
    out = wall.copy()
    inner = np.broadcast_to((u >= 1) & (u <= L - 2), shape)
    litarr = np.array([I(n) for n in sp["lit"]], np.uint16)
    dark = I(sp["dark"])
    if st == "armored":
        panel = rng.integers(0, 3, (L // 8 + 2, H // 8 + 2))
        pid = np.array([I("gray_concrete"), I("gray_concrete"), I("light_gray_concrete")], np.uint16)
        out = pid[panel[u // 8, v // 8]]
        seam = ((u % 8) == 0) | ((v % 8) == 0)
        out = np.where(seam, I("polished_blackstone"), out)
        haz = (v < 2) | ((v >= H - 4) & (v < H - 1))
        stripe = np.where(((u + v) // 2) % 2 == 0, I("yellow_concrete"), I("black_concrete"))
        out = np.where(haz, stripe, out)
        amber = (v == H - 6) & ((u % 8) == 4)
        out = np.where(amber, I("shroomlight"), out)
        if sp.get("chevron"):
            cx0 = L // 2 - 5
            chev = (u >= cx0) & (u < cx0 + 10) & (v >= 8) & (v < 18)
            out = np.where(chev, stripe, out)
            out = np.where(chev & ((u == cx0) | (u == cx0 + 9) | (v == 8) | (v == 17)), I("black_concrete"), out)
        out = out.astype(np.uint16)
    elif st == "blank":
        seam = ((u % 10) == 0)
        out = np.where(seam, trim, out)
        gate = (u >= L // 2 - 3) & (u < L // 2 + 3) & (v < 5)
        out = np.where(gate, I("iron_block"), out)
        lamp = (v == 6) & ((u % 10) == 5)
        out = np.where(lamp, I("shroomlight"), out)
    else:
        upper = np.broadcast_to((v >= base) & (v <= H - 3), shape)
        if st == "punched":
            win = (((u % 4) == 1) | ((u % 4) == 2)) & (((v % 4) == 1) | ((v % 4) == 2))
            cu, cv = u // 4, v // 4
        elif st == "ribbon":
            win = (((v % 4) == 1) | ((v % 4) == 2)) & ((u % 12) != 0)
            cu, cv = u // 6, v // 4
        elif st == "apt":
            win = ((u % 3) == 1) & (((v % 4) == 1) | ((v % 4) == 2))
            out = np.where((v % 4) == 3, trim, out)
            cu, cv = u // 3, v // 4
        else:  # curtain
            win = ((v % 4) == 1) | ((v % 4) == 2)
            win = win & ((u % 3) != 0)
            cu, cv = u // 3, v // 4
            glass = inner & upper
            out = np.where(glass, dark, out)
            out = np.where(glass & (((u % 3) == 0) | ((v % 4) == 0)), trim, out)
        win = win & inner & upper
        cuM, cvM = int(np.max(cu)) + 1, int(np.max(cv)) + 1
        T = rng.random((cuM, cvM))
        boost = np.where(rng.random(cvM) < 0.09, 0.55, 0.0)
        p = sp["plit"] + boost[np.broadcast_to(cv, shape)]
        lit = T[np.broadcast_to(cu, shape), np.broadcast_to(cv, shape)] < p
        pick = rng.choice(len(litarr), size=shape, p=sp["litp"])
        out = np.where(win, np.where(lit, litarr[pick], dark), out)
        # ground floor: shop fronts
        if base > 0:
            shop = (v >= 1) & (v <= 2) & ((u % 6) >= 1) & ((u % 6) <= 4) & inner
            slit = rng.random(L // 6 + 2)[np.broadcast_to(u // 6, shape)] < 0.45
            out = np.where(np.broadcast_to(v < base, shape), wall, out)
            out = np.where(shop, np.where(slit, litarr[pick], dark), out)
            out = np.where(np.broadcast_to(v == base - 1, shape) & inner, trim, out)
    out = out.astype(np.uint16)
    out[0, :] = wall[0, :] if st != "armored" else out[0, :]
    out[L - 1, :] = wall[L - 1, :] if st != "armored" else out[L - 1, :]
    out[:, H - 1] = trim if st != "armored" else I("black_concrete")
    return out


def prism(c, x0, z0, x1, z1, y0, H, sp, seed):
    """A hollow, windowed tower body.  Row H-1 is the roof plate, the parapet is put on top."""
    w = c.w
    rng = np.random.default_rng(seed)
    L, D = x1 - x0, z1 - z0
    if H < 3 or L < 3 or D < 3 or y0 + H + 4 >= SY:
        return
    w.a[x0:x1, y0:y0 + H, z0] = facade_ids(c, sp, L, H, rng)
    w.a[x0:x1, y0:y0 + H, z1 - 1] = facade_ids(c, sp, L, H, rng)
    w.a[x0, y0:y0 + H, z0:z1] = facade_ids(c, sp, D, H, rng).T
    w.a[x1 - 1, y0:y0 + H, z0:z1] = facade_ids(c, sp, D, H, rng).T
    c.box(x0 + 1, y0 + H - 1, z0 + 1, x1 - 1, y0 + H, z1 - 1, sp["roof"])
    if sp["style"] == "armored":
        c.ring(x0, z0, x1, z1, y0 + H, sp["trim"], 1)
        c.ring(x0 + 1, z0 + 1, x1 - 1, z1 - 1, y0 + H, sp["trim"], 1)
    else:
        c.ring(x0, z0, x1, z1, y0 + H, sp["trim"], 1)


def roof_clutter(c, x0, z0, x1, z1, yr, rng, n, tall_total, sp):
    """yr is the first free level above the roof plate (the parapet is at yr)."""
    w = c.w
    W, D = x1 - x0, z1 - z0
    occ = np.zeros((W, D), bool)

    def fit(sx, sz):
        if W - 4 < sx or D - 4 < sz:
            return None
        for _ in range(14):
            ax = rng.randint(2, W - 2 - sx)
            az = rng.randint(2, D - 2 - sz)
            if not occ[ax - 1:ax + sx + 1, az - 1:az + sz + 1].any():
                occ[ax:ax + sx, az:az + sz] = True
                return x0 + ax, az + z0
        return None

    # aircraft warning mast on tall roofs
    if tall_total >= 30:
        p = fit(1, 1)
        if p:
            hh = rng.randint(6, 14) + (tall_total // 8)
            for i in range(hh):
                c.put(p[0], yr + i, p[1], "iron_chain[axis=y]")
            c.put(p[0], yr + hh, p[1], "red_concrete")
            c.put(p[0], yr + hh + 1, p[1], "light[level=14]")
            c.put(p[0], yr + hh - 1, p[1], "iron_chain[axis=y]")
    for _ in range(n):
        kind = rng.choice(("ac", "ac", "ac", "tank", "tank", "house", "pipe", "vent", "bill", "ant", "solar"))
        if kind == "ac":
            sx, sz = rng.choice(((2, 2), (3, 2), (2, 3), (4, 2)))
            p = fit(sx, sz)
            if p:
                c.box(p[0], yr, p[1], p[0] + sx, yr + 1, p[1] + sz, "light_gray_concrete")
                c.box(p[0], yr + 1, p[1], p[0] + sx, yr + 2, p[1] + sz, "iron_trapdoor[half=top,facing=north,open=false]")
        elif kind == "tank":
            p = fit(5, 5)
            if p:
                body = rng.choice(("light_gray_concrete", "oxidized_copper", "white_concrete", "orange_terracotta"))
                for dx in range(5):
                    for dz in range(5):
                        if (dx - 2) ** 2 + (dz - 2) ** 2 <= 6:
                            for dy in range(2, 6):
                                c.put(p[0] + dx, yr + dy, p[1] + dz, body)
                            c.put(p[0] + dx, yr + 6, p[1] + dz, "iron_block")
                for (dx, dz) in ((0, 1), (4, 1), (0, 3), (4, 3), (1, 0), (3, 4)):
                    for dy in range(0, 2):
                        c.put(p[0] + dx, yr + dy, p[1] + dz, "stone_brick_wall")
                c.put(p[0] + 2, yr + 7, p[1] + 2, "iron_chain[axis=y]")
        elif kind == "house":
            sx, sz = rng.choice(((4, 4), (5, 4), (4, 5), (6, 5)))
            p = fit(sx, sz)
            if p:
                c.box(p[0], yr, p[1], p[0] + sx, yr + 3, p[1] + sz, "light_gray_concrete")
                c.box(p[0], yr + 3, p[1], p[0] + sx, yr + 4, p[1] + sz, "gray_concrete")
                c.put(p[0], yr, p[1] + 1, "iron_door[facing=west,half=lower,hinge=left,open=false,powered=false]")
                c.put(p[0], yr + 1, p[1] + 1, "iron_door[facing=west,half=upper,hinge=left,open=false,powered=false]")
                c.put(p[0] - 1, yr, p[1] + 1, "stone_slab[type=bottom]") if False else None
        elif kind == "pipe":
            ln = rng.randint(6, 12)
            if rng.random() < 0.5:
                p = fit(ln, 1)
                if p:
                    c.box(p[0], yr, p[1], p[0] + ln, yr + 1, p[1] + 1, "iron_block")
            else:
                p = fit(1, ln)
                if p:
                    c.box(p[0], yr, p[1], p[0] + 1, yr + 1, p[1] + ln, "iron_block")
        elif kind == "vent":
            p = fit(4, 4)
            if p:
                c.box(p[0], yr, p[1], p[0] + 4, yr + 3, p[1] + 4, "iron_block")
                c.box(p[0] + 1, yr + 3, p[1] + 1, p[0] + 3, yr + 4, p[1] + 3, "copper_grate")
        elif kind == "bill":
            if tall_total < 38:
                p = fit(10, 3)
                if p:
                    col = rng.choice(SIGN_COLORS)
                    ln = rng.choice((8, 10))
                    c.box(p[0], yr, p[1], p[0] + ln, yr + 3, p[1] + 1, "iron_bars")
                    c.box(p[0], yr + 3, p[1], p[0] + ln, yr + 8, p[1] + 1, "gray_concrete")
                    c.box(p[0] + 1, yr + 4, p[1] + 1, p[0] + ln - 1, yr + 7, p[1] + 2, col)
                    c.box(p[0] + 1, yr + 4, p[1] - 1, p[0] + ln - 1, yr + 7, p[1], col)
                    for xx in range(p[0] + 2, p[0] + ln - 1, 3):
                        c.put(xx, yr + 5, p[1] + 2, "light[level=13]")
                        c.put(xx, yr + 5, p[1] - 2, "light[level=13]")
        elif kind == "ant":
            p = fit(1, 1)
            if p:
                hh = rng.randint(6, 16)
                for i in range(hh):
                    c.put(p[0], yr + i, p[1], "iron_chain[axis=y]")
                c.put(p[0], yr + hh - 4, p[1], "iron_block")
        elif kind == "solar":
            p = fit(6, 3)
            if p:
                for dx in range(6):
                    for dz in range(3):
                        c.put(p[0] + dx, yr, p[1] + dz, "daylight_detector[inverted=true]")


def blade_sign(c, x, z, y, axis, rng, h=None):
    """A vertical neon sign standing 1 block off a facade.  axis 'x' means the sign plane is x-constant."""
    h = h or rng.randint(8, 16)
    a, b = rng.choice(NEON), rng.choice(NEON)
    for dy in range(h):
        nm = a if (dy % 4) != 3 else "black_concrete"
        for k in range(2):
            if axis == "x":
                c.put(x, y + dy, z + k, nm if k == 0 else b if (dy % 4) != 3 else "black_concrete")
            else:
                c.put(x + k, y + dy, z, nm if k == 0 else b if (dy % 4) != 3 else "black_concrete")


# ------------------------------------------------------------------ ordinary buildings
def make_building(c, lot, ring, dist):
    rng = c.rng
    x0, z0, x1, z1 = lot["rect"]
    W, D = x1 - x0, z1 - z0
    if lot.get("style"):
        style = lot["style"]
    else:
        if ring:
            tbl = (("glass", 4), ("office", 3), ("apt", 2), ("armored", 1))
        elif dist <= 78:
            tbl = (("glass", 4), ("office", 4), ("apt", 1), ("armored", 1), ("shop", 1))
        else:
            tbl = (("glass", 2), ("office", 3), ("apt", 3), ("armored", 1), ("shop", 2), ("warehouse", 1))
        pool = [n for n, k in tbl for _ in range(k)]
        style = rng.choice(pool)
        if min(W, D) < 11 and style in ("glass", "office"):
            style = rng.choice(("shop", "apt"))
    hr = dict(glass=(22, 46), office=(14, 36), apt=(14, 30), armored=(18, 30), shop=(8, 14), warehouse=(8, 12),
              house=(6, 7), open=(0, 0))[style]
    H = rng.randint(*hr)
    if ring and style not in ("house", "open", "warehouse", "shop"):
        H = rng.randint(38, 62)
    elif dist <= 78 and style in ("glass", "office"):
        H = min(64, H + rng.randint(2, 10))
    if style == "open":
        lot["kind"] = "open"
        return "open"
    if style == "house":
        lot["kind"] = "house"
        return "house"
    seed = x0 * 1000 + z0 * 7 + 3
    sp = make_spec(c, rng, style, tall=H >= 34)
    # setbacks for tall ones
    if style in ("glass", "office") and H >= 28 and W >= 16 and D >= 16 and rng.random() < 0.65:
        hp = rng.randint(7, 12)
        ins = rng.randint(2, 4)
        pod = dict(make_spec(c, rng, "office"))
        prism(c, x0, z0, x1, z1, ST, hp, pod, seed)
        roof_clutter(c, x0, z0, x1, z1, ST + hp, rng, 3, hp, pod)
        t0 = (x0 + ins, z0 + ins, x1 - ins, z1 - ins)
        Ht = H - hp
        prism(c, *t0, ST + hp, Ht, sp, seed + 11)
        if Ht >= 24 and (t0[2] - t0[0]) >= 12 and (t0[3] - t0[1]) >= 12 and rng.random() < 0.5:
            i2 = 2
            h2 = 7
            prism(c, t0[0] + i2, t0[1] + i2, t0[2] - i2, t0[3] - i2, ST + H, h2, sp, seed + 13)
            roof_clutter(c, t0[0] + i2, t0[1] + i2, t0[2] - i2, t0[3] - i2, ST + H + h2, rng, 3, H + h2, sp)
            roof_clutter(c, *t0, ST + H, rng, 2, 0, sp)
            tot = H + h2
        else:
            roof_clutter(c, *t0, ST + H, rng, 2 + (t0[2] - t0[0]) * (t0[3] - t0[1]) // 90, H, sp)
            tot = H
    else:
        prism(c, x0, z0, x1, z1, ST, H, sp, seed)
        roof_clutter(c, x0, z0, x1, z1, ST + H, rng, 2 + W * D // 80, H, sp)
        tot = H
    if style == "armored":
        # a gate in the base of one face and a rim of floodlights
        pass
    lot["height"] = tot
    return style


def build_house(c, lot):
    rng = c.rng
    x0, z0, x1, z1 = lot["rect"]
    parts = subdivide(rng, x0, z0, x1, z1, 14, 9, gap=2)
    for (a, b, cc, d) in parts:
        a, b, cc, d = a + 1, b + 1, cc - 1, d - 1
        W, D = cc - a, d - b
        if W < 7 or D < 7:
            continue
        hw = rng.randint(5, 7)
        wall = rng.choice(("white_concrete", "light_gray_concrete", "white_terracotta", "calcite", "smooth_stone"))
        sp = dict(style="punched", wall=wall, trim="gray_concrete", lit=[n for n, _ in LIT_WARM],
                  litp=np.array([p for _, p in LIT_WARM], float) / 10.0, plit=0.22, base=0, dark="tinted_glass",
                  roof="gray_concrete")
        prism(c, a, b, cc, d, ST, hw, sp, a * 131 + b)
        roof = rng.choice(("deepslate_tile", "stone_brick", "polished_blackstone_brick", "deepslate_tile"))
        yt = ST + hw
        # clear the cornice ring so the gable starts cleanly
        if D >= W:      # ridge along z, slopes in x
            half = W // 2
            for k in range(half):
                for zz in range(b - 1 if False else b, d):
                    c.put(a + k, yt + k, zz, roof + "_stairs[facing=east,half=bottom,shape=straight]")
                    c.put(cc - 1 - k, yt + k, zz, roof + "_stairs[facing=west,half=bottom,shape=straight]")
                for xx in range(a + k + 1, cc - 1 - k):
                    c.put(xx, yt + k, b, wall)
                    c.put(xx, yt + k, d - 1, wall)
            if W % 2:
                for zz in range(b, d):
                    c.put(a + half, yt + half, zz, roof + "_slab[type=bottom]")
        else:
            half = D // 2
            for k in range(half):
                for xx in range(a, cc):
                    c.put(xx, yt + k, b + k, roof + "_stairs[facing=south,half=bottom,shape=straight]")
                    c.put(xx, yt + k, d - 1 - k, roof + "_stairs[facing=north,half=bottom,shape=straight]")
                for zz in range(b + k + 1, d - 1 - k):
                    c.put(a, yt + k, zz, wall)
                    c.put(cc - 1, yt + k, zz, wall)
            if D % 2:
                for xx in range(a, cc):
                    c.put(xx, yt + half, b + half, roof + "_slab[type=bottom]")
        # a tree or two in the yard
        if rng.random() < 0.6:
            tree_round(c, rng.choice((a - 1, cc)), ST, rng.randint(b, d - 1), rng, "oak", (5, 8))


def subdivide(rng, x0, z0, x1, z1, maxs, mins, gap=1):
    out = []

    def rec(x0, z0, x1, z1):
        W, D = x1 - x0, z1 - z0
        splitx = W >= D
        L = W if splitx else D
        if L <= maxs or (L <= maxs * 1.35 and rng.random() < 0.35):
            out.append((x0, z0, x1, z1))
            return
        g = rng.choice((gap, gap + 1)) if gap else 0
        lo, hi = mins, L - mins - g
        if hi < lo:
            out.append((x0, z0, x1, z1))
            return
        s = rng.randint(lo, hi)
        if splitx:
            rec(x0, z0, x0 + s, z1)
            rec(x0 + s + g, z0, x1, z1)
        else:
            rec(x0, z0, x1, z0 + s)
            rec(x0, z0 + s + g, x1, z1)

    rec(x0, z0, x1, z1)
    return out


# ------------------------------------------------------------------ landmark towers
def tiers(c, cx, cz, base_w, specs, y0, seed):
    """Stacked prisms centred on (cx, cz); specs: [(inset_from_base, height, spec)]."""
    y = y0
    for k, (inset, h, sp) in enumerate(specs):
        hw = base_w // 2 - inset
        prism(c, cx - hw, cz - hw, cx + hw, cz + hw, y, h, sp, seed + k)
        y += h
    return y


def landmark_spire(c, rect):
    rng = c.rng
    x0, z0, x1, z1 = rect
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    pod = make_spec(c, rng, "office")
    gl = make_spec(c, rng, "glass")
    gl.update(wall="black_concrete", trim="polished_deepslate", plit=0.2)
    top = make_spec(c, rng, "glass")
    top.update(wall="light_gray_concrete", trim="white_concrete", plit=0.3)
    y = tiers(c, cx, cz, 28, [(0, 12, pod), (4, 30, gl), (5, 16, gl), (7, 8, top)], ST, 900)
    # neon ring at 2/3 height
    c.ring(cx - 6, cz - 6, cx + 6, cz + 6, ST + 42, "sea_lantern", 1)
    # crown and spire
    c.ring(cx - 3, cz - 3, cx + 3, cz + 3, y, "iron_block", 2)
    for i in range(22):
        c.put(cx, y + i, cz, "iron_chain[axis=y]")
    for i in range(0, 12):
        c.put(cx, y + i, cz, "iron_block")
    c.put(cx, y + 22, cz, "red_concrete")
    c.put(cx, y + 23, cz, "light[level=15]")
    for (dx, dz) in ((-5, -5), (4, -5), (-5, 4), (4, 4)):
        c.put(cx + dx, ST + 12, cz + dz, "red_concrete")
    # podium roof gets billboards/clutter
    roof_clutter(c, cx - 14, cz - 14, cx + 14, cz + 14, ST + 12, rng, 5, 12, pod)
    return y + 23


def landmark_stepped(c, rect):
    rng = c.rng
    x0, z0, x1, z1 = rect
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    s1 = make_spec(c, rng, "office")
    s1.update(style="ribbon", wall="light_gray_concrete", trim="gray_concrete", plit=0.22)
    s2 = make_spec(c, rng, "office")
    s2.update(style="punched", wall="white_concrete", trim="gray_concrete", plit=0.22)
    y = tiers(c, cx, cz, 28, [(0, 10, s1), (3, 24, s2), (6, 18, s2), (9, 10, s1)], ST, 940)
    # helipad
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            r = math.hypot(dx, dz)
            if 3.0 <= r < 4.2:
                c.put(cx + dx, y - 1, cz + dz, "yellow_concrete")
            elif r < 3.0:
                c.put(cx + dx, y - 1, cz + dz, "black_concrete")
    for dz in range(-2, 3):
        c.put(cx - 1, y - 1, cz + dz, "white_concrete")
        c.put(cx + 1, y - 1, cz + dz, "white_concrete")
    c.put(cx, y - 1, cz, "white_concrete")
    for (dx, dz) in ((-4, -4), (4, -4), (-4, 4), (4, 4), (0, -5), (0, 5), (-5, 0), (5, 0)):
        c.put(cx + dx, y, cz + dz, "red_concrete")
        c.put(cx + dx, y + 1, cz + dz, "light[level=12]")
    c.ring(cx - 6, cz - 6, cx + 7, cz + 7, y, "polished_deepslate", 1)
    for i in range(14):
        c.put(cx + 5, y + i, cz + 5, "iron_chain[axis=y]")
    c.put(cx + 5, y + 14, cz + 5, "red_concrete")
    c.put(cx + 5, y + 15, cz + 5, "light[level=14]")
    # lower roofs
    roof_clutter(c, cx - 14, cz - 14, cx + 14, cz + 14, ST + 10, rng, 4, 10, s1)
    return y + 14


def landmark_round(c, cx, cz, R, H):
    rng = c.rng
    I = c.I
    sp = make_spec(c, rng, "glass")
    sp.update(wall="gray_concrete", trim="light_gray_concrete", plit=0.25)
    litarr = np.array([I(n) for n in sp["lit"]], np.uint16)
    rn = np.random.default_rng(cx * 7 + cz)
    N = int(2 * math.pi * R / 3)
    tbl = rn.random((N + 1, H // 4 + 2))
    for dx in range(-R - 1, R + 2):
        for dz in range(-R - 1, R + 2):
            r = math.hypot(dx, dz)
            if r > R + 0.5:
                continue
            shell = r > R - 1.0
            ang = math.atan2(dz, dx)
            k = int((ang + math.pi) / (2 * math.pi) * N)
            for v in range(H):
                if not shell:
                    if v == H - 1:
                        c.put(cx + dx, ST + v, cz + dz, "light_gray_concrete")
                    continue
                if v == H - 1:
                    nm = "white_concrete"
                elif v < 4:
                    nm = "light_gray_concrete" if v in (0, 3) else (
                        sp["lit"][0] if tbl[k, 0] < 0.4 and k % 2 == 0 else "tinted_glass")
                elif v % 4 == 0 or k % 3 == 0:
                    nm = "gray_concrete"
                elif v % 4 in (1, 2) and tbl[k, v // 4] < sp["plit"]:
                    nm = rng.choice(sp["lit"])
                else:
                    nm = "tinted_glass"
                c.put(cx + dx, ST + v, cz + dz, nm)
    # neon ring near the top and a crown
    for dx in range(-R - 1, R + 2):
        for dz in range(-R - 1, R + 2):
            r = math.hypot(dx, dz)
            if R - 1.0 < r <= R + 0.5:
                c.put(cx + dx, ST + H - 4, cz + dz, "sea_lantern")
                c.put(cx + dx, ST + H, cz + dz, "light_gray_concrete")
    for i in range(16):
        c.put(cx, ST + H + i, cz, "iron_chain[axis=y]")
    c.put(cx, ST + H + 16, cz, "red_concrete")
    c.put(cx, ST + H + 17, cz, "light[level=15]")
    return ST + H + 17


def landmark_lattice(c, cx, cz):
    """A red-and-white steel lattice tower."""
    top_y = 64
    levels = [0, 8, 16, 24, 32, 40, 48, 56, 64]

    def hw(y):
        return max(1.0, 12.5 * (1 - y / 70.0) ** 1.6 + 1.0)

    def col(y):
        return "red_concrete" if (y // 8) % 2 == 0 else "white_concrete"

    pts = {}
    for y in range(0, top_y + 1):
        h = hw(y)
        nm = col(y)
        for sx in (-1, 1):
            for sz in (-1, 1):
                px, pz = cx + int(round(sx * h)), cz + int(round(sz * h))
                for dx in (0, 1 if sx > 0 else -1):
                    for dz in (0, 1 if sz > 0 else -1):
                        if h >= 3 or (dx == 0 and dz == 0):
                            c.put(px + dx * 0, ST + y, pz + dz * 0, nm)
                            c.put(px - (1 if sx > 0 else -1) * 0 + (dx if h >= 4 else 0), ST + y, pz + (dz if h >= 4 else 0), nm)
    for a, b in zip(levels[:-1], levels[1:]):
        for (sx, sz) in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            pass
        ha, hb = hw(a), hw(b)
        corners_a = [(cx + int(round(sx * ha)), cz + int(round(sz * ha))) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        corners_b = [(cx + int(round(sx * hb)), cz + int(round(sz * hb))) for sx, sz in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        nm = col(a)
        for k in range(4):
            k2 = (k + 1) % 4
            # horizontal ring members
            c.line((corners_a[k][0], ST + a, corners_a[k][1]), (corners_a[k2][0], ST + a, corners_a[k2][1]), nm)
            # X braces
            c.line((corners_a[k][0], ST + a, corners_a[k][1]), (corners_b[k2][0], ST + b, corners_b[k2][1]), nm)
            c.line((corners_a[k2][0], ST + a, corners_a[k2][1]), (corners_b[k][0], ST + b, corners_b[k][1]), nm)
    # observation decks
    for (yy, r, hh) in ((26, 6, 4), (46, 3, 3)):
        c.box(cx - r, ST + yy, cz - r, cx + r + 1, ST + yy + hh, cz + r + 1, "light_gray_concrete")
        for dx in range(-r, r + 1):
            for dz in range(-r, r + 1):
                if abs(dx) == r or abs(dz) == r:
                    for dy in (1, 2) if hh == 4 else (1,):
                        c.put(cx + dx, ST + yy + dy, cz + dz,
                              "sea_lantern" if (dx + dz) % 2 == 0 else "tinted_glass")
        c.box(cx - r - 1, ST + yy, cz - r - 1, cx + r + 2, ST + yy + 1, cz + r + 2, "red_concrete")
    # feet and floodlights
    for sx in (-1, 1):
        for sz in (-1, 1):
            px, pz = cx + int(round(sx * hw(0))), cz + int(round(sz * hw(0)))
            c.box(px - 1, ST, pz - 1, px + 2, ST + 2, pz + 2, "gray_concrete")
            c.put(px + sx * 2, ST, pz + sz * 2, "sea_lantern")
    for i in range(18):
        c.put(cx, ST + top_y + i, cz, "iron_chain[axis=y]")
    c.put(cx, ST + top_y + 18, cz, "red_concrete")
    c.put(cx, ST + top_y + 19, cz, "light[level=15]")
    return ST + top_y + 19


def landmark_twin(c, rect):
    rng = c.rng
    x0, z0, x1, z1 = rect
    sp1 = make_spec(c, rng, "glass")
    sp1.update(wall="black_concrete", trim="gray_concrete", plit=0.22)
    sp2 = make_spec(c, rng, "glass")
    sp2.update(wall="gray_concrete", trim="light_gray_concrete", plit=0.24)
    pod = make_spec(c, rng, "office")
    prism(c, x0 + 2, z0 + 10, x1 - 2, z1 - 10, ST, 8, pod, 960)
    prism(c, x0 + 3, z0 + 11, x0 + 19, z1 - 11, ST + 8, 44, sp1, 961)
    prism(c, x1 - 19, z0 + 11, x1 - 3, z1 - 11, ST + 8, 50, sp2, 962)
    ya, yb = ST + 8 + 44, ST + 8 + 50
    # skybridge
    c.box(x0 + 19, ST + 40, z0 + 15, x1 - 19, ST + 44, z1 - 15, "gray_concrete")
    c.box(x0 + 19, ST + 41, z0 + 16, x1 - 19, ST + 43, z1 - 16, "sea_lantern")
    for (xx, yy, tp) in ((x0 + 10, ya, 1), (x1 - 11, yb, 2)):
        for i in range(12):
            c.put(xx, yy + i, (z0 + z1) // 2, "iron_chain[axis=y]")
        c.put(xx, yy + 12, (z0 + z1) // 2, "red_concrete")
        c.put(xx, yy + 13, (z0 + z1) // 2, "light[level=14]")
    roof_clutter(c, x0 + 3, z0 + 11, x0 + 19, z1 - 11, ya, rng, 2, 0, sp1)
    roof_clutter(c, x1 - 19, z0 + 11, x1 - 3, z1 - 11, yb, rng, 2, 0, sp2)
    return yb + 14


# ------------------------------------------------------------------ armored buildings, weapons, power
def armored_spec(c, rng, chevron=False):
    sp = make_spec(c, rng, "armored")
    sp["chevron"] = chevron
    return sp


def shutter_front(c, x0, z0, x1, z1, y0, face, width, top_v, bot_v, open_half):
    """A roller-shutter in one face of an armored block.  face in n,s,e,w."""
    I = c.I
    L = (x1 - x0) if face in "ns" else (z1 - z0)
    u0 = (L - width) // 2
    for u in range(u0 - 1, u0 + width + 1):
        for v in range(bot_v - 1, top_v + 1):
            edge = u in (u0 - 1, u0 + width) or v in (bot_v - 1, top_v)
            if face == "n":
                p = (x0 + u, y0 + v, z0)
            elif face == "s":
                p = (x0 + u, y0 + v, z1 - 1)
            elif face == "w":
                p = (x0, y0 + v, z0 + u)
            else:
                p = (x1 - 1, y0 + v, z0 + u)
            if edge:
                nm = hazard_name(u, v)
            else:
                vv = v - bot_v
                if open_half and vv >= (top_v - bot_v) // 2:
                    nm = "air"
                else:
                    nm = "light_gray_concrete" if vv % 2 == 0 else "gray_concrete"
                    if vv == (top_v - bot_v) - 1:
                        nm = "polished_blackstone"
                    if u == u0 + width // 2:
                        nm = "polished_blackstone"
            c.put(p[0], p[1], p[2], nm)
    # amber lamps either side of the shutter
    for u in (u0 - 3, u0 + width + 2):
        for v in (bot_v + 2, top_v - 2):
            if face == "n":
                c.put(x0 + u, y0 + v, z0, "shroomlight")
            elif face == "s":
                c.put(x0 + u, y0 + v, z1 - 1, "shroomlight")
            elif face == "w":
                c.put(x0, y0 + v, z0 + u, "shroomlight")
            else:
                c.put(x1 - 1, y0 + v, z0 + u, "shroomlight")


def gun_inside(c, x0, z0, x1, z1, y0, face, width, bot_v, top_v):
    """A gun barrel seen through the opened shutter: a 4x4 tube ending flush with the face."""
    L = (x1 - x0) if face in "ns" else (z1 - z0)
    mid = L // 2
    yc = y0 + bot_v + (top_v - bot_v) * 3 // 4
    for t in range(0, 12):
        for a in range(-2, 2):
            for b in range(-2, 2):
                ring_ = max(abs(a + 0.5), abs(b + 0.5)) > 1.0
                nm = "gray_concrete" if ring_ else "black_concrete"
                if t == 0 and not ring_:
                    nm = "air"
                if face == "e":
                    p = (x1 - 2 - t, yc + b, z0 + mid + a)
                elif face == "w":
                    p = (x0 + 1 + t, yc + b, z0 + mid + a)
                elif face == "n":
                    p = (x0 + mid + a, yc + b, z0 + 1 + t)
                else:
                    p = (x0 + mid + a, yc + b, z1 - 2 - t)
                c.put(p[0], p[1], p[2], nm)
    # glow behind
    if face == "e":
        c.box(x1 - 5, yc - 3, z0 + mid - 3, x1 - 4, yc + 3, z0 + mid + 3, "air")
        c.put(x1 - 6, yc + 3, z0 + mid, "shroomlight")
        c.put(x1 - 6, yc - 3, z0 + mid, "shroomlight")
    elif face == "w":
        c.put(x0 + 5, yc + 3, z0 + mid, "shroomlight")
        c.put(x0 + 5, yc - 3, z0 + mid, "shroomlight")


def build_weapon(c, lot, which):
    rng = c.rng
    x0, z0, x1, z1 = lot["rect"]
    face = lot["face"]
    H = 34
    sp = armored_spec(c, rng)
    prism(c, x0, z0, x1, z1, ST, H, sp, 700 + which)
    # shutter in the face toward the avenue
    shutter_front(c, x0, z0, x1, z1, ST, face, 24, 20, 5, open_half=(which == 1))
    if which == 1:
        gun_inside(c, x0, z0, x1, z1, ST, face, 24, 5, 20)
    # roof: radar, vents, red lights
    roof_clutter(c, x0, z0, x1, z1, ST + H, c.rng, 4, H, sp)
    # missile-rack roof boxes
    for k in range(3):
        bx = x0 + 3 + k * 4
        c.box(bx, ST + H, z0 + 6, bx + 3, ST + H + 3, z0 + 13, "gray_concrete")
        c.box(bx, ST + H + 3, z0 + 6, bx + 3, ST + H + 4, z0 + 13, hazard_name(bx, k))
    lot["height"] = H


def build_bunker(c, lot, idx):
    """Cover near the plaza: heavy armored blocks, about 30 tall; four different silhouettes."""
    rng = c.rng
    x0, z0, x1, z1 = lot["rect"]
    H = 30
    sp = armored_spec(c, rng, chevron=(idx in (0, 2)))
    prism(c, x0, z0, x1, z1, ST, H, sp, 600 + idx)
    # hazard apron around the base
    c.ring(x0 - 1, z0 - 1, x1 + 1, z1 + 1, ST - 1, "yellow_concrete", 1)
    if idx == 0:
        # raised central boss and chamfered corners
        c.box(x0 + 3, ST + H + 1, z0 + 3, x1 - 3, ST + H + 5, z1 - 3, "gray_concrete")
        c.box(x0 + 3, ST + H + 5, z0 + 3, x1 - 3, ST + H + 6, z1 - 3, "yellow_concrete")
        for (px, pz) in ((x0 + 1, z0 + 1), (x1 - 2, z0 + 1), (x0 + 1, z1 - 2), (x1 - 2, z1 - 2)):
            c.put(px, ST + H + 1, pz, "shroomlight")
    elif idx == 1:
        # radar mast with a dish
        mx, mz = (x0 + x1) // 2, (z0 + z1) // 2
        for i in range(10):
            c.put(mx, ST + H + 1 + i, mz, "iron_block")
        for dx in range(-3, 4):
            for dz in range(-3, 4):
                r = math.hypot(dx, dz)
                if 1.5 <= r <= 3.3:
                    c.put(mx + dx, ST + H + 10 + int(r // 2), mz + dz, "iron_block")
        c.put(mx, ST + H + 11, mz, "red_concrete")
        c.put(mx, ST + H + 12, mz, "light[level=14]")
    elif idx == 2:
        # vertical armor fins on the sides
        for yy in range(ST + 2, ST + H - 2):
            for xx in range(x0 + 2, x1 - 2, 4):
                c.put(xx, yy, z0 - 1, "polished_blackstone")
                c.put(xx, yy, z1, "polished_blackstone")
        c.box(x0 + 2, ST + H + 1, z0 + 2, x1 - 2, ST + H + 3, z1 - 2, "iron_block")
    else:
        # sloped shoulders: stair rim and shutter on the plaza face
        for k in range(3):
            c.ring(x0 + k, z0 + k, x1 - k, z1 - k, ST + H + 1 + k, "gray_concrete", 1)
        shutter_front(c, x0, z0, x1, z1, ST, "e", 8, 14, 3, open_half=False)
    lot["height"] = H


def build_power(c):
    """The power-cable socket building: a tall armored block with a huge socket in its west face."""
    rng = c.rng
    x0, z0, x1, z1 = 208, 128, 240, 146
    H = 54
    sp = armored_spec(c, rng)
    sp["wall"] = "gray_concrete"
    prism(c, x0, z0, x1, z1, ST, H, sp, 800)
    zc = 137
    yc = ST + 22
    # protruding plate (into the ring road by one block), then the recessed socket
    for dz in range(-8, 8):
        for dy in range(-8, 9):
            edge = dz in (-8, 7) or dy in (-8, 8)
            nm = hazard_name(dz, dy) if edge else ("iron_block" if (dz + dy) % 5 else "chiseled_copper")
            c.put(207, yc + dy, zc + dz, nm)
            c.put(208, yc + dy, zc + dz, nm)
    for dz in range(-4, 4):
        for dy in range(-4, 5):
            for dx in range(0, 4):
                c.put(207 + dx, yc + dy, zc + dz, "polished_blackstone" if dx == 3 else "air")
    for dz in range(-4, 4):
        for dy in range(-4, 5):
            c.put(207, yc + dy, zc + dz, "yellow_concrete" if (dz in (-4, 3) or dy in (-4, 4)) else "air")
    # contact bars
    for dy in (-2, 2):
        for dz in range(-3, 3):
            c.put(209, yc + dy, zc + dz, "copper_block")
            c.put(208, yc + dy, zc + dz, "copper_block")
    for dy in range(-3, 4):
        c.put(209, yc + dy, zc, "waxed_oxidized_copper")
        c.put(209, yc + dy, zc - 1, "waxed_oxidized_copper")
    for (dz, dy) in ((-7, -7), (6, -7), (-7, 7), (6, 7)):
        c.put(206, yc + dy, zc + dz, "shroomlight")
    # thick cables from the ground into the plate
    for (cz0) in (zc - 6, zc + 5):
        for y in range(ST, yc - 8):
            for dz in range(0, 2):
                for dx in range(0, 2):
                    c.put(206 + dx, y, cz0 + dz, "black_concrete")
        for dz in range(0, 2):
            c.put(206, yc - 9, cz0 + dz, "iron_block")
    # warning light bars
    for y in range(ST + 6, ST + H - 4, 12):
        for zz in range(z0 + 2, z1 - 2, 3):
            c.put(208, y, zz, "red_concrete")
            c.put(207, y, zz, "light[level=10]")
    # the transformer yard to the east
    c.box(240, ST, 128, 248, ST + 1, 146, "light_gray_concrete")
    for zz in (131, 138, 143):
        c.box(241, ST + 1, zz - 1, 246, ST + 5, zz + 2, "iron_block")
        for xx in (242, 244):
            for i in range(4):
                c.put(xx, ST + 5 + i, zz, "iron_chain[axis=y]")
    c.ring(240, 128, 248, 146, ST + 1, "iron_bars", 2)
    roof_clutter(c, x0, z0, x1, z1, ST + H, rng, 4, H, sp)
    # antennas
    for xx in (214, 226, 236):
        for i in range(18):
            c.put(xx, ST + H + i, 133, "iron_chain[axis=y]")
        c.put(xx, ST + H + 18, 133, "red_concrete")
        c.put(xx, ST + H + 19, 133, "light[level=14]")
    return dict(socket=(207, yc, zc))


# ------------------------------------------------------------------ parks, lamps and street props
def lamp_post(c, x, z, h=10, head="glowstone"):
    for i in range(h):
        c.put(x, ST + i, z, "iron_chain[axis=y]")
    c.put(x, ST + h, z, head)
    c.put(x, ST + h + 1, z, "iron_chain[axis=y]")
    c.put(x, ST + h - 1, z, "iron_block")


def build_park(c, lot):
    rng = c.rng
    x0, z0, x1, z1 = lot["rect"]
    W, D = x1 - x0, z1 - z0
    n = max(3, W * D // 70)
    for _ in range(n):
        x = rng.randint(x0 + 2, x1 - 3)
        z = rng.randint(z0 + 2, z1 - 3)
        if abs(x - (x0 + x1) // 2) <= 2 or abs(z - (z0 + z1) // 2) <= 2:
            continue
        tree_round(c, x, ST, z, rng, rng.choice(("oak", "oak", "cherry")), (8, 13))
    if lot["kind"] == "park" and rng.random() < 0.7 and W >= 16 and D >= 14:
        px, pz = x0 + 3, z0 + 3
        sp = dict(style="ribbon", wall="white_concrete", trim="gray_concrete", lit=["sea_lantern"],
                  litp=np.array([1.0]), plit=0.5, base=0, dark="tinted_glass", roof="gray_concrete")
        prism(c, px, pz, px + 10, pz + 8, ST, 7, sp, px * 3 + pz)
    for (x, z) in ((x0 + 1, z0 + 1), (x1 - 2, z0 + 1), (x0 + 1, z1 - 2), (x1 - 2, z1 - 2)):
        lamp_post(c, x, z, 6, "sea_lantern")


def build_open(c, lot):
    rng = c.rng
    x0, z0, x1, z1 = lot["rect"]
    cx, cz = (x0 + x1) // 2, (z0 + z1) // 2
    for (dx, dz) in ((-2, -2), (2, 2), (-2, 2), (2, -2)):
        tree_round(c, cx + dx * 2, ST, cz + dz * 2, rng, "cherry", (7, 10))
    c.box(cx - 1, ST, cz - 1, cx + 1, ST + 2, cz + 1, "stone_bricks")
    c.box(cx - 1, ST + 2, cz - 1, cx + 1, ST + 3, cz + 1, "sea_lantern")


def sidewalk_lamps(c):
    """Street lamps along the sidewalks (outermost sidewalk column, next to the buildings)."""
    w = c.w
    pl = c.plaza
    for (a, b) in ROADS:
        for (lo, hi, axis) in ((CITY[0] + 8, CITY[1] - 8, 0), (CITY[0] + 8, CITY[1] - 8, 1)):
            for t in range(lo, hi, 18):
                for side_ in (a, b - 1):
                    if axis == 0:
                        x, z = side_, t
                    else:
                        x, z = t, side_
                    if not (c.road[x, z] and c.side[x, z]):
                        continue
                    # keep out of intersections and the plaza
                    cross = any(ra <= (z if axis == 0 else x) < rb for ra, rb in ROADS)
                    near = any(ra - 3 <= (z if axis == 0 else x) < rb + 3 for ra, rb in ROADS)
                    if near or pl[x, z]:
                        continue
                    lamp_post(c, x, z, 10, "glowstone" if (a, b) != MAIN else "sea_lantern")


def plaza_masts(c):
    """Floodlight masts at the four corners of the plaza."""
    for (x, z) in ((113, 113), (205, 113), (113, 205), (205, 205)):
        for i in range(24):
            c.box(x, ST + i, z, x + 2, ST + i + 1, z + 2, "gray_concrete" if i % 6 else "black_concrete")
        c.box(x - 1, ST + 24, z - 1, x + 3, ST + 26, z + 3, "sea_lantern")
        c.put(x, ST + 26, z, "light[level=15]")
        for i in range(6):
            c.put(x, ST + 26 + i, z, "iron_chain[axis=y]")
        c.put(x, ST + 32, z, "red_concrete")
        c.put(x, ST + 33, z, "light[level=13]")


def blade_signs(c, lots):
    rng = c.rng
    for lot in lots:
        if lot["kind"] != "city" or not lot.get("height") or lot["height"] < 14:
            continue
        if rng.random() > 0.55:
            continue
        x0, z0, x1, z1 = lot["rect"]
        xa, xb, za, zb = lot["cell"]
        face = rng.choice(("w", "e", "n", "s"))
        y = ST + rng.randint(7, max(8, min(18, lot["height"] - 12)))
        if face == "w" and x0 <= xa + 1:
            blade_sign(c, x0 - 1, rng.randint(z0 + 3, max(z0 + 3, z1 - 6)), y, "x", rng)
        elif face == "e" and x1 >= xb - 1:
            blade_sign(c, x1, rng.randint(z0 + 3, max(z0 + 3, z1 - 6)), y, "x", rng)
        elif face == "n" and z0 <= za + 1:
            blade_sign(c, rng.randint(x0 + 3, max(x0 + 3, x1 - 6)), z0 - 1, y, "z", rng)
        elif face == "s" and z1 >= zb - 1:
            blade_sign(c, rng.randint(x0 + 3, max(x0 + 3, x1 - 6)), z1, y, "z", rng)


def gate_and_vehicles(c):
    """Shelter hatches painted in the roads (the fortress city's retractable exits) and a few abandoned cars."""
    rng = c.rng
    I = c.I
    for (x0, z0) in ((100, 60), (214, 60), (100, 252), (214, 252), (60, 100), (60, 214), (252, 100), (252, 214)):
        for dx in range(0, 8):
            for dz in range(0, 6):
                edge = dx in (0, 7) or dz in (0, 5)
                c.put(x0 + dx, ST - 1, z0 + dz, hazard_name(dx, dz) if edge else "iron_block")
    for k in range(26):
        a, b = ROADS[rng.randint(0, len(ROADS) - 1)]
        if (a, b) == MAIN:
            continue
        t = rng.randint(40, 280)
        vertical = rng.random() < 0.5
        off = rng.choice((a + 3, b - 5))
        x, z = (off, t) if vertical else (t, off)
        if any(ra - 3 <= (z if vertical else x) < rb + 3 for ra, rb in ROADS) or c.plaza[x, z]:
            continue
        col = rng.choice(("white_concrete", "light_gray_concrete", "black_concrete", "red_concrete",
                          "blue_concrete", "yellow_concrete"))
        sx, sz = (2, 4) if vertical else (4, 2)
        c.box(x, ST, z, x + sx, ST + 1, z + sz, col)
        c.box(x + (0 if vertical else 1), ST + 1, z + (1 if vertical else 0),
              x + (2 if vertical else 3), ST + 2, z + (3 if vertical else 2), col)
        c.put(x + (0 if vertical else 1), ST + 1, z + (1 if vertical else 0), "tinted_glass")


# ------------------------------------------------------------------ the plan
def plan_lots(c):
    rng = c.rng
    lots = []
    landmarks = {(1, 1): "stepped", (4, 1): "spire", (1, 4): "lattice", (4, 4): "twin",
                 (0, 1): "round", (5, 4): "round"}
    for i, (xa, xb) in enumerate(CELLS):
        for j, (za, zb) in enumerate(CELLS):
            cell = (xa, xb, za, zb)
            ring = i in (0, 5) or j in (0, 5)
            dist = max(abs((xa + xb) / 2 - 160), abs((za + zb) / 2 - 160))
            if i in (2, 3) and j in (2, 3):
                x0 = 116 if i == 2 else 190
                z0 = 116 if j == 2 else 190
                lots.append(dict(kind="bunker", rect=(x0, z0, x0 + 14, z0 + 14), cell=cell, idx=(j - 2) * 2 + (i - 2)))
            elif (i, j) in ((2, 1), (3, 1)):
                if i == 2:
                    lots.append(dict(kind="weapon", rect=(128, 76, 146, 108), cell=cell, face="e", which=0))
                else:
                    lots.append(dict(kind="weapon", rect=(174, 76, 192, 108), cell=cell, face="w", which=1))
            elif (i, j) == (4, 2):
                lots.append(dict(kind="power", rect=(208, 128, 248, 146), cell=cell))
            elif j == 5 and 1 <= i <= 4:
                lots.append(dict(kind="park", rect=(xa, za, xb, zb), cell=cell))
            elif (i, j) in landmarks:
                lk = landmarks[(i, j)]
                cx, cz = (xa + xb) // 2, (za + zb) // 2
                if lk == "round":
                    lots.append(dict(kind="landmark", lk="round", rect=(cx - 11, cz - 11, cx + 11, cz + 11), cell=cell))
                else:
                    lots.append(dict(kind="landmark", lk=lk, rect=(cx - 14, cz - 14, cx + 14, cz + 14), cell=cell))
                # the margin of a landmark cell: small plaza strips with trees
                for (a, b, cc, d) in ((xa, za, xb, cz - 14), (xa, cz + 14, xb, zb), (xa, cz - 14, cx - 14, cz + 14),
                                      (cx + 14, cz - 14, xb, cz + 14)):
                    if cc - a >= 4 and d - b >= 4:
                        lots.append(dict(kind="strip", rect=(a, b, cc, d), cell=cell))
            else:
                parts = subdivide(rng, xa, za, xb, zb, 24 if not ring else 22, 11, gap=1)
                for (a, b, cc, d) in parts:
                    lots.append(dict(kind="city", rect=(a, b, cc, d), cell=cell, ring=ring, dist=dist))
    return lots


def build_strip(c, lot):
    rng = c.rng
    x0, z0, x1, z1 = lot["rect"]
    for _ in range(max(1, (x1 - x0) * (z1 - z0) // 90)):
        tree_round(c, rng.randint(x0 + 1, x1 - 2), ST, rng.randint(z0 + 1, z1 - 2), rng, rng.choice(("oak", "cherry")), (7, 11))


def dirt_under_cover(w):
    """Grass, podzol and mycelium with a solid block on top turn to dirt in the game, so draw them as dirt: the canvas
    then shows what the game will (under roads and buildings nobody sees the difference).  Same test as build.py:
    a full cube above, not glass or ice."""
    import compile as comp                      # tools/world is on sys.path (build.py and main() both put it there)
    pal = w.palette
    dirt = w._id("dirt")
    solid = np.zeros(len(w.palette), bool)
    for g in range(2, len(pal)):
        solid[g] = (not comp.needs_neighbours(comp.canon(pal[g]))) and not any(k in pal[g] for k in ("glass", "ice"))
    grass = np.zeros(len(w.palette), bool)
    for g in range(2, len(pal)):
        grass[g] = pal[g].split(":", 1)[1].split("[")[0] in ("grass_block", "podzol", "mycelium")
    a = w.a
    covered = grass[a[:, :-1, :]] & solid[a[:, 1:, :]]
    a[:, :-1, :][covered] = dirt
    return int(covered.sum())


def build(w):
    c = C(w)
    build_terrain(c)
    lots = plan_lots(c)
    # decide the open / house lots now, so that their ground can be painted into the street layer
    for lot in lots:
        if lot["kind"] == "city":
            x0, z0, x1, z1 = lot["rect"]
            ring = lot["ring"]
            dist = lot["dist"]
            rr = c.rng.random()
            if not ring and dist > 78 and rr < 0.07:
                lot["kind"] = "open"
            elif not ring and dist > 78 and rr < 0.14 and min(x1 - x0, z1 - z0) >= 14:
                lot["kind"] = "house"
            if lot["kind"] == "city" and (x1 - x0 < 8 or z1 - z0 < 8):
                lot["kind"] = "open"
    c.lots = lots
    paint_ground(c, lots)
    build_launch(c)
    plaza_masts(c)
    tallest = 0
    info = {}
    for lot in lots:
        k = lot["kind"]
        if k == "city":
            make_building(c, lot, lot["ring"], lot["dist"])
            if lot["kind"] == "house":
                build_house(c, lot)
            elif lot["kind"] == "open":
                build_open(c, lot)
        elif k == "house":
            build_house(c, lot)
        elif k == "weapon":
            build_weapon(c, lot, lot["which"])
        elif k == "bunker":
            build_bunker(c, lot, lot["idx"])
        elif k == "power":
            info["power"] = build_power(c)
        elif k in ("park",):
            build_park(c, lot)
        elif k == "open":
            build_open(c, lot)
        elif k == "strip":
            build_strip(c, lot)
        elif k == "landmark":
            lk = lot["lk"]
            x0, z0, x1, z1 = lot["rect"]
            if lk == "spire":
                tallest = max(tallest, landmark_spire(c, lot["rect"]))
            elif lk == "stepped":
                tallest = max(tallest, landmark_stepped(c, lot["rect"]))
            elif lk == "round":
                tallest = max(tallest, landmark_round(c, (x0 + x1) // 2, (z0 + z1) // 2, 10, 58))
            elif lk == "lattice":
                tallest = max(tallest, landmark_lattice(c, (x0 + x1) // 2, (z0 + z1) // 2))
            elif lk == "twin":
                tallest = max(tallest, landmark_twin(c, (lot["cell"][0], lot["cell"][2], lot["cell"][1], lot["cell"][3])))
    blade_signs(c, lots)
    sidewalk_lamps(c)
    gate_and_vehicles(c)
    dirt_under_cover(w)

    # ---------------- anchors
    w.anchor("launch_top", 160.0, ST, 160.0, yaw=180.0)
    w.anchor("start", 160.0, ST, 160.0, yaw=180.0)
    w.anchor("launch_bottom", 160.0, 1, 160.0, yaw=180.0)
    w.anchor("angel_start", 160.0, ST, 50.0, yaw=0.0)
    w.anchor("angel_path_1", 160.0, ST, 76.0, yaw=0.0)
    w.anchor("angel_path_2", 160.0, ST, 100.0, yaw=0.0)
    w.anchor("angel_path_3", 160.0, ST, 122.0, yaw=0.0)
    sock = info["power"]["socket"]
    w.anchor("power", 200.0, ST, float(sock[2]), yaw=-90.0)
    w.anchor("power_socket", 207.0, float(sock[1]), float(sock[2]), yaw=90.0)
    for lot in lots:
        if lot["kind"] == "bunker":
            x0, z0, x1, z1 = lot["rect"]
            n = lot["idx"] + 1
            # cover_N: street level, three blocks off the corner facing the arena centre (open ground);
            # cover_N_centre: the middle of the block itself (hollow inside)
            sx_ = 1 if x1 <= 160 else -1
            sz_ = 1 if z1 <= 160 else -1
            ix = (x1 if sx_ > 0 else x0) + sx_ * 3.0
            iz = (z1 if sz_ > 0 else z0) + sz_ * 3.0
            w.anchor("cover_%d" % n, ix, ST, iz, yaw=0.0)
            w.anchor("cover_%d_centre" % n, (x0 + x1) / 2.0, ST, (z0 + z1) / 2.0)
    c.info = info
    return c


# ------------------------------------------------------------------ checks and pictures (run as a script)
def _color_table(w):
    from PIL import Image  # noqa: F401
    base = {
        "white": (225, 225, 228), "light_gray": (150, 150, 152), "gray": (80, 82, 86), "black": (22, 22, 26),
        "yellow": (225, 200, 50), "red": (190, 40, 40), "orange": (225, 120, 30), "magenta": (190, 60, 180),
        "lime": (110, 200, 40), "cyan": (30, 150, 160), "light_blue": (60, 150, 215), "pink": (230, 130, 170),
        "blue": (50, 60, 170), "brown": (110, 70, 40), "green": (80, 110, 40), "purple": (110, 50, 160),
    }
    emis = {"sea_lantern": (215, 250, 245), "glowstone": (255, 215, 130), "redstone_lamp": (255, 190, 110),
            "shroomlight": (255, 140, 60), "ochre_froglight": (255, 235, 130), "verdant_froglight": (150, 255, 160),
            "pearlescent_froglight": (255, 170, 235), "end_rod": (255, 255, 255), "lantern": (255, 200, 100)}
    spec = {"stone": (110, 112, 116), "deepslate": (55, 55, 62), "tuff": (90, 92, 85), "andesite": (130, 130, 128),
            "polished_andesite": (140, 140, 138), "polished_deepslate": (60, 60, 68), "grass_block": (60, 105, 55),
            "podzol": (80, 60, 40), "dirt": (100, 75, 50), "sand": (200, 190, 140), "gravel": (120, 115, 112),
            "water": (25, 45, 110), "spruce_leaves": (28, 62, 38), "oak_leaves": (40, 90, 40),
            "cherry_leaves": (200, 140, 170), "spruce_log": (60, 45, 30), "oak_log": (90, 70, 45),
            "tinted_glass": (24, 20, 34), "iron_block": (190, 192, 196), "copper_block": (190, 110, 80),
            "oxidized_copper": (70, 150, 130), "waxed_oxidized_copper": (70, 150, 130),
            "chiseled_copper": (190, 110, 80), "copper_grate": (180, 110, 80),
            "polished_blackstone": (35, 32, 38), "stone_bricks": (115, 115, 115), "smooth_stone": (150, 150, 150),
            "calcite": (225, 225, 220), "dirt_path": (140, 120, 70), "daylight_detector": (40, 45, 70),
            "iron_trapdoor": (180, 182, 186), "iron_bars": (120, 122, 126), "lightning_rod": (180, 100, 70),
            "iron_chain": (60, 60, 66), "stone_brick_wall": (110, 110, 110), "iron_door": (190, 190, 190),
            "deepslate_tile": (45, 45, 52), "blackstone": (36, 33, 40), "cobbled_deepslate": (62, 62, 68),
            "dark_oak_planks": (62, 46, 28), "spruce_planks": (110, 80, 50), "red_stained_glass": (200, 40, 40),
            "copper_bulb": (255, 190, 120), "lantern": (255, 200, 100), "polished_blackstone_slab": (35, 32, 38), "polished_blackstone_brick": (40, 38, 45), "stone_brick": (115, 115, 115)}
    rgb = np.zeros((len(w.palette), 3), np.float32)
    em = np.zeros(len(w.palette), bool)
    skip = np.zeros(len(w.palette), bool)
    for i, nm in enumerate(w.palette):
        if nm is None:
            skip[i] = True
            continue
        n = nm.split("[")[0].replace("minecraft:", "")
        if n in ("air", "light"):
            skip[i] = True
            continue
        if n in emis:
            rgb[i] = emis[n]
            em[i] = True
            continue
        if n in spec:
            rgb[i] = spec[n]
            continue
        for suf in ("_concrete_slab", "_concrete_stairs", "_concrete", "_terracotta"):
            if n.endswith(suf):
                key = n[: -len(suf)]
                bc = base.get(key, (150, 150, 150))
                rgb[i] = bc if suf != "_terracotta" else tuple(int(v * 0.72) for v in bc)
                break
        else:
            hit = False
            for k, v in spec.items():
                if n.startswith(k):
                    rgb[i] = v
                    hit = True
                    break
            if not hit:
                rgb[i] = (170, 80, 170)
    return rgb, em, skip


def render_top(w, path, scale=3):
    from PIL import Image
    rgb, em, skip = _color_table(w)
    a = w.a
    solid = ~skip[a]
    top = a.shape[1] - 1 - np.argmax(solid[:, ::-1, :], axis=1)
    anyc = solid.any(axis=1)
    ids = np.take_along_axis(a, top[:, None, :], axis=1)[:, 0, :]
    col = rgb[ids]
    shade = (0.45 + 0.55 * np.clip(top / 110.0, 0, 1))[..., None]
    col = np.where(em[ids][..., None], col, col * shade * 0.9)
    col = np.where(anyc[..., None], col, 0)
    img = col.transpose(1, 0, 2).astype(np.uint8)
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path)


def render_slice(w, path, axis, at, scale=4, window=None):
    from PIL import Image
    rgb, em, skip = _color_table(w)
    a = w.a
    sl = a[at, :, :] if axis == "x" else a[:, :, at]       # [y, z] or [x, y]
    img = rgb[sl]
    emm = em[sl]
    img = np.where(emm[..., None], img, img * 0.8)
    img = np.where(skip[sl][..., None], np.array([14, 16, 28], np.float32), img)
    if axis == "x":
        img = img.transpose(0, 1, 2)[::-1]                  # rows = y (flipped), cols = z
    else:
        img = img.transpose(1, 0, 2)[::-1]                  # rows = y, cols = x
    img = img.astype(np.uint8)
    if window:
        (c0, c1) = window
        img = img[:, c0:c1]
    Image.fromarray(img).resize((img.shape[1] * scale, img.shape[0] * scale), Image.NEAREST).save(path)


def render_eye(w, path, pos, yaw, pitch, fov=100.0, size=(720, 360), far=420.0, step=0.5):
    """A crude ray-marched view.  yaw 0 looks south (+z), 180 north (-z), -90 east, 90 west (Minecraft)."""
    from PIL import Image
    rgb, em, skip = _color_table(w)
    a = w.a
    W, H = size
    sx, sy, sz = w.size
    f = (W / 2) / math.tan(math.radians(fov) / 2)
    u = (np.arange(W) - W / 2 + 0.5) / f
    v = -(np.arange(H) - H / 2 + 0.5) / f
    U, V = np.meshgrid(u, v)
    yw, pt = math.radians(yaw), math.radians(pitch)
    # camera basis (x east, y up, z south); forward at yaw 0 = +z
    fwd = np.array([-math.sin(yw) * math.cos(pt), math.sin(-pt) * 1.0, math.cos(yw) * math.cos(pt)])
    right = np.array([-math.cos(yw), 0.0, -math.sin(yw)])
    up = np.cross(fwd, right)
    up = up if up[1] > 0 else -up
    d = fwd[None, None, :] + U[..., None] * right[None, None, :] + V[..., None] * up[None, None, :]
    d = d / np.linalg.norm(d, axis=2, keepdims=True)
    d = d.reshape(-1, 3)
    n = d.shape[0]
    p0 = np.array(pos, np.float64)
    img = np.zeros((n, 3), np.float32)
    # sky
    sky_t = np.clip(d[:, 1] * 1.5 + 0.1, 0, 1)
    img[:] = (np.array([34, 40, 70]) * (1 - sky_t[:, None]) + np.array([6, 8, 22]) * sky_t[:, None])
    alive = np.ones(n, bool)
    prev = np.floor(p0).astype(int)[None, :].repeat(n, 0)
    t = 0.0
    idx = np.arange(n)
    while t < far and alive.any():
        t += step
        sel = idx[alive]
        pp = p0[None, :] + d[sel] * t
        cell = np.floor(pp).astype(int)
        inside = (cell[:, 0] >= 0) & (cell[:, 0] < sx) & (cell[:, 1] >= 0) & (cell[:, 1] < sy) & (cell[:, 2] >= 0) & (cell[:, 2] < sz)
        dead = ~inside
        # rays that have left the box upward / outward are sky
        alive[sel[dead]] = False
        sel = sel[inside]
        cell = cell[inside]
        bid = a[cell[:, 0], cell[:, 1], cell[:, 2]]
        hit = ~skip[bid]
        if hit.any():
            hs = sel[hit]
            hc = cell[hit]
            hb = bid[hit]
            pc = prev[hs]
            diff = hc - pc
            norm_up = (diff[:, 1] < 0)
            norm_x = (diff[:, 0] != 0) & (diff[:, 1] == 0)
            shade = np.where(norm_up, 1.0, np.where(norm_x, 0.62, 0.78))
            fog = np.clip(t / far, 0, 1) ** 1.2
            col = rgb[hb] * 0.75 * shade[:, None]
            col = np.where(em[hb][:, None], rgb[hb], col)
            col = col * (1 - 0.6 * fog) + np.array([30, 38, 64], np.float32) * (0.6 * fog)
            img[hs] = col
            alive[hs] = False
        prev[sel] = cell
    img = np.clip(img, 0, 255).reshape(H, W, 3).astype(np.uint8)
    Image.fromarray(img).save(path)


def walk_check(w, start=(160, 160), goal=(160, 50), size=10, height=28, step=2):
    """Can a size x size x height box walk from start to goal?  Obstacles above the step height count."""
    skip = _color_table(w)[2]
    a = w.a
    obs = (~skip[a[:, ST + step:ST + height, :]]).any(axis=1)            # [x, z]
    # the world edge and unbuilt cells block too
    sx, sz = obs.shape
    ii = np.zeros((sx + 1, sz + 1), np.int32)
    ii[1:, 1:] = obs.cumsum(0).cumsum(1)
    half = size // 2
    free = np.zeros((sx, sz), bool)
    xs = np.arange(half, sx - half)
    zs = np.arange(half, sz - half)
    X, Z = np.meshgrid(xs, zs, indexing="ij")
    tot = ii[X + half, Z + half] - ii[X - half, Z + half] - ii[X + half, Z - half] + ii[X - half, Z - half]
    free[half:sx - half, half:sz - half] = tot == 0
    # ground must be solid under the whole box
    ground = (~skip[a[:, ST - 1, :]])
    gi = np.zeros((sx + 1, sz + 1), np.int32)
    gi[1:, 1:] = (~ground).cumsum(0).cumsum(1)
    gt = gi[X + half, Z + half] - gi[X - half, Z + half] - gi[X + half, Z - half] + gi[X - half, Z - half]
    free[half:sx - half, half:sz - half] &= gt <= (size * size) // 2
    from collections import deque
    prev = {start: None}
    dq = deque([start])
    ok = free[start]
    while dq and ok:
        cur = dq.popleft()
        if cur == goal:
            break
        for dxz in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx = (cur[0] + dxz[0], cur[1] + dxz[1])
            if nx in prev or not (0 <= nx[0] < sx and 0 <= nx[1] < sz) or not free[nx]:
                continue
            prev[nx] = cur
            dq.append(nx)
    reach = goal in prev
    # the straight corridor
    x0, x1 = start[0] - half, start[0] + half
    z0, z1 = min(start[1], goal[1]), max(start[1], goal[1])
    straight = not obs[x0:x1, z0:z1 + 1].any()
    ground_ok = bool(((~ground[x0:x1, z0:z1 + 1]).mean()) < 0.1)
    path = []
    if reach:
        cur = goal
        while cur is not None:
            path.append(cur)
            cur = prev[cur]
        path.reverse()
    return dict(reachable=reach, straight_corridor_clear=bool(straight), ground_solid=bool(ground_ok),
                path_len=len(path), free_cells=int(free.sum())), obs, free, path


def ray_clear(w, p, q, step=0.25):
    skip = _color_table(w)[2]
    p = np.array(p, float)
    q = np.array(q, float)
    n = int(np.linalg.norm(q - p) / step)
    for i in range(n):
        c_ = np.floor(p + (q - p) * i / n).astype(int)
        if not w.inside(*c_):
            return False, tuple(c_)
        if not skip[w.a[tuple(c_)]]:
            return False, tuple(c_)
    return True, None


def skyline(w, eye, step=0.5):
    """For each azimuth, the lowest elevation at which a ray escapes the box (degrees)."""
    skip = _color_table(w)[2]
    sx, sy, sz = w.size
    res = []
    for az in range(0, 360, 5):
        a = math.radians(az)
        dxz = np.array([math.sin(a), math.cos(a)])
        lowest = None
        for el in np.arange(-10, 40, 1.0):
            e = math.radians(el)
            d = np.array([dxz[0] * math.cos(e), math.sin(e), dxz[1] * math.cos(e)])
            p = np.array(eye, float)
            escaped = True
            t = 0.0
            while t < 500:
                t += step
                pp = p + d * t
                c_ = np.floor(pp).astype(int)
                if not (0 <= c_[0] < sx and 0 <= c_[1] < sy and 0 <= c_[2] < sz):
                    break
                if not skip[w.a[c_[0], c_[1], c_[2]]]:
                    escaped = False
                    break
            if escaped:
                lowest = el
                break
        res.append((az, lowest))
    return res


def validate_blocks(w):
    import json
    cand = [r"D:\genesis-vr\work\mcdata\out\reports\blocks.json"]
    d = json.load(open(cand[0]))
    bad = []
    for nm in w.palette:
        if nm is None:
            continue
        base = nm.split("[")[0]
        if base not in d:
            bad.append((nm, "no such block"))
            continue
        if "[" in nm:
            props = d[base].get("properties", {})
            for kv in nm[nm.index("[") + 1:-1].split(","):
                k, v = kv.split("=")
                if k not in props or v not in props[k]:
                    bad.append((nm, "bad state " + kv))
    return bad


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))
    import layout
    import voxel
    import time
    origin, size = layout.SETS["city"]
    w = voxel.World("city", origin, size)
    t0 = time.time()
    c = build(w)
    print("built in %.1fs; palette %d; non-void cells %d" % (time.time() - t0, len(w.palette), int((w.a > 0).sum())))
    bad = validate_blocks(w)
    print("block validation:", "OK" if not bad else bad)
    out = os.path.join(os.path.dirname(here), "preview", "city")
    os.makedirs(out, exist_ok=True)
    render_top(w, os.path.join(out, "top.png"), 3)
    render_slice(w, os.path.join(out, "slice_x160.png"), "x", 160, 3)
    render_slice(w, os.path.join(out, "slice_z160.png"), "z", 160, 3)
    render_slice(w, os.path.join(out, "shaft_x160.png"), "x", 160, 8, window=(140, 180))
    voxel.preview(w, os.path.join(out, "voxel_top.png"), "y")
    eye = (160.0, 58.0, 160.0)
    render_eye(w, os.path.join(out, "eye_north.png"), eye, 180.0, 4.0)
    render_eye(w, os.path.join(out, "eye_east.png"), eye, -90.0, 4.0)
    render_eye(w, os.path.join(out, "eye_south.png"), eye, 0.0, 4.0)
    render_eye(w, os.path.join(out, "eye_west.png"), eye, 90.0, 4.0)
    render_eye(w, os.path.join(out, "aerial.png"), (300.0, 130.0, 20.0), 45.0, 22.0, fov=85.0, size=(720, 420), far=700)
    for nm, pos, yaw, pitch, fov in (
            ("v_plaza", (160.0, 105.0, 245.0), 180.0, 40.0, 80.0),
            ("v_weapons", (160.0, 50.0, 125.0), -150.0, 6.0, 90.0),
            ("v_power", (185.0, 48.0, 150.0), -75.0, 0.0, 90.0),
            ("v_shaft_up", (160.0, 4.0, 160.0), 180.0, -70.0, 90.0),
            ("v_from_monster", (160.0, 46.0, 52.0), 0.0, 8.0, 100.0),
            ("v_lake", (160.0, 58.0, 250.0), 0.0, 14.0, 100.0),
            ("v_houses", (60.0, 70.0, 130.0), 30.0, 20.0, 100.0),
            ("v_south_aerial", (160.0, 135.0, 318.0), 180.0, 28.0, 85.0),
            ("v_street", (160.0, 36.0, 120.0), 180.0, 2.0, 100.0)):
        render_eye(w, os.path.join(out, nm + ".png"), pos, yaw, pitch, fov=fov, size=(720, 400))
    res, obs, free, path = walk_check(w)
    print("walk:", res)
    ok1, hit1 = ray_clear(w, eye, (160.0, 47.0, 50.0))
    print("eye -> angel centre clear:", ok1, hit1)
    ok2, hit2 = ray_clear(w, eye, (160.0, 70.0, 50.0))
    print("eye -> angel head clear:", ok2, hit2)
    sk = skyline(w, eye)
    print("skyline min elevation where rays escape (deg):", min(s[1] for s in sk if s[1] is not None), "max",
          max(s[1] for s in sk if s[1] is not None), "unescaped azimuths:", [s[0] for s in sk if s[1] is None][:10])
    worst = (99, None)
    for px in (40, 100, 160, 220, 280):
        for pz in (40, 100, 160, 220, 280):
            s2 = skyline(w, (float(px), 58.0, float(pz)))
            lo2 = min((s[1] if s[1] is not None else 99) for s in s2)
            if lo2 < worst[0]:
                worst = (lo2, (px, pz))
    print("lowest escaping ray from any of 25 viewpoints at y=58: %s deg at %s" % worst)
    skip = _color_table(w)[2]
    zone = w.a[152:168, ST:ST + 31, 42:58]
    print("monster zone solid cells:", int((~skip[zone]).sum()))
    for k, v in sorted(w.anchors.items()):
        print("anchor %-14s local (%.1f, %.1f, %.1f) yaw %.0f" % (k, v["x"] - origin[0], v["y"] - origin[1], v["z"] - origin[2], v["yaw"]))
    return w, c


if __name__ == "__main__":
    main()
