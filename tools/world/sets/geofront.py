"""GEOFRONT - the reveal: an immense underground cavern lit gold, seen from the car-train gallery on its wall.

Footprint 320 x 144 x 320 (x east, y up, z south).  Run this file directly to build, run the checks and
write previews to tools/world/preview/geofront/.

PLAN (x east ->, z south v; centre of the cavern is (160, 160))
    cavern      a rounded super-ellipsoid, air radius 152 at the equator (y = 16), ceiling ~ y 138, floor ~ y 17
    city plate  the flat dark underside of the city, y 131, radius ~62, with ring/spoke light collectors;
                16 inverted skyscrapers hang from it (bottoms between y ~81 and y ~115)
    lake        centre (150, 225), 110 x 68, water surface y 15 (cells up to 15), sand shore
    hq          pyramid 71 wide, 40 high, centre (240, 150); plaza; low entrance building on the EAST face,
                door at x 292; inverted-pyramid water pit south of the plaza at (250, 230)
    forest      oak, birch, spruce, dark oak, cherry, tall jungle giants; meadows; a few roads; a monorail loop
    car-train   starts in a dark tunnel in the NW rock (58 closed blocks), runs NE (45 deg); its cavern-side wall ends at
                "wall_opens" and 6 blocks later the rider is at "reveal" (64, 64) y 97 with the whole cavern in
                view (the wall has to end a few blocks BEFORE the anchor, otherwise the lake, which lies behind the
                perpendicular of the track, is hidden by the end of the wall); then the line runs clockwise along the north and east walls as a covered gallery
                (open colonnade on the cavern side, glass rail), descending 1 in 4 to the terminal at the east
                wall (x ~ 307, z ~ 150-170, deck top y 18), 30 blocks from the pyramid door.

Conventions
    * railbed top ("deck top") is a surface height; deck is half-block slabs where the surface is x.5.
    * 'wall_opens' is the first open column, 'reveal' the point where the view is complete (6 blocks on).
    * anchors for the train give the player's FEET standing ON the wagon bed, i.e. one block above the railbed
      top (wagon bed = the cell at y - 1 of the anchor).  wagon(w, x, y, z, facing) takes that same position.
    * leaves are persistent; no block needs neighbour updates to look right (glass blocks, not panes).
"""
import math
import os
import random
import sys

import numpy as np

SX, SY, SZ = 320, 144, 320
CX = CZ = 160.0
Y0 = 16.0                       # equator level: below it the cavern wall is vertical
A_AIR, B_AIR = 152.0, 122.5     # air semi-axes (horizontal, vertical)
A_HULL, B_HULL = 159.5, 127.5   # outer rock hull
WATER_Y = 15                    # highest water cell
LAND = 17                       # standard top solid block of open ground (feet level 18)

# car-train geometry
PHI_J = -135.0                  # polar angle (atan2(dz, dx)) of the reveal point
LT = 64.0                       # tunnel length before the wall opens
F0, FEND = 97.0, 18.0           # deck top at the reveal / at the terminal
SLOPE, FLAT_END, DS = 0.25, 34.0, 0.5
HW = 3.5                        # half-width of the clear railbed (7 wide); the lining is 2 more each side
OPEN_BACK = 6.0                 # blocks before the reveal anchor where the tunnel wall starts to be open

# layout
PX, TZ = 240, 150               # pyramid centre
PYR_HALF, PYR_H = 35, 40
PLAZA = (197, 296, 108, 192)    # x0, x1, z0, z1
PIT = (250, 232)
PIT_HALF = 18
LK = (150.0, 225.0, 55.0, 34.0)  # lake centre x, z and semi-axes
TOWER_Y = 130                   # first (top) layer of every tower
PLATE_Y = 131                   # lowest layer of the city plate

YAW = {"south": 0.0, "west": 90.0, "north": 180.0, "east": -90.0}
DIRV = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}


# ------------------------------------------------------------------------------------------------ maths helpers
def ss(t):
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def vnoise(rng, shape, cell):
    gx, gz = int(math.ceil(shape[0] / cell)) + 2, int(math.ceil(shape[1] / cell)) + 2
    g = rng.uniform(-1, 1, (gx, gz))
    xs, zs = np.arange(shape[0]) / cell, np.arange(shape[1]) / cell
    x0, z0 = xs.astype(int), zs.astype(int)
    fx, fz = ss(xs - x0)[:, None], ss(zs - z0)[None, :]
    a, b = g[x0][:, z0], g[x0 + 1][:, z0]
    c, d = g[x0][:, z0 + 1], g[x0 + 1][:, z0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fz) + (c * (1 - fx) + d * fx) * fz


def fbm(rng, shape, cell, octaves=3):
    out, amp, tot = 0.0, 1.0, 0.0
    for _ in range(octaves):
        out = out + amp * vnoise(rng, shape, cell)
        tot += amp
        amp *= 0.5
        cell = max(2.0, cell / 2.0)
    return out / tot * 1.6


def hash3(x, y, z):
    """Deterministic 0..99 per cell (ints or int arrays)."""
    return ((x * 73856093) ^ (y * 19349663) ^ (z * 83492791)) % 100


_WOB = [(3, 0.55, 0.7, 0.020), (5, 0.40, 2.1, -0.015), (8, 0.28, 4.0, 0.035), (13, 0.18, 1.2, -0.05), (21, 0.10, 5.1, 0.06)]


def wobble(theta, y):
    s = np.zeros((len(y), len(theta)))
    for k, amp, ph, cy in _WOB:
        s += amp * np.sin(k * theta[None, :] + ph + cy * y[:, None])
    return s


def rw(y):
    """Air radius of the (un-wobbled) cavern wall at height y."""
    u = max(y - Y0, 0.0) / B_AIR
    return A_AIR * max(1 - u ** 3, 0.0) ** (1.0 / 3.0)


def Rp(y):
    """Radius at which the gallery centre-line runs when its deck is at y (hugs the wall, capped near the foot)."""
    return min(rw(y + 4) + HW, 150.0)


# ------------------------------------------------------------------------------------------------ the rail line
def make_path():
    """Centre-line of the train, one sample every DS blocks.  Returns dict of numpy arrays + indices."""
    ph0 = math.radians(PHI_J)
    RJ = Rp(F0)
    J = np.array([CX + RJ * math.cos(ph0), CZ + RJ * math.sin(ph0)])
    T0 = np.array([-math.sin(ph0), math.cos(ph0)])
    N0 = np.array([-math.cos(ph0), -math.sin(ph0)])
    S = J - LT * T0
    rows = []     # x, z, F, tx, tz, nx, nz, mode
    n_t = int(round(LT / DS))
    for i in range(n_t):
        p = S + T0 * (i * DS)
        rows.append((p[0], p[1], F0, T0[0], T0[1], N0[0], N0[1], 0))
    ph, F, s_arc, flat = ph0, F0, 0.0, 0.0
    while True:
        R = Rp(F)
        p = (CX + R * math.cos(ph), CZ + R * math.sin(ph))
        T = (-math.sin(ph), math.cos(ph))
        N = (-math.cos(ph), -math.sin(ph))
        mode = 1 if F > FEND + 1e-6 else 2
        rows.append((p[0], p[1], F, T[0], T[1], N[0], N[1], mode))
        if F <= FEND + 1e-6:
            flat += DS
            if flat >= FLAT_END:
                break
        else:
            F = max(F - SLOPE * float(ss(s_arc / 24.0)) * DS, FEND)
        ph += DS / R
        s_arc += DS
    a = np.array(rows)
    P = dict(x=a[:, 0], z=a[:, 1], F=a[:, 2], tx=a[:, 3], tz=a[:, 4], nx=a[:, 5], nz=a[:, 6], mode=a[:, 7].astype(int),
             n_t=n_t, S=S, J=J, T0=T0)
    P["hq"] = np.round(P["F"] * 2) / 2
    seg = np.hypot(np.diff(P["x"]), np.diff(P["z"]))
    seg3 = np.hypot(seg, np.diff(P["F"]))
    P["dist"] = np.concatenate([[0], np.cumsum(seg3)])
    return P


# ------------------------------------------------------------------------------------------------ the builder
class Geo:
    def __init__(self, w):
        self.w = w
        self.a = w.a
        self.rng = np.random.default_rng(2015)
        self.pr = random.Random(2015)
        self.P = make_path()
        self.anchor_info = {}

    def id(self, name):
        return self.w._id(name)

    def put_air(self, x, y, z, bid):
        if 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ and self.a[x, y, z] == 1:
            self.a[x, y, z] = bid

    def put(self, x, y, z, bid):
        if 0 <= x < SX and 0 <= y < SY and 0 <= z < SZ:
            self.a[x, y, z] = bid

    # ------------------------------------------------------------------ 1. terrain fields
    def fields(self):
        rng = self.rng
        xs = np.arange(SX) + 0.5
        X, Z = np.meshgrid(xs, xs, indexing="ij")
        self.X, self.Z = X, Z
        self.rr = np.hypot(X - CX, Z - CZ)
        self.th = np.arctan2(Z - CZ, X - CX)
        n = fbm(rng, (SX, SZ), 70, 3)
        H = 18.2 + 2.2 * n
        for hx, hz, hr, hh in [(75, 118, 22, 7), (225, 52, 20, 6), (48, 205, 18, 6), (118, 70, 16, 4)]:
            H = H + hh * np.exp(-(((X - hx) ** 2 + (Z - hz) ** 2) / (2 * (hr / 2.2) ** 2)))
        H = np.maximum(H, 16.0)

        def dist_rect(x0, x1, z0, z1):
            return np.hypot(np.maximum(np.maximum(x0 - X, X - x1), 0), np.maximum(np.maximum(z0 - Z, Z - z1), 0))

        def flat(Hh, d, level, feather):
            wgt = 1 - ss(d / feather)
            return Hh * (1 - wgt) + level * wgt

        px0, px1, pz0, pz1 = PLAZA
        H = flat(H, dist_rect(px0, px1 + 1, pz0, pz1 + 1), LAND, 9)
        H = flat(H, dist_rect(PIT[0] - 24, PIT[0] + 24, PIT[1] - 24, PIT[1] + 24), LAND, 9)
        P = self.P
        sel = np.where(P["dist"] > P["dist"][-1] - 110)[0]
        dmin = np.full(X.shape, 1e9)
        for i in sel[::3]:
            dmin = np.minimum(dmin, np.hypot(X - P["x"][i], Z - P["z"][i]))
        self.d_term = dmin
        H = flat(H, np.maximum(dmin - 12, 0), LAND, 9)
        # lake
        lx, lz, la, lb = LK
        thl = np.arctan2(Z - lz, X - lx)
        wob = 1 + 0.10 * np.sin(3 * thl + 1.3) + 0.07 * np.sin(5 * thl + 0.4) + 0.04 * np.sin(9 * thl + 2.0)
        q = (((X - lx) / la) ** 2 + ((Z - lz) / lb) ** 2) / wob ** 2
        self.q = q
        t = ss((q - 1.0) / 0.45)
        Hout = WATER_Y + (H - WATER_Y) * t
        Hin = 8 + 7 * np.clip(q, 0, 1) ** 0.6
        H = np.where(q >= 1.0, Hout, Hin)
        self.Hf = H
        self.Hh = np.floor(H + 0.5).astype(int)
        # forest density, zones
        self.fd = fbm(rng, (SX, SZ), 48, 3)
        self.zone_c = fbm(rng, (SX, SZ), 70, 2)       # conifer vs broadleaf
        self.zone_g = fbm(rng, (SX, SZ), 40, 2)       # special groves
        self.patch = fbm(rng, (SX, SZ), 14, 2)
        self.rough = fbm(rng, (SX, SZ), 90, 2)

    # roads and monorail polylines (x, z)
    ROADS = [
        [(196, 190), (170, 178), (120, 170), (80, 150), (64, 100), (82, 56), (115, 40)],
        [(278, 196), (274, 232), (250, 262), (210, 280), (165, 288)],
        [(240, 107), (236, 72), (206, 46)],
    ]
    MONO = [(194, 150), (125, 150), (88, 172), (80, 212), (98, 255), (140, 283), (195, 285), (240, 268), (262, 238), (262, 212)]

    @staticmethod
    def poly_dist(X, Z, pts):
        d = np.full(X.shape, 1e9)
        for (x1, z1), (x2, z2) in zip(pts[:-1], pts[1:]):
            vx, vz = x2 - x1, z2 - z1
            tt = np.clip(((X - x1) * vx + (Z - z1) * vz) / (vx * vx + vz * vz), 0, 1)
            d = np.minimum(d, np.hypot(X - (x1 + tt * vx), Z - (z1 + tt * vz)))
        return d

    # ------------------------------------------------------------------ 2. the shell, floor and surface
    def carve(self):
        a, w = self.a, self.w
        Yc = np.arange(SY) + 0.5
        Zc = np.arange(SZ) + 0.5
        rock_names = ["stone", "andesite", "stone", "tuff", "stone", "granite", "stone", "dripstone_block",
                      "andesite", "stone", "brown_terracotta", "stone", "tuff", "stone"]
        rock = np.array([self.id(n) for n in rock_names], dtype=np.uint16)
        # (not gravel: a gravel speck in a ceiling or an overhang has nothing under it and falls; diorite is the same grey)
        speck = np.array([self.id(n) for n in ["cobblestone", "diorite", "andesite", "tuff"]], dtype=np.uint16)
        plate_id = self.id("deepslate")
        n2 = fbm(self.rng, (SX, SZ), 30, 2)
        self.plate_bot_2d = np.where(self.rr < 76, PLATE_Y + np.maximum(self.rr - 62, 0) * 0.55, 9999)
        for i in range(SX):
            dx = i + 0.5 - CX
            rr = np.hypot(dx, Zc - CZ)
            th = np.arctan2(Zc - CZ, dx)
            wob = wobble(th, Yc)
            Ae = A_AIR * (1 + 0.012 * wob)
            Be = B_AIR * (1 + 0.006 * wob)
            dyv = np.maximum(Yc - Y0, 0)[:, None]
            g = (rr[None, :] / Ae) ** 3 + (dyv / Be) ** 3
            hull = (rr[None, :] / A_HULL) ** 3 + (dyv / B_HULL) ** 3 < 1
            floor_solid = Yc[:, None] <= self.Hh[i][None, :]
            plate = Yc[:, None] >= self.plate_bot_2d[i][None, :]
            air = (g < 1) & ~floor_solid & ~plate
            solid = hull & ~air
            s = Yc[:, None] * 0.34 + 5.0 * n2[i][None, :] + 1.5 * wob
            mat = rock[np.floor(s).astype(int) % len(rock)]
            h = hash3(i, np.arange(SY)[:, None], np.arange(SZ)[None, :])
            mat = np.where(h < 7, speck[h % 4], mat)
            mat = np.where(Yc[:, None] >= self.plate_bot_2d[i][None, :], plate_id, mat)
            a[i] = np.where(air, 1, np.where(solid, mat, 0)).astype(np.uint16)
        self.n2 = n2

    def surface(self):
        a = self.a
        X, Z, Hh, q = self.X, self.Z, self.Hh, self.q
        # surface codes: 0 grass 1 podzol 2 moss 3 coarse 4 sand 5 gravel 6 road 7 plaza a 8 plaza b 9 plaza c 10 clay
        surf = np.zeros(X.shape, dtype=int)
        con = (self.zone_c > 0.15) & (self.fd > 0.15)
        surf[con & (self.patch > -0.2)] = 1
        surf[(self.patch > 0.55) & (self.zone_c <= 0.15)] = 2
        surf[(self.patch < -0.75)] = 3
        # lake: bed and shore
        surf[(q < 1.0) & (Hh <= WATER_Y)] = 4
        surf[(q < 1.0) & (self.patch > 0.3) & (Hh <= WATER_Y)] = 5
        surf[(q < 0.55) & (self.patch < -0.1)] = 10
        surf[(q >= 1.0) & (q < 1.32) & (Hh <= 16)] = 4
        surf[(q >= 1.0) & (q < 1.18) & (self.patch > 0.4)] = 5
        # roads
        road = np.full(X.shape, 1e9)
        for r in self.ROADS:
            road = np.minimum(road, self.poly_dist(X, Z, r))
        self.road_d = road
        surf[(road < 2.6) & (q > 1.35)] = 6
        # plaza paving
        px0, px1, pz0, pz1 = PLAZA
        inp = (X >= px0) & (X < px1 + 1) & (Z >= pz0) & (Z < pz1 + 1)
        xi, zi = X.astype(int), Z.astype(int)
        pat = np.where(((xi // 4 + zi // 4) % 2) == 0, 7, 8)
        pat = np.where((xi % 12 == 0) | (zi % 12 == 0), 9, pat)
        apron = (X >= px1) & (X < 308) & (Z >= TZ - 8) & (Z < TZ + 24)      # paved way from the door to the terminal
        surf[inp | apron] = pat[inp | apron]
        # pit surround
        inpit = (np.abs(X - PIT[0] - 0.5) < 23) & (np.abs(Z - PIT[1] - 0.5) < 23)
        surf[inpit] = pat[inpit]
        # under the deck at the terminal
        self.surf = surf
        top = ["grass_block", "podzol", "moss_block", "coarse_dirt", "sand", "gravel", "gray_concrete",
               "polished_andesite", "smooth_stone", "stone_bricks", "clay"]
        sub = ["dirt", "dirt", "dirt", "dirt", "sand", "gravel", "stone", "stone", "stone", "stone", "clay"]
        topi = np.array([self.id(n) for n in top], dtype=np.uint16)
        subi = np.array([self.id(n) for n in sub], dtype=np.uint16)
        ix, iz = np.meshgrid(np.arange(SX), np.arange(SZ), indexing="ij")
        inside = self.rr < 151
        for d in range(0, 4):
            ids = topi[surf] if d == 0 else subi[surf]
            m = inside
            a[ix[m], (Hh - d)[m], iz[m]] = ids[m]
        # water
        wid = self.id("water")
        for y in range(4, WATER_Y + 1):
            m = (Hh < y) & inside & (self.q < 1.6)
            cur = a[:, y, :]
            cur[m] = wid
        # lily pads
        lily = self.id("lily_pad")
        rr_ = self.rng.random(X.shape)
        m = (Hh <= 13) & (Hh >= 11) & (rr_ < 0.025) & (self.q < 0.95)
        for x_, z_ in zip(*np.where(m)):
            if a[x_, 16, z_] == 1:
                a[x_, 16, z_] = lily

    # ------------------------------------------------------------------ 3. headquarters
    def headquarters(self):
        a = self.a
        top = LAND + 1                      # first air cell above the plaza
        quartz = self.id("smooth_quartz")
        px, pz = PX, TZ
        ctr = lambda k: PYR_HALF - 0.875 * k
        halfs = [int(math.floor(ctr(k))) for k in range(PYR_H)]
        lantern = self.id("sea_lantern")
        band = self.id("light_gray_concrete")
        body = self.id("quartz_block")
        for k in range(PYR_H):
            h = halfs[k]
            y = top + k
            a[px - h:px + h + 1, y, pz - h:pz + h + 1] = body if (k % 10 == 9) else quartz
        # stairs on the exposed ring
        for k in range(PYR_H):
            h = halfs[k]
            nh = halfs[k + 1] if k + 1 < PYR_H else -1
            if nh >= h:
                continue
            y = top + k
            sq = {d: self.id(f"smooth_quartz_stairs[facing={d},half=bottom,shape=straight]") for d in DIRV}
            for t in range(-h + 1, h):
                for d, (sx_, sz_) in [("north", (t, -h)), ("south", (t, h)), ("west", (-h, t)), ("east", (h, t))]:
                    opp = {"north": "south", "south": "north", "west": "east", "east": "west"}[d]
                    # lit strips
                    strip = (abs(t) % 12 == 0) and k % 3 == 0 and k > 2
                    a[px + sx_, y, pz + sz_] = lantern if strip else sq[opp]
        apex = top + PYR_H
        a[px, apex, pz] = self.id("iron_block")
        for k in range(1, 6):
            a[px, apex + k, pz] = self.id("end_rod[facing=up]") if k > 1 else self.id("iron_bars")
        a[px, apex + 1, pz] = self.id("sea_lantern")
        # plaza steps ring around the pyramid foot
        px0, px1, pz0, pz1 = PLAZA
        # lamp posts around the plaza
        post = self.id("light_gray_concrete")
        for lx in range(px0 + 4, px1 - 2, 18):
            for lz in (pz0 + 3, pz1 - 3):
                for k in range(1, 6):
                    a[lx, LAND + k, lz] = post
                a[lx, LAND + 6, lz] = lantern
        for lz in range(pz0 + 12, pz1 - 8, 18):
            for lx in (px0 + 3,):
                for k in range(1, 6):
                    a[lx, LAND + k, lz] = post
                a[lx, LAND + 6, lz] = lantern
        # entrance building on the east face
        bx0, bx1 = PX + PYR_HALF + 1, PX + PYR_HALF + 17
        bz0, bz1 = TZ - 12, TZ + 12
        y0, y1 = LAND + 1, LAND + 9
        wall = self.id("white_concrete")
        trim = self.id("light_gray_concrete")
        glass = self.id("light_blue_stained_glass")
        roof = self.id("gray_concrete")
        a[bx0:bx1 + 1, y0:y1 + 1, bz0:bz1 + 1] = wall
        # hall inside
        a[bx0 + 2:bx1 - 1, y0:y1 - 2, bz0 + 2:bz1 - 1] = 1
        # doorway on the east face (z TZ-3..TZ+3, y0..y0+4)
        a[bx1 - 2:bx1 + 1, y0:y0 + 5, TZ - 3:TZ + 4] = 1
        # windows on the north/south faces and east face
        for z_ in list(range(bz0 + 3, bz1 - 2, 3)):
            a[bx1, y0 + 2:y0 + 6, z_] = glass if abs(z_ - TZ) > 4 else a[bx1, y0 + 2, z_]
        for x_ in range(bx0 + 3, bx1 - 2, 3):
            for zz in (bz0, bz1):
                a[x_, y0 + 2:y0 + 6, zz] = glass
        a[bx0:bx1 + 1, y1, bz0:bz1 + 1] = roof
        a[bx0 - 0:bx1 + 2, y1 + 1, bz0 - 1:bz1 + 2] = trim
        a[bx0 + 2:bx1 - 1, y1 - 2, bz0 + 2:bz1 - 1] = trim       # ceiling inside
        a[bx0 + 3:bx1 - 2, y1 - 2, TZ - 1:TZ + 2] = lantern
        # canopy over the door
        a[bx1 + 1:bx1 + 5, y0 + 6, TZ - 5:TZ + 6] = trim
        for zz in (TZ - 5, TZ + 5):
            for yy in range(y0, y0 + 6):
                a[bx1 + 4, yy, zz] = trim
        a[bx1 + 1:bx1 + 4, y0 + 5, TZ - 4:TZ + 5] = lantern
        self.door = (bx1 + 2.0, LAND + 1, TZ + 0.5)
        # inverted pyramid pit with water
        pcx, pcz = PIT
        brick = self.id("stone_bricks")
        qb = self.id("quartz_bricks")
        water = self.id("water")
        for dx in range(-PIT_HALF - 2, PIT_HALF + 3):
            for dz in range(-PIT_HALF - 2, PIT_HALF + 3):
                rho = max(abs(dx), abs(dz))
                x_, z_ = pcx + dx, pcz + dz
                if rho > PIT_HALF + 1:
                    continue
                if rho >= PIT_HALF:
                    a[x_, LAND, z_] = qb
                    continue
                yb = 6 + int(round(rho / PIT_HALF * 11))
                a[x_, 4:yb, z_] = brick if (rho % 3) else qb
                a[x_, yb, z_] = brick if (rho % 3) else qb
                for y in range(yb + 1, 17):
                    a[x_, y, z_] = water
                a[x_, 17, z_] = 1
        for dx, dz in [(0, 0), (6, 0), (-6, 0), (0, 6), (0, -6)]:
            yb = 6 + int(round(max(abs(dx), abs(dz)) / PIT_HALF * 11))
            a[pcx + dx, yb, pcz + dz] = lantern
        # pit rim lamps
        for dx, dz in [(-20, -20), (20, -20), (-20, 20), (20, 20)]:
            for k in range(1, 5):
                a[pcx + dx, LAND + k, pcz + dz] = post
            a[pcx + dx, LAND + 5, pcz + dz] = lantern

    # ------------------------------------------------------------------ 4. city plate details and towers
    def plate_and_towers(self):
        a = self.a
        rr, th = self.rr, self.th
        m = rr < 62
        ix, iz = np.where(m)
        tiles = self.id("deepslate_tiles")
        pol = self.id("polished_deepslate")
        lant = self.id("sea_lantern")
        froglight = self.id("ochre_froglight")
        ang = (th + math.pi) / (2 * math.pi) * 8
        frac = ang - np.floor(ang)
        arc = np.minimum(frac, 1 - frac) * (2 * math.pi * rr / 8)
        for x_, z_ in zip(ix, iz):
            r = rr[x_, z_]
            if (abs(r - 12) < 0.7) or (abs(r - 30) < 0.7) or (abs(r - 48) < 0.7):
                b = lant
            elif 12 < r < 56 and arc[x_, z_] < 0.6:
                b = froglight
            elif ((x_ // 6 + z_ // 6) % 2) == 0:
                b = pol
            else:
                b = tiles
            a[x_, PLATE_Y, z_] = b
        # chamfer ring of the plate: dark band
        # towers
        rng = random.Random(77)
        lengths = [44, 42, 40, 38, 36, 33, 30, 28, 26, 24, 22, 20, 18, 16, 15, 34]
        rng.shuffle(lengths)
        kinds = ["step", "taper", "step", "round", "taper", "step", "taper", "round", "step", "taper", "step",
                 "round", "taper", "step", "taper", "step"]
        placed = []
        tries = 0
        k = 0
        while k < 16 and tries < 5000:
            tries += 1
            rad = rng.uniform(6, 53)
            ang_ = rng.uniform(0, 2 * math.pi)
            cx, cz = int(CX + rad * math.cos(ang_)), int(CZ + rad * math.sin(ang_))
            hx = rng.choice([2, 3, 3, 4, 5, 5])
            hz = rng.choice([2, 3, 4, 4, 5])
            if kinds[k] == "round":
                hz = hx
            ok = all(abs(cx - ox) > hx + ohx + 3 or abs(cz - oz) > hz + ohz + 3 for ox, oz, ohx, ohz in placed)
            if not ok or math.hypot(cx - CX, cz - CZ) + max(hx, hz) * 1.4 > 59:
                continue
            placed.append((cx, cz, hx, hz))
            self.tower(cx, cz, hx, hz, lengths[k], kinds[k], 1000 + k)
            k += 1
        self.towers = placed
        self.tower_lengths = lengths

    def tower(self, cx, cz, hx, hz, L, kind, seed):
        a = self.a
        core = self.id("gray_concrete")
        pillar = self.id("light_gray_concrete")
        band = self.id("polished_andesite")
        ledge = self.id("smooth_stone")
        glasses = [self.id("glass"), self.id("light_blue_stained_glass"), self.id("cyan_stained_glass")]
        lit = [self.id("ochre_froglight"), self.id("sea_lantern")]
        black = self.id("black_concrete")
        prev = None
        for j in range(L):
            y = TOWER_Y - j
            t = j / float(L)
            if kind == "step":
                inset = 0 if t < 0.5 else (1.5 if t < 0.78 else 3.0)
                ex, ez = max(hx - inset, 1.0), max(hz - inset, 1.0)
            elif kind == "taper":
                f = max(1 - t ** 1.3, 0.0)
                ex, ez = max(hx * f + 0.6, 0.8), max(hz * f + 0.6, 0.8)
            else:
                f = 1 - 0.55 * t ** 2.2
                ex = ez = max(hx * f, 1.0)
            ext = int(math.ceil(max(ex, ez)))
            cells = set()
            for dx in range(-ext, ext + 1):
                for dz in range(-ext, ext + 1):
                    if kind == "round":
                        if dx * dx + dz * dz <= ex * ex + 0.5:
                            cells.add((dx, dz))
                    elif abs(dx) <= ex and abs(dz) <= ez:
                        cells.add((dx, dz))
            cur = cells
            for (dx, dz) in cells:
                x_, z_ = cx + dx, cz + dz
                edge = any((dx + ox, dz + oz) not in cells for ox, oz in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if not edge:
                    b = core
                elif j % 4 == 0:
                    b = band
                elif (dx + dz) % 3 == 0:
                    b = pillar
                else:
                    h = int(hash3(x_, y, z_))
                    if h < 11:
                        b = lit[0]
                    elif h < 14:
                        b = lit[1]
                    elif h < 62:
                        b = glasses[0]
                    elif h < 86:
                        b = glasses[1]
                    else:
                        b = glasses[2]
                a[x_, y, z_] = b
            # where this layer is smaller than the one above, the exposed underside of that one is a ledge
            if prev is not None:
                for (dx, dz) in prev - cells:
                    a[cx + dx, y + 1, cz + dz] = ledge
            prev = cur
        ybot = TOWER_Y - L + 1
        for (dx, dz) in prev:
            a[cx + dx, ybot, cz + dz] = ledge
        # spire
        for k in range(1, 7):
            if k <= 4:
                a[cx, ybot - k, cz] = self.id("iron_bars")
            else:
                a[cx, ybot - k, cz] = self.id("end_rod[facing=down]")
        a[cx, ybot - 1, cz] = self.id("sea_lantern")

    # ------------------------------------------------------------------ 5. the rail line
    def rail_line(self):
        a, P = self.a, self.P
        n = len(P["x"])
        n_t = P["n_t"]
        SW = {}
        qs = np.arange(-HW - 2.0, HW + 2.01, 0.5)
        cap_rows = []
        # start cap: extend backwards
        for k in range(1, 5):
            cap_rows.append((P["S"] - P["T0"] * (k * DS), F0, P["T0"], np.array([P["nx"][0], P["nz"][0]]), -1, -k))
        # end cap
        for k in range(1, 5):
            i = n - 1
            p = np.array([P["x"][i] + P["tx"][i] * DS * k, P["z"][i] + P["tz"][i] * DS * k])
            cap_rows.append((p, FEND, np.array([P["tx"][i], P["tz"][i]]), np.array([P["nx"][i], P["nz"][i]]), -1, n + k))
        cols = {}
        pairs = []
        open_from = n_t - int(OPEN_BACK / DS)       # the tunnel wall on the cavern side ends here, a little before the reveal
        self.open_from = open_from
        for i in range(n):
            md = P["mode"][i]
            if md == 0 and i >= open_from:
                md = 1
            pairs.append((i, np.array([P["x"][i], P["z"][i]]), np.array([P["nx"][i], P["nz"][i]]), md, P["hq"][i]))
        for p, F, T, N, mode, idx in cap_rows:
            pairs.append((idx, p, N, -1, round(F * 2) / 2))
        for i, p, N, mode, hq in pairs:
            for q in qs:
                if mode >= 1 and q > HW + 0.5:
                    continue
                pos = p + N * q
                cx, cz = int(math.floor(pos[0])), int(math.floor(pos[1]))
                d2 = (pos[0] - cx - 0.5) ** 2 + (pos[1] - cz - 0.5) ** 2
                old = cols.get((cx, cz))
                if old is None or d2 < old[0] - 1e-9:
                    cols[(cx, cz)] = (d2, i, q, mode, hq)
        self.cols = cols
        deck_a = self.id("polished_andesite")
        deck_s = self.id("polished_andesite_slab[type=bottom]")
        rail_a = self.id("polished_deepslate")
        rail_s = self.id("polished_deepslate_slab[type=bottom]")
        girder = self.id("deepslate_bricks")
        lining = self.id("polished_deepslate")
        lining2 = self.id("deepslate_tiles")
        roof = self.id("gray_concrete")
        pillar = self.id("light_gray_concrete")
        glass = self.id("glass")
        lant = self.id("sea_lantern")
        yellow = self.id("yellow_concrete")
        for (cx, cz), (d2, i, q, mode, hq) in cols.items():
            full = abs(hq - round(hq)) < 1e-6
            yA = int(math.ceil(hq))
            yc = yA - 1 if full else int(math.floor(hq))
            if mode == -1:
                a[cx, yc - 2:yA + 9, cz] = lining
                continue
            tunnel = (mode == 0)
            if tunnel:
                role = "in" if abs(q) <= HW else ("side" if q > HW else "back")
            else:
                role = "back" if q < -HW else ("in" if q <= HW else "open")
            rail = abs(abs(q) - 1.5) < 0.01
            if role in ("back", "side"):
                a[cx, yc - 2:yA + 9, cz] = lining if ((i // 8) % 2 == 0 or role == "back") else lining2
                continue
            # deck
            if full:
                a[cx, yc, cz] = rail_a if rail else deck_a
            else:
                a[cx, yc, cz] = rail_s if rail else deck_s
            a[cx, yc - 2:yc, cz] = girder
            a[cx, yA:yA + 7, cz] = 1
            a[cx, yA + 7:yA + 9, cz] = roof
            if role == "open":
                rel = i - open_from
                pill = rel >= 26 and ((rel - 26) % 20) < 2
                if pill:
                    a[cx, yA:yA + 7, cz] = pillar
                elif mode == 1:
                    a[cx, yA, cz] = glass
            if role == "in" and tunnel is False and not rail and mode == 2 and abs(q - HW) < 0.01:
                a[cx, yc, cz] = yellow if full else a[cx, yc, cz]
        # lamps in the roof, hidden lights
        light = lambda lv: self.id(f"light[level={lv}]")
        for i in range(0, n, 16):
            hq = P["hq"][i]
            yA = int(math.ceil(hq))
            for qq in (-2.5, 2.5):
                pos = np.array([P["x"][i], P["z"][i]]) + np.array([P["nx"][i], P["nz"][i]]) * qq
                cx, cz = int(math.floor(pos[0])), int(math.floor(pos[1]))
                if P["mode"][i] >= 1:
                    a[cx, yA + 7, cz] = lant
            if P["mode"][i] == 0 and i < open_from:
                for qq in (-2.5, 2.5):
                    pos = np.array([P["x"][i], P["z"][i]]) + np.array([P["nx"][i], P["nz"][i]]) * qq
                    a[int(math.floor(pos[0])), yA + 5, int(math.floor(pos[1]))] = light(12)
        # piers
        pier = self.id("light_gray_concrete")
        cap = self.id("gray_concrete")
        for i in range(n_t + 12, n, 24):
            hq = P["hq"][i]
            full = abs(hq - round(hq)) < 1e-6
            yA = int(math.ceil(hq))
            yc = yA - 1 if full else int(math.floor(hq))
            for qq in (-2.5, 2.5):
                pos = np.array([P["x"][i], P["z"][i]]) + np.array([P["nx"][i], P["nz"][i]]) * qq
                cx, cz = int(math.floor(pos[0])), int(math.floor(pos[1]))
                for ox in (0, 1):
                    for oz in (0, 1):
                        y = yc - 3
                        while y > 0 and a[cx + ox, y, cz + oz] in (0, 1):
                            a[cx + ox, y, cz + oz] = cap if y > yc - 6 else pier
                            y -= 1
        # tree exclusion: lower part of the line
        mask = np.zeros((SX, SZ), dtype=bool)
        for (cx, cz), (d2, i, q, mode, hq) in cols.items():
            if 0 <= cx < SX and 0 <= cz < SZ:
                mask[cx, cz] = True
        self.path_mask = mask

    # ------------------------------------------------------------------ 6. monorail
    def monorail(self):
        a = self.a
        pts = self.MONO
        beam = self.id("light_gray_concrete")
        rail = self.id("iron_block")
        post = self.id("gray_concrete")
        lant = self.id("sea_lantern")
        samples = []
        for (x1, z1), (x2, z2) in zip(pts[:-1], pts[1:]):
            L = math.hypot(x2 - x1, z2 - z1)
            m = int(L / 0.5)
            for k in range(m):
                t = k / m
                samples.append((x1 + (x2 - x1) * t, z1 + (z2 - z1) * t, (x2 - x1) / L, (z2 - z1) / L))
        # beam height follows the highest ground nearby, smoothed
        ground = np.array([self.Hh[int(sx), int(sz)] for sx, sz, _, _ in samples], dtype=float)
        k = 15
        pad = np.pad(ground, k, mode="edge")
        sm = np.array([pad[i:i + 2 * k + 1].max() for i in range(len(ground))])
        sm = np.convolve(np.pad(sm, 12, mode="edge"), np.ones(25) / 25, mode="valid")
        yb = np.round(sm).astype(int) + 7
        cells = {}
        for (sx, sz, tx, tz), y in zip(samples, yb):
            for q in (-1.0, -0.5, 0.0, 0.5, 1.0):
                cx, cz = int(math.floor(sx - tz * q)), int(math.floor(sz + tx * q))
                cells[(cx, cz)] = y
        for (cx, cz), y in cells.items():
            a[cx, y, cz] = beam
            a[cx, y - 1, cz] = beam
        for (sx, sz, tx, tz), y in zip(samples, yb):
            cx, cz = int(math.floor(sx)), int(math.floor(sz))
            a[cx, y + 1, cz] = rail
        for idx in range(0, len(samples), 24):
            sx, sz, tx, tz = samples[idx]
            y = yb[idx]
            cx, cz = int(math.floor(sx)), int(math.floor(sz))
            for ox in (0, 1):
                for oz in (0, 1):
                    yy = y - 2
                    while yy > 1 and a[cx + ox, yy, cz + oz] in (0, 1):
                        a[cx + ox, yy, cz + oz] = post
                        yy -= 1
            # T head and lamp
            for q in range(-3, 4):
                a[int(math.floor(sx - tz * q)), y - 2, int(math.floor(sz + tx * q))] = post
            a[cx, y + 2, cz] = lant
        # station near the plaza: a low roofed platform at the first 26 samples
        self.mono_cells = cells
        self.mono_y = yb
        self.mono_samples = samples
        # a short train parked at the station
        (sx, sz, tx, tz) = samples[34]
        y = yb[34]
        white = self.id("white_concrete")
        blue = self.id("light_blue_stained_glass")
        stripe = self.id("blue_concrete")
        for k in range(-14, 15):
            for q in (-1, 0, 1):
                cx, cz = int(math.floor(sx + tx * k - tz * q)), int(math.floor(sz + tz * k + tx * q))
                a[cx, y + 2, cz] = white
                a[cx, y + 3, cz] = blue if abs(q) == 1 and k % 3 else white
                a[cx, y + 4, cz] = white
        # keep the beam under it

    # ------------------------------------------------------------------ 7. wall and ceiling emitters
    def wall_lights(self):
        a = self.a
        solid = a > 1
        air = a == 1
        # surface air cells: air with a solid neighbour on any side except below (floor handled by ground lights)
        nb = np.zeros_like(air)
        nb[1:] |= solid[:-1]
        nb[:-1] |= solid[1:]
        nb[:, :, 1:] |= solid[:, :, :-1]
        nb[:, :, :-1] |= solid[:, :, 1:]
        nb[:, :-1] |= solid[:, 1:]
        cand = np.where(air & nb)
        ys = cand[1]
        keep = ys > 17
        cand = tuple(c[keep] for c in cand)
        rng = np.random.default_rng(99)
        order = rng.permutation(len(cand[0]))
        grid = {}
        pts = []
        SPACING = 8.0
        cs = 11
        for oi in order:
            x_, y_, z_ = int(cand[0][oi]), int(cand[1][oi]), int(cand[2][oi])
            gx, gy, gz = x_ // cs, y_ // cs, z_ // cs
            good = True
            for ax in (gx - 1, gx, gx + 1):
                for ay in (gy - 1, gy, gy + 1):
                    for az in (gz - 1, gz, gz + 1):
                        for (px, py, pz) in grid.get((ax, ay, az), ()):
                            if (px - x_) ** 2 + (py - y_) ** 2 + (pz - z_) ** 2 < SPACING ** 2:
                                good = False
                                break
                        if not good:
                            break
                    if not good:
                        break
                if not good:
                    break
            if good:
                grid.setdefault((gx, gy, gz), []).append((x_, y_, z_))
                pts.append((x_, y_, z_))
        # The sources are invisible light blocks in the air cell next to the rock (one cell off the wall or the
        # ceiling), not glowing patches set into it: they light the cavern just the same and the walls read as rock.
        # (This used to put a five-block patch of glowstone / shroomlight / froglight into the rock at every point.)
        light15 = self.id("light[level=15]")
        n = 0
        for (x_, y_, z_) in pts:
            a[x_, y_, z_] = light15
            n += 1
        self.n_wall_lights = n

    # ------------------------------------------------------------------ 8. forest
    def trees(self):
        a = self.a
        rng = random.Random(4242)
        X, Z, Hh = self.X, self.Z, self.Hh
        surf = self.surf
        free = np.ones(X.shape, dtype=bool)
        free &= self.rr < 139
        free &= self.q > 1.6
        px0, px1, pz0, pz1 = PLAZA
        free &= ~((X > px0 - 8) & (X < px1 + 8) & (Z > pz0 - 8) & (Z < pz1 + 8))
        free &= ~((np.abs(X - PIT[0]) < 32) & (np.abs(Z - PIT[1]) < 32))
        free &= self.road_d > 4.5
        mono = np.full(X.shape, 1e9)
        mono = self.poly_dist(X, Z, self.MONO)
        free &= mono > 6
        free &= (self.d_term > 17)
        # keep clear of the whole lower gallery
        pm = self.path_mask
        P = self.P
        pd = np.full(X.shape, 1e9)
        for i in range(0, len(P["x"]), 4):
            if P["F"][i] < 60:
                pd = np.minimum(pd, np.hypot(X - P["x"][i], Z - P["z"][i]))
        free &= pd > 9
        # view corridor to the lake (reveal -> lake)
        J = P["J"]
        lx, lz = LK[0], LK[1]
        v = np.array([lx - J[0], lz - J[1]])
        v /= np.linalg.norm(v)
        start = np.array([lx, lz]) - v * 105
        corridor = self.poly_dist(X, Z, [tuple(start), (lx, lz)])
        self.corridor = corridor
        free &= corridor > 13
        # tall trees stay out of the cone between the reveal and the lake (their tops would hide the water)
        ex, ez = P["x"][P["n_t"]], P["z"][P["n_t"]]
        ux, uz = lx - ex, lz - ez
        ul = math.hypot(ux, uz)
        ux, uz = ux / ul, uz / ul
        along = (X - ex) * ux + (Z - ez) * uz
        lateral = np.abs((X - ex) * uz - (Z - ez) * ux)
        tall_ok = ~((along > 105) & (along < 270) & (lateral < 0.34 * along))
        # the open clearing in the middle
        free &= self.rr > 14
        self.tree_free = free
        dens = np.clip((self.fd + 0.5) * 1.5, 0, 1)
        types = {}
        lg = lambda n: self.id(n)
        L = lambda n: self.id(f"{n}[persistent=true]")
        ids = dict(oak_log=lg("oak_log"), oak=L("oak_leaves"), birch_log=lg("birch_log"), birch=L("birch_leaves"),
                   spruce_log=lg("spruce_log"), spruce=L("spruce_leaves"), dark_log=lg("dark_oak_log"), dark=L("dark_oak_leaves"),
                   cherry_log=lg("cherry_log"), cherry=L("cherry_leaves"), jungle_log=lg("jungle_log"), jungle=L("jungle_leaves"),
                   azalea=L("azalea_leaves"), flower=L("flowering_azalea_leaves"), acacia_log=lg("acacia_log"), acacia=L("acacia_leaves"))
        count = {}

        def blob(cx, cy, cz, rx, ry, rz, leaf, jitter=0.35):
            for dx in range(-int(rx) - 1, int(rx) + 2):
                for dy in range(-int(ry) - 1, int(ry) + 2):
                    for dz in range(-int(rz) - 1, int(rz) + 2):
                        d = (dx / rx) ** 2 + (dy / ry) ** 2 + (dz / rz) ** 2
                        if d <= 1.0 - jitter * rng.random() * 0.8:
                            self.put_air(cx + dx, cy + dy, cz + dz, leaf)

        def trunk(x, y, z, h, log, thick=1):
            for k in range(h):
                for ox in range(thick):
                    for oz in range(thick):
                        self.put(x + ox, y + k, z + oz, log)

        def oak(x, y, z):
            h = rng.randint(5, 9)
            r = rng.uniform(2.8, 4.3)
            blob(x, y + h, z, r, r * 0.85, r, ids["oak"])
            if rng.random() < 0.5:
                bx, bz = rng.choice([-2, 2]), rng.choice([-2, 2])
                blob(x + bx, y + h - 2, z + bz, 2.2, 1.8, 2.2, ids["oak"])
            trunk(x, y, z, h + 1, ids["oak_log"])

        def birch(x, y, z):
            h = rng.randint(7, 11)
            blob(x, y + h - 1, z, 2.5, 3.6, 2.5, ids["birch"])
            trunk(x, y, z, h + 1, ids["birch_log"])

        def spruce(x, y, z):
            h = rng.randint(10, 19)
            rmax = rng.uniform(3.0, 4.6)
            for dy in range(2, h + 3):
                f = (h + 3 - dy) / float(h + 1)
                r = rmax * f
                if (dy % 2) == 0:
                    r *= 0.65
                ri = int(math.ceil(r))
                for dx in range(-ri, ri + 1):
                    for dz in range(-ri, ri + 1):
                        if dx * dx + dz * dz <= r * r + 0.3:
                            self.put_air(x + dx, y + dy, z + dz, ids["spruce"])
            trunk(x, y, z, h + 2, ids["spruce_log"])

        def dark(x, y, z):
            h = rng.randint(10, 15)
            blob(x + 1, y + h, z + 1, rng.uniform(5.5, 7.5), 3.2, rng.uniform(5.5, 7.5), ids["dark"], 0.5)
            blob(x + 1, y + h + 2, z + 1, 3.5, 2.5, 3.5, ids["dark"])
            trunk(x, y, z, h + 2, ids["dark_log"], 2)

        def cherry(x, y, z):
            h = rng.randint(5, 8)
            blob(x, y + h, z, rng.uniform(4, 5.2), 2.8, rng.uniform(4, 5.2), ids["cherry"], 0.5)
            trunk(x, y, z, h + 1, ids["cherry_log"])

        def giant(x, y, z):
            h = rng.randint(18, 27)
            blob(x + 1, y + h, z + 1, 5.5, 4.2, 5.5, ids["jungle"])
            blob(x + 1, y + h // 2 + 2, z + 1, 4.0, 2.6, 4.0, ids["jungle"])
            trunk(x, y, z, h + 2, ids["jungle_log"], 2)

        def acacia(x, y, z):
            h = rng.randint(6, 9)
            blob(x, y + h, z, 4.8, 1.6, 4.8, ids["acacia"], 0.5)
            trunk(x, y, z, h + 1, ids["acacia_log"])

        def bush(x, y, z):
            lf = rng.choice([ids["azalea"], ids["flower"], ids["oak"]])
            blob(x, y + 1, z, 1.7, 1.3, 1.7, lf)

        n = 0
        for gx in range(8, SX - 8, 3):
            for gz in range(8, SZ - 8, 3):
                x = gx + rng.randint(-1, 1)
                z = gz + rng.randint(-1, 1)
                if not free[x, z]:
                    continue
                if surf[x, z] not in (0, 1, 2, 3):
                    continue
                d = dens[x, z]
                r = rng.random()
                if r > d * 0.85:
                    # sparse meadow: the odd lone tree or bush
                    if r > 0.985 and self.rr[x, z] > 25:
                        oak(x, Hh[x, z] + 1, z)
                    elif r > 0.965:
                        bush(x, Hh[x, z] + 1, z)
                    continue
                y = Hh[x, z] + 1
                zc = self.zone_c[x, z]
                zg = self.zone_g[x, z]
                r2 = rng.random()
                if zg > 0.35 and r2 < 0.6:
                    kind = "cherry"
                elif zg < -0.4 and r2 < 0.55:
                    kind = "dark"
                elif zc > 0.15:
                    kind = "spruce" if r2 < 0.8 else ("giant" if r2 < 0.83 else "birch")
                elif zc < -0.15:
                    kind = rng.choice(["oak", "oak", "birch", "oak", "acacia" if rng.random() < 0.2 else "oak", "bush"])
                    if r2 > 0.97:
                        kind = "giant"
                else:
                    kind = rng.choice(["oak", "birch", "spruce", "oak", "dark", "bush"])
                    if r2 > 0.985:
                        kind = "giant"
                if kind in ("spruce", "giant", "dark") and not tall_ok[x, z]:
                    kind = "bush"
                if kind == "dark" and (not free[min(x + 1, SX - 1), z] or not free[x, min(z + 1, SZ - 1)]):
                    kind = "oak"
                {"oak": oak, "birch": birch, "spruce": spruce, "dark": dark, "cherry": cherry, "giant": giant,
                 "acacia": acacia, "bush": bush}[kind](x, y, z)
                count[kind] = count.get(kind, 0) + 1
        self.tree_count = count

    def flora(self):
        a = self.a
        rng = np.random.default_rng(31)
        X, Z, Hh = self.X, self.Z, self.Hh
        grass = self.id("short_grass")
        fern = self.id("fern")
        tl = self.id("tall_grass[half=lower]")
        tu = self.id("tall_grass[half=upper]")
        flowers = [self.id(n) for n in ["dandelion", "poppy", "cornflower", "azure_bluet", "oxeye_daisy", "allium"]]
        ok = (self.surf == 0) | (self.surf == 1) | (self.surf == 2)
        ok &= (self.rr < 146) & (self.q > 1.2) & (self.road_d > 3)
        r = rng.random(X.shape)
        n = 0
        for x_, z_ in zip(*np.where(ok & (r < 0.34))):
            y = Hh[x_, z_] + 1
            if a[x_, y, z_] != 1:
                continue
            v = r[x_, z_] / 0.34
            if self.surf[x_, z_] == 1:
                a[x_, y, z_] = fern if v < 0.4 else grass
            elif v < 0.55:
                a[x_, y, z_] = grass
            elif v < 0.76 and a[x_, y + 1, z_] == 1:
                a[x_, y, z_] = tl
                a[x_, y + 1, z_] = tu
            elif v < 0.88:
                a[x_, y, z_] = flowers[(x_ // 9 + z_ // 7) % len(flowers)]
            else:
                a[x_, y, z_] = fern
            n += 1
        self.n_flora = n

    # ------------------------------------------------------------------ 9. ground lights
    def ground_lights(self):
        a = self.a
        light15 = self.id("light[level=15]")
        n = 0
        S = 8
        for j, gz in enumerate(range(6, SZ - 4, S)):
            off = 4 if (j % 2) else 0
            for gx in range(6 + off, SX - 4, S):
                if math.hypot(gx - CX, gz - CZ) > 149:
                    continue
                placed = False
                for ox, oz in [(0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (2, 0), (0, 2), (-2, 0), (0, -2)]:
                    x_, z_ = gx + ox, gz + oz
                    if not (0 <= x_ < SX and 0 <= z_ < SZ):
                        continue
                    y0 = max(self.Hh[x_, z_], WATER_Y) + 1
                    for y in range(y0, y0 + 4):
                        if a[x_, y, z_] == 1:
                            a[x_, y, z_] = light15
                            placed = True
                            break
                    if placed:
                        break
                n += placed
        self.n_ground_lights = n

    def canopy_lights(self):
        """Hidden light sources just above whatever stands on the ground (canopies, roofs, water): lights the tops
        of trees and the upper pyramid, which the ground lattice cannot reach."""
        a = self.a
        light15 = self.id("light[level=15]")
        transp = _classes(self.w)[0]
        n = 0
        S = 9
        for j, gz in enumerate(range(5, SZ - 4, S)):
            off = 5 if (j % 2) else 0
            for gx in range(5 + off, SX - 4, S):
                if math.hypot(gx - CX, gz - CZ) > 146:
                    continue
                col = a[gx, :, gz]
                y = int(max(self.Hh[gx, gz], WATER_Y)) + 45
                y = min(y, 100)
                while y > 0 and (col[y] == 1 or "light" in (self.w.palette[col[y]] or "")):
                    y -= 1
                for yy in range(y + 2, y + 4):
                    if a[gx, yy, gz] == 1:
                        a[gx, yy, gz] = light15
                        n += 1
                        break
        self.n_canopy_lights = n

    # ------------------------------------------------------------------ 10. anchors
    def make_anchors(self):
        w, P = self.w, self.P
        n = len(P["x"])
        n_t = P["n_t"]

        def pos(i, extra=0):
            hq = P["hq"][i]
            fy = int(math.ceil(hq)) + 1 + extra
            return P["x"][i], fy, P["z"][i]

        def yaw_of(dx, dz):
            return math.degrees(math.atan2(-dx, dz))

        # start: 10 blocks into the tunnel
        dist = P["dist"]
        s0 = 10.0
        i0 = int(np.argmin(np.abs(dist - s0)))
        x, y, z = pos(i0)
        w.anchor("start", x, y, z, yaw_of(P["tx"][i0], P["tz"][i0]), 0)
        self.anchor_info["start"] = (x, y, z)
        # terminal: 14 blocks into the flat terminal section
        first_flat = int(np.argmax(P["mode"] == 2))
        it = first_flat + int(14 / DS)
        # train anchors every 14 blocks of path length
        tlimit = dist[it] - 12
        k = 1
        names = []
        while s0 + 14 * k <= tlimit:
            i = int(np.argmin(np.abs(dist - (s0 + 14 * k))))
            x, y, z = pos(i)
            nm = f"train_{k}"
            w.anchor(nm, x, y, z, yaw_of(P["tx"][i], P["tz"][i]), 0)
            self.anchor_info[nm] = (x, y, z)
            names.append(nm)
            k += 1
        self.n_train = k - 1
        # wall_opens: the first open column (cavern side)
        x, y, z = pos(self.open_from)
        w.anchor("wall_opens", x, y, z, yaw_of(P["tx"][self.open_from], P["tz"][self.open_from]), 0)
        self.anchor_info["wall_opens"] = (x, y, z)
        # reveal: the first column where the wall is open
        x, y, z = pos(n_t)
        # face the middle of the view: between the pyramid, the towers and the lake
        tx_, tz_ = (PX + 160 + LK[0]) / 3.0, (TZ + 160 + LK[1]) / 3.0
        ry = yaw_of(tx_ - x, tz_ - z)
        w.anchor("reveal", x, y, z, ry, 4.0)
        self.anchor_info["reveal"] = (x, y, z)
        self.reveal_yaw = ry
        x, y, z = pos(it)
        door = self.door
        w.anchor("terminal", x, y, z, yaw_of(door[0] - x, door[2] - z), 0)
        self.anchor_info["terminal"] = (x, y, z)
        w.anchor("hq_entrance", door[0], door[1], door[2], YAW["west"], 0)
        self.anchor_info["hq_entrance"] = door

    def run(self):
        self.fields()
        self.carve()
        self.surface()
        self.wall_lights()
        self.headquarters()
        self.plate_and_towers()
        self.rail_line()
        self.monorail()
        self.trees()
        self.flora()
        self.ground_lights()
        self.canopy_lights()
        self.make_anchors()


def dirt_under_cover(w):
    """Grass, podzol and mycelium with a solid block on top turn to dirt in the game, so draw them as dirt: the canvas
    then shows what the game will (under buildings, trunks and paving nobody sees the difference).  Same test as
    build.py: a full cube above, not glass or ice."""
    import compile as comp                      # tools/world is on sys.path (build.py and __main__ both put it there)
    pal = w.palette
    dirt = w._id("dirt")
    solid = np.zeros(len(w.palette), bool)
    grass = np.zeros(len(w.palette), bool)
    for g in range(2, len(pal)):
        solid[g] = (not comp.needs_neighbours(comp.canon(pal[g]))) and not any(k in pal[g] for k in ("glass", "ice"))
        grass[g] = pal[g].split(":", 1)[1].split("[")[0] in ("grass_block", "podzol", "mycelium")
    a = w.a
    covered = grass[a[:, :-1, :]] & solid[a[:, 1:, :]]
    a[:, :-1, :][covered] = dirt
    return int(covered.sum())


def build(w):
    g = Geo(w)
    g.run()
    dirt_under_cover(w)
    w.geo = g          # handy for the checks below; the compiler ignores it
    return g


# ------------------------------------------------------------------------------------------------ the wagon
def wagon(w, x, y, z, facing):
    """A flat car-carrying wagon, about 5 x 9, low railings.  (x, y, z) = where the player's feet stand on it
    (a train anchor): the bed is the cell at y - 1, centred on x, z; `facing` is the direction of travel
    ('north', 'south', 'east', 'west') along its long axis.  Not placed by the set by default."""
    x, y, z = int(math.floor(x)), int(math.floor(y)), int(math.floor(z))
    ax = DIRV[facing]
    lx = (4, 2) if ax[0] != 0 else (2, 4)        # half extents along x, z
    bed = "gray_concrete"
    stripe = "yellow_concrete"
    for dx in range(-lx[0], lx[0] + 1):
        for dz in range(-lx[1], lx[1] + 1):
            edge = abs(dx) == lx[0] or abs(dz) == lx[1]
            w.set(x + dx, y - 1, z + dz, stripe if edge else bed)
            if edge:
                corner = abs(dx) == lx[0] and abs(dz) == lx[1]
                if corner:
                    w.set(x + dx, y, z + dz, "iron_block")
                    w.set(x + dx, y + 1, z + dz, "iron_block")
                else:
                    w.set(x + dx, y, z + dz, "iron_bars")
    # a drawbar at each end
    for sgn in (-1, 1):
        w.set(x + sgn * (lx[0] + 1) * (1 if ax[0] else 0), y - 1, z + sgn * (lx[1] + 1) * (1 if ax[1] else 0), "iron_block")


# ================================================================================================ checks and previews
def validate_blocks(w):
    import json
    path = r"D:\genesis-vr\work\mcdata\out\reports\blocks.json"
    if not os.path.exists(path):
        return "blocks.json not found"
    data = json.load(open(path))
    bad = []
    for nm in w.palette[1:]:
        base = nm
        props = {}
        if "[" in nm:
            base, rest = nm.split("[", 1)
            for kv in rest.rstrip("]").split(","):
                k, v = kv.split("=")
                props[k] = v
        d = data.get(base)
        if d is None:
            bad.append(nm)
            continue
        for k, v in props.items():
            if k not in d.get("properties", {}) or v not in d["properties"][k]:
                bad.append(nm)
    return bad


def rail_profile(w, g, path):
    from PIL import Image, ImageDraw
    import voxel
    tmp = path + ".tmp.png"
    voxel.preview(w, tmp, "y", 125)
    im = Image.open(tmp).convert("RGB")
    os.remove(tmp)
    sc = im.size[0] / SX
    d = ImageDraw.Draw(im)
    P = g.P
    pts = [(P["x"][i] * sc, P["z"][i] * sc) for i in range(len(P["x"]))]
    n = len(pts)
    for i in range(1, n):
        f = (P["hq"][i] - FEND) / (F0 - FEND)
        col = (int(255 * f), int(60 + 120 * (1 - f)), int(255 * (1 - f)))
        d.line([pts[i - 1], pts[i]], fill=col, width=3)
    for nm, (x, y, z) in g.anchor_info.items():
        d.ellipse([x * sc - 3, z * sc - 3, x * sc + 3, z * sc + 3], outline=(255, 255, 0))
        if nm in ("start", "reveal", "terminal", "hq_entrance", "wall_opens"):
            d.text((x * sc + 5, z * sc - 5), nm, fill=(255, 255, 255))
    # side graph below
    gh = 220
    out = Image.new("RGB", (im.size[0], im.size[1] + gh), (20, 20, 24))
    out.paste(im, (0, 0))
    d = ImageDraw.Draw(out)
    X0, Y0_ = 30, im.size[1] + gh - 20
    sx = (im.size[0] - 60) / P["dist"][-1]
    sy = (gh - 40) / 100.0
    for i in range(1, n):
        d.line([(X0 + P["dist"][i - 1] * sx, Y0_ - P["hq"][i - 1] * sy), (X0 + P["dist"][i] * sx, Y0_ - P["hq"][i] * sy)], fill=(255, 200, 80), width=2)
    for nm, (x, y, z) in g.anchor_info.items():
        i = int(np.argmin(np.hypot(P["x"] - x, P["z"] - z)))
        d.line([(X0 + P["dist"][i] * sx, Y0_), (X0 + P["dist"][i] * sx, Y0_ - 4)], fill=(255, 255, 255))
    d.text((X0, im.size[1] + 4), "deck top y along the path (distance ->)", fill=(255, 255, 255))
    out.save(path)


def _classes(w):
    names = w.palette
    n = len(names)
    transp = np.zeros(n, dtype=bool)         # light passes through
    nonsolid = np.zeros(n, dtype=bool)       # air can flow through (for the closed-shell test)
    emit = np.zeros(n, dtype=np.int8)
    sightclear = np.zeros(n, dtype=bool)     # does not block a line of sight
    for i, nm in enumerate(names):
        if nm is None:
            nonsolid[i] = True
            continue
        b = nm.split(":", 1)[1]
        base = b.split("[")[0]
        fluidlike = base in ("water",)
        plants = base in ("air", "short_grass", "tall_grass", "fern", "large_fern", "dandelion", "poppy", "cornflower",
                          "azure_bluet", "oxeye_daisy", "allium", "lily_pad", "light")
        glassy = "glass" in base or base == "iron_bars"
        nonsolid[i] = plants or fluidlike
        transp[i] = plants or fluidlike or glassy or "leaves" in base or base in ("end_rod",)
        sightclear[i] = plants or fluidlike or glassy
        if base in ("sea_lantern", "glowstone", "shroomlight", "ochre_froglight", "pearlescent_froglight", "verdant_froglight", "lantern"):
            emit[i] = 15
        elif base == "end_rod":
            emit[i] = 14
        elif base == "light":
            emit[i] = int(b.split("level=")[1].split("]")[0].split(",")[0])
    return transp, nonsolid, emit, sightclear


def check_closed(w):
    from scipy import ndimage
    _, nonsolid, _, _ = _classes(w)
    open_ = nonsolid[w.a] | (w.a == 0)
    lab, nl = ndimage.label(open_)
    seed = (160, 60, 160)
    assert w.a[seed] == 1, w.get(*seed)
    comp = lab == lab[seed]
    touches = bool(comp[0].any() or comp[-1].any() or comp[:, 0].any() or comp[:, -1].any() or comp[:, :, 0].any() or comp[:, :, -1].any())
    untouched = int(((w.a == 0) & comp).sum())
    # any other big air pockets? (components that are air cells but separate: reported)
    return dict(reaches_boundary=touches, untouched_cells_in_component=untouched, volume=int(comp.sum()))


def compute_light(w):
    transp, _, emit, _ = _classes(w)
    a = w.a
    L = emit[a].astype(np.int8)
    T = transp[a] | (a == 1)
    for _ in range(15):
        best = L.copy()
        for ax in range(3):
            sl_a = [slice(None)] * 3
            sl_b = [slice(None)] * 3
            sl_a[ax] = slice(1, None)
            sl_b[ax] = slice(None, -1)
            sa, sb = tuple(sl_a), tuple(sl_b)
            best[sa] = np.maximum(best[sa], L[sb] - 1)
            best[sb] = np.maximum(best[sb], L[sa] - 1)
        newL = np.where(T, np.maximum(L, best), L)
        if np.array_equal(newL, L):
            break
        L = newL
    return L


def cast(w, p0, p1, clear, step=0.25):
    """First blocking cell on the segment p0 -> p1 (None if clear)."""
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    dist = np.linalg.norm(d)
    n = int(dist / step)
    for k in range(1, n):
        p = p0 + d * (k / n)
        c = (int(math.floor(p[0])), int(math.floor(p[1])), int(math.floor(p[2])))
        if not w.inside(*c):
            return c
        if not clear[w.a[c]]:
            return c
    return None


def sight_report(w, g):
    """Ray-march from the reveal anchor at eye height toward the pyramid, the lake and the towers."""
    _, _, _, clear = _classes(w)
    clear = clear.copy()
    clear[1] = True
    clear[0] = False
    rx, ry, rz = g.anchor_info["reveal"]
    eye = (rx, ry + 1.62, rz)
    top = LAND + 1
    halfs = [int(math.floor(PYR_HALF - 0.875 * k)) for k in range(PYR_H)]

    def visible(p, slack=0.0):
        """True if the first blocking cell on the way to p is within 1.6 blocks of p (i.e. p's own surface)."""
        hit = cast(w, eye, p, clear)
        if hit is None:
            return True
        c = np.array(hit) + 0.5
        return float(np.linalg.norm(c - np.array(p))) < 1.6 + slack

    res = {"pyramid": {}, "lake": {}, "towers": {}}
    # pyramid: points just off the north and west faces at several heights, plus the apex
    res["pyramid"]["apex"] = visible((PX + 0.5, top + PYR_H + 1.5, TZ + 0.5))
    for k in (6, 14, 22, 30):
        h = halfs[k]
        for off in (-12, 0, 12):
            res["pyramid"][f"north k{k} off{off}"] = visible((PX + 0.5 + off, top + k + 0.5, TZ - h - 0.6))
            res["pyramid"][f"west k{k} off{off}"] = visible((PX - h - 0.6, top + k + 0.5, TZ + 0.5 + off))
    # lake: grid of water-surface points
    lx, lz, la, lb = LK
    for ax in np.linspace(-0.8, 0.8, 9):
        for az in np.linspace(-0.8, 0.8, 7):
            x_, z_ = lx + ax * la, lz + az * lb
            ix, iz = int(x_), int(z_)
            if g.q[ix, iz] < 0.8 and g.Hh[ix, iz] <= WATER_Y - 1:
                res["lake"][(round(x_), round(z_))] = visible((x_, WATER_Y + 1.0, z_))
    # towers: aim at the axis at three heights; the tower counts as seen if the first thing hit lies inside its footprint
    for i, (cx, cz, hx, hz) in enumerate(g.towers):
        L = g.tower_lengths[i]
        seen = 0
        for fy in (0.1, 0.5, 0.9):
            y = TOWER_Y - int(L * fy)
            hit = cast(w, eye, (cx + 0.5, y + 0.5, cz + 0.5), clear)
            if hit is None or (abs(hit[0] - cx) <= hx + 1 and abs(hit[2] - cz) <= hz + 1 and abs(hit[1] - y) <= 3):
                seen += 1
        res["towers"][f"tower {i} L{L}"] = seen
    return eye, res


def light_report(w, g, L, eye):
    a = w.a
    out = {}
    X, Z = np.meshgrid(np.arange(SX), np.arange(SZ), indexing="ij")
    rr = np.hypot(X + 0.5 - CX, Z + 0.5 - CZ)
    Hh = g.Hh
    y_air = np.where(Hh <= WATER_Y - 1, WATER_Y + 1, Hh + 1)
    la = L[X, y_air, Z]
    transp, _, _, _ = _classes(w)
    open_ = (a[X, y_air, Z] == 1) | transp[a[X, y_air, Z]]
    m = (rr < 147) & open_
    out["floor cells"] = int(m.sum())
    out["floor < 7"] = float((la[m] < 7).mean())
    out["floor < 5"] = float((la[m] < 5).mean())
    out["floor mean"] = float(la[m].mean())
    # surfaces: air cells next to solid on walls/ceiling (above y 24)
    air = a == 1
    solid = (a > 1) & ~transp[a]
    nb = np.zeros_like(air)
    nb[1:] |= solid[:-1]
    nb[:-1] |= solid[1:]
    nb[:, :, 1:] |= solid[:, :, :-1]
    nb[:, :, :-1] |= solid[:, :, 1:]
    nb[:, :-1] |= solid[:, 1:]
    nb[:, 1:] |= solid[:, :-1]
    surf = air & nb
    surf[:, :18] = False
    out["upper surface air cells"] = int(surf.sum())
    out["upper surface < 5"] = float((L[surf] < 5).mean())
    out["upper surface < 3"] = float((L[surf] < 3).mean())
    # sightline air: along rays from the eye to the pyramid, lake, towers
    return out


def sight_light(w, L, eye, targets):
    vals = []
    transp, _, _, _ = _classes(w)
    for p in targets:
        p = np.array(p, float)
        e = np.array(eye, float)
        n = int(np.linalg.norm(p - e))
        for k in range(1, n):
            q = e + (p - e) * (k / n)
            c = (int(q[0]), int(q[1]), int(q[2]))
            if w.a[c] == 1:
                vals.append(L[c])
    vals = np.array(vals)
    return len(vals), float((vals < 7).mean()), float((vals < 4).mean())


def check_rail(w, g):
    P, a = g.P, w.a
    transp, _, _, _ = _classes(w)
    n = len(P["x"])
    bad = tot = 0
    for i in range(4, n, 2):
        hq = P["hq"][i]
        yA = int(math.ceil(hq))
        for q in range(-3, 4):
            cx = int(math.floor(P["x"][i] + P["nx"][i] * q))
            cz = int(math.floor(P["z"][i] + P["nz"][i] * q))
            tot += 1
            y = yA + 3
            while y > 0 and (a[cx, y, cz] == 1 or "light" in (w.palette[a[cx, y, cz]] or "")):
                y -= 1
            nm = w.palette[a[cx, y, cz]] or ""
            top = y + (0.5 if "slab" in nm else 1.0)
            air_ok = all(a[cx, yy, cz] == 1 or "light" in (w.palette[a[cx, yy, cz]] or "")
                         for yy in range(int(math.ceil(top)), int(math.ceil(top)) + 6))
            if not (abs(top - hq) <= 0.5 and air_ok):
                bad += 1
    horiz = np.concatenate([[0], np.cumsum(np.hypot(np.diff(P["x"]), np.diff(P["z"])))])
    worst = 0.0
    for span in (6, 12, 24):          # in blocks of path
        k = int(span / DS)
        drop = P["hq"][:-k] - P["hq"][k:]
        run = horiz[k:] - horiz[:-k]
        worst = max(worst, float((drop / np.maximum(run, 1e-6)).max()))
    # anchor spacing (horizontal path distance)
    names = ["start"] + [f"train_{k}" for k in range(1, g.n_train + 1)]
    pos = []
    for nm in names:
        x, y, z = g.anchor_info[nm]
        i = int(np.argmin(np.hypot(P["x"] - x, P["z"] - z)))
        pos.append(P["dist"][i])
    gaps = np.diff(pos)
    steps = np.abs(np.diff(P["hq"])).max()
    return dict(cross_sections_checked=tot, cross_sections_bad=bad, worst_slope_over_6_12_24_block_spans=round(worst, 3),
                anchor_gaps_3d=(round(float(gaps.min()), 1), round(float(gaps.max()), 1)), max_step_between_samples=float(steps),
                total_path_length=round(float(P["dist"][-1]), 1), tunnel_closed_blocks=round((g.open_from) * DS, 1))


_RGB = [
    ("sea_lantern", (255, 245, 215)), ("glowstone", (255, 214, 120)), ("shroomlight", (245, 160, 70)),
    ("froglight", (255, 225, 150)), ("light[", (255, 0, 255)), ("lantern", (255, 220, 160)),
    ("water", (50, 100, 200)), ("lava", (240, 110, 20)), ("grass_block", (95, 160, 70)), ("moss", (85, 130, 60)),
    ("podzol", (110, 80, 40)), ("coarse_dirt", (120, 85, 60)), ("dirt", (130, 95, 65)), ("sand", (225, 210, 160)),
    ("gravel", (140, 135, 130)), ("clay", (160, 165, 180)), ("leaves", (50, 125, 50)), ("cherry_leaves", (240, 160, 200)),
    ("log", (105, 80, 50)), ("glass", (160, 210, 230)), ("grass", (80, 150, 60)), ("fern", (60, 130, 60)),
    ("tuff", (110, 108, 98)), ("diorite", (170, 168, 165)), ("andesite", (135, 135, 130)), ("granite", (150, 105, 85)), ("dripstone", (125, 100, 80)),
    ("terracotta", (140, 90, 65)), ("cobblestone", (115, 115, 115)), ("deepslate", (60, 60, 68)), ("blackstone", (40, 36, 44)),
    ("white_concrete", (235, 235, 235)), ("quartz", (236, 230, 222)), ("light_gray", (165, 165, 165)),
    ("gray_concrete", (80, 82, 88)), ("black_concrete", (20, 20, 24)), ("polished_andesite", (150, 152, 150)),
    ("smooth_stone", (160, 160, 160)), ("stone_bricks", (130, 130, 130)), ("stone", (125, 125, 125)),
    ("yellow", (230, 200, 60)), ("blue", (60, 90, 190)), ("iron", (205, 205, 205)), ("end_rod", (255, 255, 255)),
    ("poppy", (220, 40, 40)), ("dandelion", (240, 220, 40)), ("lily", (50, 140, 60)),
]


def _palette_rgb(w):
    out = np.zeros((len(w.palette), 3), dtype=np.float32)
    for i, nm in enumerate(w.palette):
        if nm is None:
            continue
        b = nm.split(":", 1)[1]
        col = (200, 80, 200)
        for key, rgb in _RGB:
            if key in b:
                col = rgb
                break
        out[i] = col
    return out


def render(w, eye, yaw, pitch, fov, size, path, maxd=420.0, step=0.5, glass_clear=True, L=None):
    """Ray-marched preview.  With a light array L the picture is shaded by block light (roughly what the game shows);
    returns the block-light levels of the air cells next to every visible surface."""
    from PIL import Image
    Wd, Ht = size
    transp, _, emit, clear = _classes(w)
    iswater = np.array([(nm or '').endswith(':water') for nm in w.palette])
    opaque = ~((clear & ~iswater) | (np.arange(len(w.palette)) == 1))
    if not glass_clear:
        opaque = ~(np.arange(len(w.palette)) == 1)
    opaque[0] = True
    rgb = _palette_rgb(w)
    lit = emit > 0
    xs = (np.arange(Wd) + 0.5) / Wd * 2 - 1
    ys = 1 - (np.arange(Ht) + 0.5) / Ht * 2
    th = math.tan(math.radians(fov) / 2)
    cam = np.stack(np.broadcast_arrays(xs[None, :] * th, ys[:, None] * th * Ht / Wd, np.ones((Ht, Wd))), -1).reshape(-1, 3)
    yw, pt = math.radians(yaw), math.radians(pitch)
    f = np.array([-math.sin(yw) * math.cos(pt), -math.sin(pt), math.cos(yw) * math.cos(pt)])
    r = np.array([-math.cos(yw), 0, -math.sin(yw)])
    u = np.cross(r, f)
    d = cam[:, 0:1] * r + cam[:, 1:2] * u + cam[:, 2:3] * f
    d /= np.linalg.norm(d, axis=1, keepdims=True)
    n = d.shape[0]
    e = np.array(eye, float)
    img = np.zeros((n, 3), dtype=np.float32)
    sky = np.array([30, 24, 20], dtype=np.float32)
    img[:] = sky
    active = np.arange(n)
    prev = np.floor(e + d * 0.0).astype(int)
    prevc = np.tile(np.floor(e).astype(int), (n, 1))
    lvs = []
    t = 0.2
    while t < maxd and len(active):
        p = e + d[active] * t
        c = np.floor(p).astype(int)
        inb = (c[:, 0] >= 0) & (c[:, 0] < SX) & (c[:, 1] >= 0) & (c[:, 1] < SY) & (c[:, 2] >= 0) & (c[:, 2] < SZ)
        cc = np.clip(c, 0, [SX - 1, SY - 1, SZ - 1])
        ids = w.a[cc[:, 0], cc[:, 1], cc[:, 2]]
        hit = inb & opaque[ids]
        out = ~inb
        if hit.any():
            hi = active[hit]
            hc = c[hit]
            pc = prevc[hi]
            dc = pc - hc
            shade = np.where(dc[:, 1] > 0, 1.0, np.where(dc[:, 1] < 0, 0.45, np.where(dc[:, 0] != 0, 0.78, 0.66)))
            if L is not None:
                pcc = np.clip(pc, 0, [SX - 1, SY - 1, SZ - 1])
                lv = L[pcc[:, 0], pcc[:, 1], pcc[:, 2]].astype(np.float32)
                lvs.append(lv)
                shade = shade * (0.18 + 0.82 * np.clip(lv / 12.0, 0, 1) ** 0.8)
            col = rgb[ids[hit]] * shade[:, None]
            col = np.where(lit[ids[hit]][:, None], rgb[ids[hit]] * 1.2, col)
            fog = np.clip(t / maxd, 0, 1)[..., None] if isinstance(t, np.ndarray) else min(t / maxd, 1.0) * 0.55
            col = col * (1 - fog) + np.array([200, 160, 90]) * fog
            img[hi] = np.clip(col, 0, 255)
        keep = ~(hit | out)
        prevc[active] = c
        active = active[keep]
        t += step
    arr = img.reshape(Ht, Wd, 3).astype(np.uint8)
    Image.fromarray(arr).save(path)
    return np.concatenate(lvs) if lvs else None


def previews(w, g, outdir, L=None):
    from PIL import Image
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import voxel
    os.makedirs(outdir, exist_ok=True)
    for at in (24, 60, 100, 125):
        voxel.preview(w, os.path.join(outdir, f"top_cut{at}.png"), "y", at)
    voxel.preview(w, os.path.join(outdir, "top_full.png"), "y", None)
    voxel.preview(w, os.path.join(outdir, f"slice_z{TZ}_pyramid.png"), "z", TZ)
    voxel.preview(w, os.path.join(outdir, f"slice_x{PX}_pyramid.png"), "x", PX)
    voxel.preview(w, os.path.join(outdir, "slice_x160_centre.png"), "x", 160)
    rx, ry, rz = g.anchor_info["reveal"]
    eye = (rx, ry + 1.62, rz)
    rail_profile(w, g, os.path.join(outdir, "rail_profile.png"))
    stats = {}
    stats["reveal"] = render(w, eye, g.reveal_yaw, 8, 100, (900, 520), os.path.join(outdir, "view_reveal.png"), L=L)
    P = g.P
    # a few more viewpoints
    for nm in ("train_3", "train_8", "train_14", "train_20", "terminal"):
        if nm in g.anchor_info:
            x, y, z = g.anchor_info[nm]
            i = int(np.argmin(np.hypot(P["x"] - x, P["z"] - z)))
            yaw = math.degrees(math.atan2(-P["nx"][i], P["nz"][i]))
            stats[nm] = render(w, (x, y + 1.62, z), yaw, 5, 100, (800, 450), os.path.join(outdir, f"view_{nm}.png"), L=L)
    lyaw = math.degrees(math.atan2(-(LK[0] - rx), LK[1] - rz))
    stats["reveal_lake"] = render(w, eye, lyaw, 14, 100, (900, 520), os.path.join(outdir, "view_reveal_lake.png"), L=L)
    stats["reveal_wide"] = render(w, eye, g.reveal_yaw, 0, 140, (1000, 480), os.path.join(outdir, "view_reveal_wide.png"), L=L)
    stats["from_nw"] = render(w, (70, 60, 80), -45, 10, 100, (900, 520), os.path.join(outdir, "view_overview_sw.png"), L=L)
    stats["from_south"] = render(w, (160, 90, 290), 180, 14, 100, (900, 520), os.path.join(outdir, "view_overview_from_south.png"), L=L)
    stats["from_west"] = render(w, (30, 80, 170), -90, 12, 100, (900, 520), os.path.join(outdir, "view_overview_from_west.png"), L=L)
    stats["floor_north"] = render(w, (160, 40, 20), 0, 12, 100, (900, 520), os.path.join(outdir, "view_from_floor_north.png"), L=L)
    stats["ground_lake"] = render(w, (200, 22, 215), 0, -4, 100, (900, 520), os.path.join(outdir, "view_ground_lake.png"), L=L)
    if L is not None:
        for k, v in stats.items():
            if v is not None and len(v):
                print(f"  visible surfaces in view '{k}': {len(v)} px, <7: {float((v < 7).mean()):.1%}, <4: {float((v < 4).mean()):.1%}, mean {float(v.mean()):.1f}")


if __name__ == "__main__":
    import time
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))
    from voxel import World
    from layout import SETS
    origin, size = SETS["geofront"]
    w = World("geofront", origin, size)
    t0 = time.time()
    g = build(w)
    print(f"built in {time.time() - t0:.1f}s; palette {len(w.palette)} entries")
    out = os.path.join(os.path.dirname(here), "preview", "geofront")
    os.makedirs(out, exist_ok=True)
    print("anchors:")
    for k, v in w.anchors.items():
        loc = {"x": v["x"] - origin[0], "y": v["y"] - origin[1], "z": v["z"] - origin[2]}
        print(f"  {k:12s} ({loc['x']:.1f}, {loc['y']:.1f}, {loc['z']:.1f}) yaw {v['yaw']:.0f} pitch {v['pitch']:.0f}")
    if "--fast" in sys.argv:
        previews(w, g, out)
        sys.exit(0)
    print("block validation (invalid entries):", validate_blocks(w))
    from voxel import World as _W
    tw_ = _W("t", (0, 0, 0), (40, 12, 40))
    for k_, f_ in enumerate(("north", "east", "south", "west")):
        wagon(tw_, 20, 4, 20, f_)
    print("wagon ok; cells:", int((tw_.a > 1).sum()))
    print("closed shell:", check_closed(w))
    print("rail:", check_rail(w, g))
    eye, sight = sight_report(w, g)
    print("eye", tuple(round(v, 1) for v in eye))
    py, lk, tw = sight["pyramid"], sight["lake"], sight["towers"]
    print(f"  pyramid points visible {sum(py.values())}/{len(py)}  (apex {py['apex']})")
    print(f"  lake points visible {sum(lk.values())}/{len(lk)}")
    print(f"  towers seen (>=1 of 3 heights) {sum(1 for v in tw.values() if v)}/{len(tw)}; per tower {list(tw.values())}")
    t0 = time.time()
    L = compute_light(w)
    print(f"light computed in {time.time() - t0:.1f}s")
    print(light_report(w, g, L, eye))
    tg = [(PX + 0.5, 60, TZ + 0.5), (PX - 20, 40, TZ - 30), (LK[0], 16, LK[1]), (CX, 125, CZ), (CX + 30, 100, CZ - 20), (CX - 30, 110, CZ + 20)]
    print("air along sightlines (count, frac <7, frac <4):", sight_light(w, L, eye, tg))
    n_emit = int((_classes(w)[2][w.a] > 0).sum())
    print("light-emitting cells:", n_emit, " hidden light blocks:", int(sum((w.a == w._ix.get(f'minecraft:light[level={v}]', -1)).sum() for v in range(16))))
    print("trees:", g.tree_count, " flora:", g.n_flora, " wall emitters:", g.n_wall_lights, " ground lights:", g.n_ground_lights, " canopy lights:", g.n_canopy_lights)
    previews(w, g, out, L)
