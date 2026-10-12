"""OUTSKIRTS - a deserted seaside town on the edge of the fortress city, blazing midsummer noon.

Footprint 256 x 128 x 256 (x east, y up, z south). Standing level ("ground") is local y = 32: the top solid block of open
ground is y = 31 and a player's feet are at y = 32. Variations on that: the railway platform and station hall floor are one
block up (feet 33); pavements, the forecourt and the promenade are bottom slabs (feet 32.5); the road is at 32.
Anchors are given in the same feet convention, at block centres (x.5 / z.5) for standing places.

PLAN (x east ->, z south v)
    x   0..12   rear bank behind the railway (hill, rock outcrops)
    x  13..30   two tracks in a shallow cutting with portals into the hills at z 52 and 204; catenary; train on x 26..30
    x  31..41   platform (z 64..192), canopy, benches, name boards; "start" anchor
    x  42..53   station hall with ticket gates; exit east on the centre line z = 128
    x  54..91   forecourt: payphone booth (64..67, 112..116), planters, kiosk, bus stop, notice boards, shuttered arcades N and S
    x  92..184  MAIN STREET along z = 128 (road z 123..133, pavements z 119..122 / 134..137), cross street x 112..120,
                side street x 144..152 that becomes the hill road; promenade x 172..184 at the sea
    x 186..240  bay (sea surface y 31, floor ~19); beach on the west shore; far headland closes the bay at the east edge
    z  <  60    northern hills; the hill road climbs the ridge hill to the lookout bench (188, 54) at y 51 and leaves it by the
                west end, falling at most a third of a block per block to the portal forecourt at y 44 (x 176, z 35)
    z  <  40    hollow behind the ridge with the portal wall (z = 22): open striped blast gate, hall inside the hill; the
                floor runs level (y 44) from the forecourt through the gate onto the rail platform
    z > 190     southern hills with pylon lines
The angel corridor is the strip z ~ 100..158, x > 168 down to the water: only low things stand in it.

Everything is deterministic (seeded). Run this file directly to build and write previews + sightline / void checks.
Public API: build(w, with_car=False) and car(w, x, y, z, facing, color) (see its docstring).
"""
import math
import os
import random
import sys

import numpy as np

GY = 32                      # feet level of open ground; top solid block is GY - 1
N = 256
DIRS = {"north": (0, -1), "south": (0, 1), "east": (1, 0), "west": (-1, 0)}
RIGHT = {"north": "east", "east": "south", "south": "west", "west": "north"}
LEFT = {v: k for k, v in RIGHT.items()}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}
YAW = {"south": 0.0, "west": 90.0, "north": 180.0, "east": -90.0}   # Minecraft yaw for looking toward a side


# --------------------------------------------------------------------------------------------- small helpers
def bs(name, **kw):
    """Block string with state: bs('oak_stairs', facing='east') -> 'oak_stairs[facing=east]'."""
    if not kw:
        return name
    return name + "[" + ",".join("%s=%s" % (k, str(v).lower() if isinstance(v, bool) else v) for k, v in kw.items()) + "]"


def ss(t):
    """smoothstep clamp 0..1"""
    t = np.clip(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def stair(w, x, y, z, mat, facing, half="bottom", shape="straight"):
    w.set(x, y, z, bs(mat + "_stairs", facing=facing, half=half, shape=shape))


def slab(w, x, y, z, mat, typ="bottom"):
    w.set(x, y, z, bs(mat + "_slab", type=typ))


def put_if_air(w, x, y, z, block):
    if w.inside(x, y, z) and w.a[x, y, z] <= 1:
        w.a[x, y, z] = w._id(block)


class Site:
    """Everything the generators share: the world, the random stream, the ground height map and keep-clear masks."""

    def __init__(self, w):
        self.w = w
        self.rng = random.Random(1999)
        self.nrng = np.random.RandomState(2015)
        self.T = None                                  # top solid block height of the natural ground, int [x, z]
        self.keep = np.zeros((N, N), dtype=bool)       # no trees / grass clutter here
        self.road = np.zeros((N, N), dtype=bool)
        self.occ = np.zeros((N, N), dtype=bool)        # footprints of buildings and big props
        self.notes = []

    def top(self, x, z):
        return int(self.T[x, z])


# --------------------------------------------------------------------------------------------- terrain
def hills(site):
    """Float surface (top block y) for the natural terrain: flat town, ridge hill, rim of hills, bay and headland."""
    nr = site.nrng
    X, Z = np.meshgrid(np.arange(N, dtype=float), np.arange(N, dtype=float), indexing="ij")

    def bump(cx, cz, rx, rz, h, p=2.0):
        d = ((X - cx) / rx) ** 2 + ((Z - cz) / rz) ** 2
        return h * np.clip(1 - d, 0, 1) ** p

    h = np.zeros((N, N))
    # northern massif: the ridge hill with the lookout, and the high ground behind it (tunnel hill)
    h += bump(176, 60, 84, 38, 31)
    h += bump(190, -12, 150, 58, 46)
    h += bump(105, 30, 95, 48, 30)
    h += bump(30, 28, 60, 58, 30)
    h += bump(228, 72, 26, 22, 18)           # the two shoulders that flank the sea gap (north one kept off the ridge view)
    h += bump(216, 176, 32, 24, 14)
    # western bank behind the railway and south-west hills
    h += bump(-6, 128, 30, 150, 20)
    h += bump(30, 232, 70, 52, 30)
    # southern hills flanking the gap, and the far south
    h += bump(225, 212, 80, 60, 34)
    h += bump(120, 240, 110, 48, 28)
    h += bump(80, 170 + 60, 60, 40, 14)
    # general rim so that nothing ever shows the void behind the set
    d_edge = np.minimum(np.minimum(X, 255 - X), np.minimum(Z, 255 - Z))
    rim = 26 * (1 - np.clip(d_edge / 56, 0, 1)) ** 1.4
    gap_open = ss((np.abs(Z - 128) - 52) / 20)                    # 0 in the sea gap, 1 outside
    east_open = np.where(X > 170, gap_open, 1.0)
    h += rim * east_open
    # soft natural roughness
    for i in range(7):
        kx, kz = nr.uniform(0.02, 0.09, 2) * nr.choice([-1, 1], 2)
        h += nr.uniform(0.8, 2.2) * np.sin(kx * X + kz * Z + nr.uniform(0, 6.3)) * (h > 4)
    # the town stays dead flat
    def zone(x0, x1, z0, z1, rw, re, rn, rs):
        dx = np.maximum(0, np.maximum((x0 - X) / rw, (X - x1) / re))
        dz = np.maximum(0, np.maximum((z0 - Z) / rn, (Z - z1) / rs))
        return np.hypot(dx, dz)
    d = np.minimum(zone(8, 150, 68, 190, 6, 28, 26, 26),      # the town block
                   zone(8, 215, 108, 148, 6, 24, 34, 34))      # ... and the corridor to the sea
    h = h * ss(d)
    T = 31.0 + h

    # the sea in the gap between the two hills: beach slope from x~188, floor ~18 deep
    Xw = X + 7 * np.sin(Z * 0.07 + 1) + 3 * np.sin(Z * 0.21)          # a wobbly shore
    Zw = np.abs(Z - 128) + 6 * np.sin(X * 0.09)
    bay_w = 26 + 0.24 * np.clip(X - 190, 0, 65)                       # the bay widens toward the open sea
    s = np.clip((Xw - 186) / 18, 0, 1) ** 1.15 * (1 - ss((Zw - bay_w) / 26))
    T = T * (1 - s) + (31.5 - 14.0 * np.clip((Xw - 186) / 16, 0, 1) - 1.5 * np.clip((X - 215) / 40, 0, 1)) * s
    # the headlands flank the bay and run out to the east edge; between them there is open water all the way (no closing hill)
    ro = 0.8 + 0.2 * np.sin(Z * 0.11) * np.cos(Z * 0.047 + 1.3)
    closure = ss((np.abs(Z - 128) - 40) / 32)
    T = np.maximum(T, (19 + 42 * ss((X - 222) / 33) * ro) * closure)
    return T


# The hill road: feet height of the road surface at each waypoint (x, z, y).  Anchors "ridge" etc. sit on it.
HILL_ROAD = [
    (148, 128, 32.0), (148, 108, 32.0), (154, 94, 34.0), (168, 86, 38.0), (184, 80, 42.0), (198, 72, 45.5),
    (204, 62, 49.5), (194, 56, 51.0), (186, 52, 51.0),
    # the way down from the lookout to the portal forecourt: x, z are the waypoints the story drives (tools/story/paths.py
    # ridge_to_gate_xz), so the carriageway is cut under the car; y stays level across the bench (51), then falls evenly to the
    # forecourt level (44) at a third of a block per block at most, and runs level into the forecourt (the end heights sit a hair
    # under 44 so that the smoothing in catmull() lands the road exactly flush with the forecourt paving where it enters, x 176)
    (180.0, 50.8, 51.0), (176.5, 49.2, 51.0), (173.5, 48.9, 49.9), (171.3, 47.6, 48.7), (170.4, 45.0, 47.5), (170.2, 41.5, 46.2),
    (170.6, 38.2, 44.8), (173.0, 36.4, 43.7), (177.0, 35.4, 43.7), (186.0, 36.0, 43.7),
]
RIDGE = (194, 56)            # the car stops here (feet y 51.5 -> plateau at 52)
RIDGE_Y = 51
PLATEAU = (188, 54, 21, 11)  # cx, cz, rx, rz of the flat lookout bench
HOLLOW = (188, 38, 22, 14)   # the flat floor in front of the tunnel portal (y 44.5)
HOLLOW_Y = 44
HOLLOW_PAVED = (176, 41)     # the portal forecourt: x from here east, z below this (the road ends on it, flush at feet 44)


def catmull(points, ds=0.6):
    """Smooth path through (x, z, y) waypoints, sampled every ~ds blocks; y is smoothed so the grade never kinks."""
    P = np.array(points, dtype=float)
    out = []
    for i in range(len(P) - 1):
        p0, p1, p2, p3 = P[max(i - 1, 0)], P[i], P[i + 1], P[min(i + 2, len(P) - 1)]
        n = max(2, int(np.hypot(*(p2[:2] - p1[:2])) / ds))
        for k in range(n):
            t = k / n
            xz = 0.5 * (2 * p1[:2] + (-p0[:2] + p2[:2]) * t + (2 * p0[:2] - 5 * p1[:2] + 4 * p2[:2] - p3[:2]) * t * t
                        + (-p0[:2] + 3 * p1[:2] - 3 * p2[:2] + p3[:2]) * t ** 3)
            out.append((xz[0], xz[1], p1[2] + (p2[2] - p1[2]) * t))
    out.append(tuple(P[-1]))
    A = np.array(out)
    k = 14                                                       # moving average of y over ~ +-8 blocks
    y = np.pad(A[:, 2], k, mode="edge")
    A[:, 2] = np.convolve(y, np.ones(2 * k + 1) / (2 * k + 1), mode="valid")
    return A


def sculpt(site, Tf):
    """Cut and fill the hill road into the float terrain; returns the road mask data."""
    A = catmull(HILL_ROAD)
    site.road_path = A
    hw = 3.5
    R = hw + 1.3 + 15
    dist = np.full((N, N), 1e9)
    ry = np.zeros((N, N))
    # the road height of a cell is that of the nearest path sample, but blended (Gaussian, sigma 2.5) with the samples around it:
    # on the inside of a bend of a climbing road the two arms are at different heights and the nearest-sample height jumps
    # by a block or more along the bisector; blended it is a ramp
    sig, rr = 2.5, 10
    num = np.zeros((N, N))
    den = np.zeros((N, N))
    for px, pz, py in A:
        x0, x1 = max(0, int(px - R)), min(N, int(px + R) + 1)
        z0, z1 = max(0, int(pz - R)), min(N, int(pz + R) + 1)
        gx, gz = np.meshgrid(np.arange(x0, x1), np.arange(z0, z1), indexing="ij")
        d = np.hypot(gx - px, gz - pz)
        m = d < dist[x0:x1, z0:z1]
        dist[x0:x1, z0:z1] = np.where(m, d, dist[x0:x1, z0:z1])
        ry[x0:x1, z0:z1] = np.where(m, py, ry[x0:x1, z0:z1])
        a0, a1 = max(0, int(px - rr)), min(N, int(px + rr) + 1)
        b0, b1 = max(0, int(pz - rr)), min(N, int(pz + rr) + 1)
        hx, hz = np.meshgrid(np.arange(a0, a1), np.arange(b0, b1), indexing="ij")
        wt = np.exp(-((hx - px) ** 2 + (hz - pz) ** 2) / (sig * sig))
        num[a0:a1, b0:b1] += wt * py
        den[a0:a1, b0:b1] += wt
    ry = np.where(den > 1e-9, num / np.maximum(den, 1e-9), ry)
    # the stopping place "ridge": the outer strip of the carriageway on its sea side, within 8 blocks of the stop, is lowered by up to
    # 1.4 blocks, so that the road's own edge no longer hides the ground below from a seated eye (the car's 4-wide path stays level)
    X0, Z0 = np.meshgrid(np.arange(N, dtype=float), np.arange(N, dtype=float), indexing="ij")
    ax, az = RIDGE[0] + 0.5, RIDGE[1] + 0.5
    v = np.array([207.0 - ax, 63.5 - az])
    tt = np.clip(((X0 - ax) * v[0] + (Z0 - az) * v[1]) / (v @ v), 0, 1)
    dseg = np.hypot(X0 - (ax + tt * v[0]), Z0 - (az + tt * v[1]))
    south = ((X0 - ax) * (-v[1]) + (Z0 - az) * v[0]) > 0
    near = 1 - ss((np.hypot(X0 - ax, Z0 - az) - 6.5) / 4)
    ry = ry - 1.6 * ss((dseg - 1.9) / 0.9) * south * near
    wgt = 1 - ss((dist - (hw + 1.3)) / 15)
    wgt[dist > hw + 1.3 + 15] = 0
    Tf = Tf * (1 - wgt) + (ry - 1) * wgt
    site.road_dist, site.road_y, site.road_wgt = dist, ry, wgt
    return Tf


def flatten(Tf, cx, cz, rx, rz, top, fall=10):
    """Level an elliptical bench to top-block height `top`, blending out over `fall` blocks."""
    X, Z = np.meshgrid(np.arange(N, dtype=float), np.arange(N, dtype=float), indexing="ij")
    d = np.hypot((X - cx) / rx, (Z - cz) / rz)
    k = 1 - ss((d - 1) * min(rx, rz) / fall)
    return Tf * (1 - k) + top * k


def terrain(site):
    Tf = hills(site)
    Tf = sculpt(site, Tf)
    Tf = flatten(Tf, HOLLOW[0], HOLLOW[1], HOLLOW[2], HOLLOW[3], HOLLOW_Y - 1, 8)
    # the lookout bench is level but tips away gently on its sea side so the view back to the gap is never grazed by its rim
    X, Z = np.meshgrid(np.arange(N, dtype=float), np.arange(N, dtype=float), indexing="ij")
    dd = np.hypot((X - PLATEAU[0]) / PLATEAU[2], (Z - PLATEAU[1]) / PLATEAU[3])
    kk = 1 - ss((dd - 1) * min(PLATEAU[2], PLATEAU[3]) / 12)
    Tf = Tf * (1 - kk) + (RIDGE_Y - 1 - 0.16 * np.clip(Z - 56, 0, None)) * kk
    # the overlook: from the car's stopping place the ground falls away toward the sea within a few blocks, so that the town, the
    # bay and the angel's spawn lie spread out below a seated eye instead of behind a long flat shelf (the road keeps its own shape)
    ux, uz = 0.445, 0.896                                  # unit vector from the ridge toward the sea gap (230, 128)
    s_ = (X - (RIDGE[0] + 0.5)) * ux + (Z - (RIDGE[1] + 0.5)) * uz
    l_ = (X - (RIDGE[0] + 0.5)) * uz - (Z - (RIDGE[1] + 0.5)) * ux
    wedge = ss((30 - np.abs(l_)) / 16) * ss((s_ - 3.5) / 4) * ss((site.road_dist - 6.0) / 5) * ss((45 - s_) / 15)
    fall = np.maximum(RIDGE_Y - 1 - 1.15 * np.clip(s_ - 6, 0, None), 36 - 0.25 * np.clip(s_ - 17, 0, None))
    fall = np.maximum(fall, 33.0)
    # the road has the last word: the levelled bench and hollow must not leave a bank beside the road where it leaves them
    Tf = Tf * (1 - site.road_wgt) + (site.road_y - 1) * site.road_wgt
    Tf = np.minimum(Tf, Tf * (1 - wedge) + fall * wedge)                # (the overlook falls away beside the road, never under it)
    site.Tf = Tf
    T = np.rint(Tf).astype(int)
    # the road itself: half-block steps so the grade is walkable; slab_y marks the cells that carry a bottom slab
    on = site.road_dist <= 3.5
    on[HOLLOW_PAVED[0]:, :HOLLOW_PAVED[1]] = False           # the portal forecourt is paved over the road's end (tunnel())
    S2 = np.rint(site.road_y * 2).astype(int)
    site.slab_y = np.full((N, N), -1, dtype=int)
    odd = on & (S2 % 2 == 1)
    T = np.where(on, np.where(odd, (S2 - 1) // 2 - 1, S2 // 2 - 1), T)
    site.slab_y = np.where(odd, (S2 - 1) // 2, -1)
    site.hill_road = on
    site.shoulder = (site.road_dist > 3.5) & (site.road_dist <= 4.8)
    site.shoulder[HOLLOW_PAVED[0]:, :HOLLOW_PAVED[1]] = False
    site.T = T
    return T


def lay_terrain(site):
    """Stone, dirt and a surface skin for the whole set, then the sea. Roads and town paving go on top later."""
    w, T = site.w, site.T
    X, Z = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    nr = site.nrng
    ids = {k: w._id(k) for k in ("stone", "dirt", "grass_block", "sand", "gravel", "coarse_dirt", "andesite",
                                 "water", "podzol", "sandstone")}
    gy, gx = np.gradient(T.astype(float))
    slope = np.hypot(gx, gy)
    surf = np.full((N, N), ids["grass_block"], dtype=np.uint16)
    rock = nr.rand(N, N)
    # rock outcrops come in patches (low-frequency blobs), not as per-column noise
    blob = (np.sin(X * 0.21 + 1.3) + np.sin(Z * 0.27 + 0.4) + np.sin((X + Z) * 0.13) + np.sin((X - Z) * 0.17 + 2.0)) / 4
    patch = blob + 0.25 * (rock - 0.5)
    surf = np.where((slope > 1.25) & (patch > 0.30), ids["stone"], surf)
    surf = np.where((slope > 1.9) & (patch > 0.15), ids["andesite"], surf)
    surf = np.where((slope > 0.9) & (slope <= 1.4) & (rock < 0.12), ids["coarse_dirt"], surf)
    surf = np.where((slope > 0.5) & (rock < 0.04), ids["podzol"], surf)
    # shore: sand on the beach and gravel / sand on the seabed
    wet = T < 31
    near = wet.copy()
    for dx in range(-4, 5):
        for dz in range(-4, 5):
            if dx * dx + dz * dz <= 18:
                near |= np.roll(np.roll(wet, dx, 0), dz, 1)
    surf = np.where(near & (T <= 34) & (X > 170), np.where(rock < 0.1, ids["sandstone"], ids["sand"]), surf)
    surf = np.where(wet, np.where(rock < 0.25, ids["gravel"], ids["sand"]), surf)
    # keep the town's own block clear of wild surfaces: dry lawn there (paving is laid later)
    Y = np.arange(128, dtype=np.int32)[None, :, None]
    Tn = T[:, None, :]
    # faces that look out sideways (a column taller than a neighbour) wear the surface skin too, so hillsides read as
    # grass or rock rather than as horizontal strata of dirt and stone
    pad = np.pad(T, 1, mode="edge")
    low = np.minimum(np.minimum(pad[:-2, 1:-1], pad[2:, 1:-1]), np.minimum(pad[1:-1, :-2], pad[1:-1, 2:]))
    exposed = (Y > low[:, None, :] + 0) & (Y <= Tn)
    arr = np.where(Y <= Tn - 4, ids["stone"], np.where(Y < Tn, ids["dirt"], np.where(Y == Tn, surf[:, None, :], 0)))
    arr = np.where(exposed & (Y > Tn - 8) & (Y <= Tn), surf[:, None, :], arr)
    arr = np.where((arr == 0) & (Y <= 30) & (Y > Tn), ids["water"], arr)
    w.a[:] = arr.astype(np.uint16)
    site.wet = wet
    # the sea runs out to the east edge of the set: an invisible barrier column at the edge keeps the water from flowing out into
    # the void (the player sees open water, the surface running out to a clear horizon)
    edge = w.a[N - 1]
    edge[edge == ids["water"]] = w._id("barrier")


# --------------------------------------------------------------------------------------------- shared drawing
def pane(axis):
    """glass pane in a wall running along x or z, with its connections spelled out (nobody updates shapes for us)."""
    return "glass_pane[east=true,west=true]" if axis == "x" else "glass_pane[north=true,south=true]"


def bars(axis):
    return "iron_bars[east=true,west=true]" if axis == "x" else "iron_bars[north=true,south=true]"


def chain_line(w, x0, y0, z0, x1, y1, z1, sag=0.0, mat="iron_chain"):
    """An overhead wire between two points: chain blocks, sagging by `sag` blocks in the middle."""
    n = int(max(abs(x1 - x0), abs(z1 - z0)))
    if n == 0:
        return
    axis = "x" if abs(x1 - x0) >= abs(z1 - z0) else "z"
    last = None
    for i in range(n + 1):
        t = i / n
        x = int(round(x0 + (x1 - x0) * t))
        z = int(round(z0 + (z1 - z0) * t))
        y = int(round(y0 + (y1 - y0) * t - sag * 4 * t * (1 - t)))
        w.set(x, y, z, bs(mat, axis=axis))
        if last is not None and last[1] != y:        # a sag step: join the two blocks with a vertical link
            w.set(x, min(y, last[1]) + (0 if y < last[1] else 0), z, bs(mat, axis=axis))
        last = (x, y, z)


def sign_text(w, x, y, z, lines, glow=False):
    """Text on a sign that was placed at local (x, y, z); written by command after the blocks go down."""
    ax, ay, az = w.abs(x, y, z)
    msgs = ",".join('"%s"' % t for t in (list(lines) + ["", "", "", ""])[:4])
    w.command('data merge block %d %d %d {front_text:{messages:[%s],color:"black"},is_waxed:1b}' % (ax, ay, az, msgs))


def jp(s):
    """Japanese text as \\uXXXX escapes (one backslash in the command) so the command file stays plain ASCII."""
    return "".join(c if ord(c) < 128 else "\\u%04x" % ord(c) for c in s)


def place_wall_sign(w, x, y, z, facing, lines, mat="oak"):
    w.set(x, y, z, bs(mat + "_wall_sign", facing=facing))
    sign_text(w, x, y, z, lines)


# --------------------------------------------------------------------------------------------- railway and station
TRACK_A = (27, 29)             # rails of the track the train stands on
TRACK_B = (17, 19)
PLAT = (31, 41, 64, 192)       # x0, x1, z0, z1 of the platform (top block y = 32 -> feet 33)
PLAT_TOP = 32
CL = 128                       # centre line of the station and the main street
STN = (42, 53, 112, 144)       # the station hall: x0, x1, z0, z1


def cutting(S):
    """The shallow railway cutting through the town block, its two portals into the hills, rails and ballast."""
    w, T = S.w, S.T
    ZN, ZS = 52, 204                       # z of the two portal faces (north, south)
    for z in range(ZN + 1, ZS):
        for x in range(13, 31 + 1):
            if PLAT[0] <= x <= PLAT[1] and PLAT[2] <= z <= PLAT[3]:
                continue
            top = int(T[x, z])
            w.fill(x, 30, z, x, max(top, 31), z, "air")
            w.set(x, 29, z, "gravel" if (x + z) % 7 else "coarse_dirt")
            S.keep[x, z] = True
    # retaining walls on both sides where the ground rises toward the portals
    for z in range(ZN, ZS + 1):
        for x in (12, 32):
            if x == 32 and PLAT[2] <= z <= PLAT[3]:
                continue
            top = int(T[x, z])
            if top > 31:
                w.fill(x, 29, z, x, top, z, "light_gray_concrete")
            S.keep[x, z] = True
    # the portals: a concrete face with a double-track opening, and a dark tunnel behind it
    for zf, d in ((ZN, -1), (ZS, 1)):
        for x in range(12, 33):
            top = int(T[x, zf])
            w.fill(x, 29, zf, x, max(top, 38), zf, "light_gray_concrete")
        # tunnel box: stone shell, hollow inside, black end wall
        w.fill(12, 29, zf + d, 32, 39, zf + d * 12, "stone")
        w.fill(13, 30, zf + d, 31, 37, zf + d * 11, "air")
        w.fill(13, 29, zf + d, 31, 29, zf + d * 11, "gravel")
        w.fill(13, 29, zf + d * 11, 31, 37, zf + d * 12, "black_concrete")
        w.fill(13, 30, zf, 31, 37, zf, "air")                                      # the opening in the face
        w.fill(12, 38, zf, 32, 38, zf, "gray_concrete")                            # lintel and warning stripe
        for x in range(13, 32, 2):
            w.set(x, 37, zf, "yellow_concrete")
        for x in (12, 32):
            w.fill(x, 29, zf, x, 38, zf, "light_gray_concrete")
    for rail_x in TRACK_A + TRACK_B:
        for z in range(ZN - 11, ZS + 12):
            w.set(rail_x, 30, z, bs("rail", shape="north_south"))
    # a chain-link style fence on top of the west retaining wall along the platform
    for z in range(70, 190):
        w.set(12, 32, z, "iron_bars")


def platform(S):
    w = S.w
    x0, x1, z0, z1 = PLAT
    w.fill(x0, 29, z0, x1, PLAT_TOP, z1, "stone")
    rng = S.rng
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if x == x0 + 1:
                b = "yellow_concrete"                           # tactile strip along the edge
            elif x == x0:
                b = "light_gray_concrete"
            else:
                r = rng.random()
                b = "light_gray_concrete" if r < 0.8 else ("smooth_stone" if r < 0.93 else "polished_andesite")
            w.set(x, PLAT_TOP, z, b)
        S.keep[x, z0:z1 + 1] = True
    # half-step ramps at the ends
    for x in range(x0, x1 + 1):
        slab(w, x, PLAT_TOP, z0 - 1, "smooth_stone")
        slab(w, x, PLAT_TOP, z1 + 1, "smooth_stone")
    # a low wall and fence on the east side outside the hall, where the platform would otherwise end in thin air
    for z in range(z0, z1 + 1):
        if STN[2] <= z <= STN[3]:
            continue
        w.set(42, PLAT_TOP, z, "light_gray_concrete")
        w.set(42, PLAT_TOP + 1, z, "iron_bars")
        w.set(42, PLAT_TOP + 2, z, "iron_bars")
    # white line positions: a dashed safety line next to the yellow strip is already given by the strip.


def canopy(S):
    """Flat platform roof on posts, z 92..164, with a blue fascia."""
    w = S.w
    z0, z1 = 92, 164
    for z in range(z0 + 4, z1, 12):
        for x in (40,):
            for y in range(PLAT_TOP + 1, PLAT_TOP + 8):
                w.set(x, y, z, "andesite_wall" if y > PLAT_TOP + 1 else "light_gray_concrete")
    y = PLAT_TOP + 8
    w.fill(34, y, z0, 41, y, z1, "light_gray_concrete")
    w.fill(34, y + 1, z0, 41, y + 1, z0, "blue_concrete")
    w.fill(34, y + 1, z1, 41, y + 1, z1, "blue_concrete")
    w.fill(34, y + 1, z0, 34, y + 1, z1, "blue_concrete")
    w.fill(41, y + 1, z0, 41, y + 1, z1, "white_concrete")
    for z in range(z0 + 6, z1, 12):                      # skylight strips: glass between roof beams
        w.fill(35, y, z, 39, y, z + 3, "glass")
    # roof edge beam along the track side hangs 1 lower so the roof reads as a canopy
    w.fill(34, y - 1, z0, 34, y - 1, z1, "gray_concrete")


def vending(w, x, y, z, facing, body="red_concrete", wide=2):
    """Drinks machine: `wide` blocks wide, 2 high, its front toward `facing`. (x, z) is the left-most cell seen from the front."""
    f = DIRS[facing]
    r = DIRS[RIGHT[facing]]
    for i in range(wide):
        bx, bz = x + r[0] * i, z + r[1] * i
        w.set(bx, y, bz, body)
        if i == 0:
            w.set(bx, y + 1, bz, "light_blue_stained_glass")           # the display of cans
        elif i == wide - 1 and wide > 1:
            w.set(bx, y + 1, bz, "white_concrete")                      # coin panel
        else:
            w.set(bx, y + 1, bz, body)
    # a dark delivery slot in front of the bottom row, set into the body
    w.set(x + r[0] * (wide - 1), y, z + r[1] * (wide - 1), "black_concrete")


def hall(S):
    """The station hall between the platform and the forecourt. Two openings on the centre line, ticket gates inside."""
    w, rng = S.w, S.rng
    x0, x1, z0, z1 = STN
    S.keep[x0 - 2:x1 + 3, z0 - 2:z1 + 3] = True
    S.occ[x0 - 2:x1 + 3, z0 - 2:z1 + 3] = True
    fy = PLAT_TOP                       # floor row
    top = fy + 6                        # roof row
    # floor: a dark chequer that contrasts with the pale walls and the pale platform, with a bright yellow guide path from the platform
    # door to the exit and white joint lines
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            if abs(z - CL) <= 1:
                b = "yellow_concrete"
            elif abs(z - CL) == 2:
                b = "white_concrete"
            elif ((x // 2) + (z // 2)) % 2 == 0:
                b = "gray_concrete"
            else:
                b = "polished_blackstone"
            w.set(x, fy, z, b)
    # walls
    w.fill(x0, fy + 1, z0, x1, top - 1, z0, "white_concrete")
    w.fill(x0, fy + 1, z1, x1, top - 1, z1, "white_concrete")
    w.fill(x0, fy + 1, z0, x0, top - 1, z1, "white_concrete")
    w.fill(x1, fy + 1, z0, x1, top - 1, z1, "white_concrete")
    w.fill(x0, fy + 1, z0, x1, fy + 1, z0, "light_gray_concrete")
    w.fill(x0, fy + 1, z1, x1, fy + 1, z1, "light_gray_concrete")
    w.fill(x0, fy + 1, z0, x0, fy + 1, z1, "light_gray_concrete")
    w.fill(x1, fy + 1, z0, x1, fy + 1, z1, "light_gray_concrete")
    # windows (tall, 3 rows) on all four sides
    for z in range(z0 + 2, z1 - 1):
        if (z - z0) % 4 in (0, 1, 2):
            for x in (x0, x1):
                if abs(z - CL) > 4:
                    for y in range(fy + 2, fy + 5):
                        w.set(x, y, z, pane("z"))
    for x in range(x0 + 2, x1 - 1, 4):
        for z in (z0, z1):
            for y in range(fy + 2, fy + 5):
                for dx in range(3):
                    w.set(x + dx, y, z, pane("x"))
    # the two openings on the centre line
    for x in (x0, x1):
        w.fill(x, fy + 1, CL - 4, x, fy + 5, CL + 4, "air")
    # flat roof with parapet, blue fascia
    w.fill(x0 - 1, top, z0 - 1, x1 + 1, top, z1 + 1, "light_gray_concrete")
    w.fill(x0 - 1, top + 1, z0 - 1, x1 + 1, top + 1, z0 - 1, "white_concrete")
    w.fill(x0 - 1, top + 1, z1 + 1, x1 + 1, top + 1, z1 + 1, "white_concrete")
    w.fill(x0 - 1, top + 1, z0 - 1, x0 - 1, top + 1, z1 + 1, "white_concrete")
    w.fill(x1 + 1, top + 1, z0 - 1, x1 + 1, top + 1, z1 + 1, "white_concrete")
    w.fill(x0 - 1, top - 1, z0 - 1, x1 + 1, top - 1, z0 - 1, "blue_concrete")
    w.fill(x0 - 1, top - 1, z1 + 1, x1 + 1, top - 1, z1 + 1, "blue_concrete")
    # roof clutter: air handlers, antenna
    for ax in (46, 50):
        w.fill(ax, top + 1, 118, ax + 1, top + 2, 119, "light_gray_concrete")
        w.fill(ax, top + 3, 118, ax + 1, top + 3, 119, "gray_concrete")
    w.fill(48, top + 1, 136, 48, top + 7, 136, "iron_bars")
    w.fill(52, top + 1, 138, 52, top + 2, 138, "iron_bars")
    # lights in the hall ceiling
    for x in (45, 50):
        for z in range(z0 + 5, z1, 6):
            w.set(x, top - 1, z, "sea_lantern")
    # ticket gates across the hall: a waist-high partition with three passages (centre 3 wide, two 2 wide) and a blue
    # reader post at the end of each run of barrier
    gx = 47
    passages = set(range(CL - 1, CL + 2)) | {CL - 6, CL - 5, CL + 5, CL + 6}
    for z in range(z0 + 1, z1):
        if z in passages:
            continue
        w.set(gx, fy + 1, z, "light_gray_concrete")
        w.set(gx, fy + 2, z, "iron_bars")
        if (z + 1 in passages) or (z - 1 in passages):
            w.set(gx, fy + 2, z, "blue_concrete")
            w.set(gx, fy + 1, z, "white_concrete")
    # ticket machines along the south wall, a closed kiosk at the north end
    for x in (44, 46, 48, 50):
        w.set(x, fy + 1, z1 - 1, "blue_concrete")
        w.set(x, fy + 2, z1 - 1, "light_blue_stained_glass")
        w.set(x, fy + 3, z1 - 1, "blue_concrete")
    w.fill(44, fy + 1, z0 + 1, 51, fy + 1, z0 + 2, "birch_planks")
    w.fill(44, fy + 2, z0 + 1, 51, fy + 4, z0 + 1, "air")
    for x in range(44, 52):
        w.set(x, fy + 2, z0 + 2, bs("iron_trapdoor", facing="north", half="bottom", open=True))
        w.set(x, fy + 3, z0 + 2, bs("iron_trapdoor", facing="north", half="bottom", open=True))
    w.fill(44, fy + 4, z0 + 2, 51, fy + 4, z0 + 2, "red_concrete")
    # benches in the hall
    for z in (z0 + 8, z1 - 9):
        for x in (52,):
            for i in range(4):
                slab(w, x, fy + 1, z + i, "birch")
    # the station sign over the east opening, and the name boards
    w.fill(54, top - 2, CL - 8, 54, top - 1, CL + 8, "blue_concrete")
    w.fill(54, top - 3, CL - 8, 54, top - 3, CL + 8, "white_concrete")
    place_wall_sign(w, 55, top - 2, CL - 2, "east", [jp("潮見駅"), "SHIOMI STATION", "", ""], "birch")
    place_wall_sign(w, 55, top - 2, CL + 2, "east", [jp("潮見駅"), "SHIOMI STATION", "", ""], "birch")
    # porch roof over the east exit on two posts
    w.fill(54, top - 1, CL - 7, 58, top - 1, CL + 7, "light_gray_concrete")
    for z in (CL - 7, CL + 7):
        for y in range(fy + 1, top - 1):
            w.set(58, y, z, "andesite_wall")
    # --- the bright doorway: the east exit is framed in light (lit jambs, a lit porch roof, a white-and-yellow threshold), so the eye is
    # drawn along the yellow guide path to the glowing opening
    for z in (CL - 5, CL + 5):
        for y in range(fy + 1, top):
            w.set(x1, y, z, "sea_lantern")
        for y in range(fy + 1, top - 3):
            w.set(x1 + 1, y, z, "white_concrete")
    for z in range(CL - 4, CL + 5):
        w.set(x1, fy, z, "white_concrete")
        w.set(x1 + 1, fy, z, "yellow_concrete")
    for z in (CL - 6, CL, CL + 6):
        for x in range(54, 59):
            w.set(x, top - 1, z, "sea_lantern")
    # lit ceiling in the hall too: lamp rows along the guide path
    for x in range(x0 + 2, x1 - 1, 2):
        for z in (CL - 3, CL + 3):
            w.set(x, top - 1, z, "sea_lantern")
    # --- the ticket-gate line reads from far off: an overhead board across the gates, with its name on both faces, and a green
    # "go" light on every reader post
    for z in range(z0 + 1, z1):
        for y in (fy + 4, fy + 5):
            w.set(gx, y, z, "blue_concrete" if y == fy + 4 else "white_concrete")
    w.fill(gx, fy + 4, CL - 1, gx, fy + 5, CL + 1, "black_concrete")
    place_wall_sign(w, gx + 1, fy + 4, CL, "east", [jp("改札口"), "TICKET GATES", "", ""], "birch")
    place_wall_sign(w, gx - 1, fy + 4, CL, "west", [jp("改札口"), "TICKET GATES", "", ""], "birch")
    for z in range(z0 + 1, z1):
        if (z + 1 in passages) != (z - 1 in passages) and z not in passages:
            w.set(gx, fy + 3, z, "lime_concrete")
    # --- a timetable board on the pier left of the platform door: white sheet, blue frame, rows of departures struck through in red
    for z in range(113, 120):
        for y in range(fy + 1, fy + 5):
            w.set(41, y, z, "blue_concrete" if (z in (113, 119) or y in (fy + 1, fy + 4)) else ("white_concrete" if (z + y) % 3 else "light_blue_concrete"))
    for z in range(114, 119):
        w.set(41, fy + 3, z, "red_concrete")
    place_wall_sign(w, 40, fy + 2, 116, "west", [jp("時刻表"), "TIMETABLE", "ALL SERVICES", "SUSPENDED"], "birch")


def train(S):
    """Two-car commuter train standing on track A, doors shut, interior furnished, pantographs up."""
    w = S.w
    X0, X1 = 26, 30
    cars = [(96, 116), (119, 139)]
    floor, roof = PLAT_TOP, PLAT_TOP + 4
    doors = {0: (100, 111), 1: (123, 134)}
    for ci, (za, zb) in enumerate(cars):
        # underframe, bogies, wheels on the rails
        w.fill(27, floor - 1, za + 1, 29, floor - 1, zb - 1, "gray_concrete")
        for bz in (za + 3, zb - 5):
            for z in range(bz, bz + 3):
                w.set(27, floor - 1, z, "black_concrete")
                w.set(29, floor - 1, z, "black_concrete")
                w.set(28, floor - 1, z, "black_concrete")
        w.fill(X0, floor, za, X1, floor, zb, "gray_concrete")
        # shell: sides, ends, roof
        for z in range(za, zb + 1):
            for x in (X0, X1):
                w.set(x, floor + 1, z, "blue_concrete")                 # blue waist stripe
                w.set(x, floor + 2, z, "light_blue_stained_glass")      # windows at eye level from the platform
                w.set(x, floor + 3, z, "white_concrete")
        for x in range(X0, X1 + 1):
            for z in (za, zb):
                for y in range(floor + 1, floor + 4):
                    w.set(x, y, z, "white_concrete")
        w.fill(X0, roof, za, X1, roof, zb, "light_gray_concrete")
        w.fill(X0 + 1, roof + 1, za + 1, X1 - 1, roof + 1, zb - 1, "smooth_stone_slab")
        w.fill(X0 + 1, floor + 1, za + 1, X1 - 1, floor + 3, zb - 1, "air")
        # window pillars every fourth cell
        for z in range(za, zb + 1):
            if (z - za) % 4 == 3:
                for x in (X0, X1):
                    w.set(x, floor + 2, z, "white_concrete")
        # doors (double leaf, 2 high) on both sides
        for dz in doors[ci]:
            for x, face in ((X1, "west"), (X0, "east")):
                for k, hinge in ((0, "left"), (1, "right")):
                    w.set(x, floor + 1, dz + k, bs("iron_door", facing=face, half="lower", hinge=hinge, open=False, powered=False))
                    w.set(x, floor + 2, dz + k, bs("iron_door", facing=face, half="upper", hinge=hinge, open=False, powered=False))
        # seats along both walls between the doors, ceiling lights
        for z in range(za + 2, zb - 1):
            if any(dd - 1 <= z <= dd + 2 for dd in doors[ci]):
                continue
            for x in (X0 + 1, X1 - 1):
                slab(w, x, floor + 1, z, "dark_prismarine")
        for z in range(za + 2, zb - 1, 4):
            w.set(28, roof, z, "sea_lantern")
        # pantograph
        pz = za + 8
        w.fill(27, roof + 2, pz, 29, roof + 2, pz, "iron_bars[east=true,west=true]")
        w.set(27, roof + 2, pz + 1, "iron_bars"); w.set(29, roof + 2, pz + 1, "iron_bars")
        w.set(28, roof + 2, pz - 1, "light_gray_concrete")
    # the gangway between the cars
    w.fill(27, floor + 1, 117, 29, floor + 3, 118, "black_concrete")
    w.fill(28, floor + 1, 117, 28, floor + 2, 118, "air")
    w.fill(X0, floor + 3, 117, X1, roof, 118, "gray_concrete")
    w.fill(X0, floor, 117, X1, floor, 118, "gray_concrete")
    # cab ends: windscreen and lamps at the far ends
    for z, step in ((96, 0), (139, 0)):
        for x in (27, 28, 29):
            w.set(x, floor + 2, z, "light_blue_stained_glass")
            w.set(x, floor + 3, z, "light_blue_stained_glass")
            w.set(x, floor + 1, z, "blue_concrete")
        w.set(26, floor + 1, z, "yellow_concrete")
        w.set(30, floor + 1, z, "red_concrete")


def catenary(S):
    """Overhead line: concrete masts between the tracks every 20 blocks with swivel arms, one contact wire per track."""
    w = S.w
    for z in range(54, 205, 20):
        for y in range(30, 42):
            w.set(23, y, z, "andesite_wall")
        w.set(23, 41, z, "light_gray_concrete")
        for x in range(18, 29):
            if x != 23:
                w.set(x, 40, z, "iron_bars[east=true,west=true]")
        w.set(28, 39, z, "iron_chain[axis=y]")                         # hanger to the wire
        w.set(18, 39, z, "iron_chain[axis=y]")
    for x in (28, 18):
        for z in range(44, 211):
            w.set(x, 39, z, "iron_chain[axis=z]")
    # upper support wire with a gentle sag between masts
    for x in (28, 18):
        for z0 in range(54, 195, 20):
            chain_line(w, x, 41, z0, x, 41, z0 + 20, sag=1.0)


def platform_furniture(S):
    w, rng = S.w, S.rng
    y = PLAT_TOP + 1
    vending(w, 38, y, 76, "west", "red_concrete")
    vending(w, 40, y, 168, "west", "blue_concrete")
    # benches facing the track (back to the east), under the canopy
    for z in (102, 112, 144, 156):
        for i in range(4):
            slab(w, 38, y, z + i, "birch")
            w.set(39, y, z + i, bs("birch_trapdoor", facing="west", half="bottom", open=True))
    # name boards on posts: blue board, white lower edge
    for z in (84, 112, 144, 176):
        for yy in range(y, y + 4):
            w.set(36, yy, z, "andesite_wall")
        w.fill(36, y + 3, z - 3, 36, y + 4, z + 3, "blue_concrete")
        w.fill(35, y + 3, z - 3, 35, y + 4, z + 3, "blue_concrete")
        place_wall_sign(w, 37, y + 3, z, "east", [jp("潮見"), "SHIOMI", "", ""], "birch")
        place_wall_sign(w, 34, y + 3, z, "west", [jp("潮見"), "SHIOMI", "", ""], "birch")
    # litter bins and a timetable board by the hall opening
    for z in (122, 134):
        w.set(41, y, z, "gray_concrete")
        w.set(41, y + 1, z, "iron_trapdoor[facing=north,half=bottom,open=false]")
    # posters on the hall wall facing the platform: a white sheet with a red band, and a blue timetable board
    for z in (116, 139):
        w.fill(42, y + 1, z, 42, y + 2, z + 1, "white_concrete")
        w.fill(42, y + 2, z, 42, y + 2, z + 1, "red_concrete")
    w.fill(42, y + 1, 121, 42, y + 2, 122, "blue_concrete")
    place_wall_sign(w, 41, y + 2, 120, "west", [jp("避難命令"), "ALL TRAINS", "SUSPENDED", ""], "birch")


# --------------------------------------------------------------------------------------------- the town: ground
ROAD = "polished_blackstone"
ROAD_SLAB = "polished_blackstone_slab"
MAIN_X0, MAIN_X1 = 92, 184          # the main street runs from the forecourt to the sea wall
ROAD_Z = (123, 133)                 # carriageway, centre z = 128
WALK_N = (119, 122)                 # pavements
WALK_S = (134, 137)
FRONT_N, FRONT_S = 118, 138         # building fronts: last row north of the street / first row south of it
CROSS_X = (112, 120)                # the cross street (north and south arms)
HILL_X = (144, 152)                 # the side street that becomes the hill road
FORE = (54, 91, 98, 158)            # the forecourt x0, x1, z0, z1


def paving(w, x0, z0, x1, z1, base="stone", top="smooth_stone", var=None, rng=None):
    """A raised pavement (bottom slab on a base block). `var` is a list of (block, chance) for worn / mixed slabs."""
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            w.set(x, GY - 1, z, base)
            b = top
            if var and rng is not None:
                r = rng.random()
                for vb, ch in var:
                    if r < ch:
                        b = vb
                        break
                    r -= ch
            slab(w, x, GY, z, b)


def road_paint(S):
    """Carriageways, pavements, markings and the forecourt paving. All at the natural ground, so stands are y = 32."""
    w, rng = S.w, S.rng
    y = GY - 1
    # main street and arms
    w.fill(MAIN_X0, y, ROAD_Z[0], MAIN_X1, y, ROAD_Z[1], ROAD)
    w.fill(CROSS_X[0], y, 96, CROSS_X[1], y, ROAD_Z[0], ROAD)
    w.fill(CROSS_X[0], y, ROAD_Z[1], CROSS_X[1], y, 190, ROAD)
    w.fill(HILL_X[0], y, 106, HILL_X[1], y, ROAD_Z[0], ROAD)
    # pavements: north, south, and along the arms
    wmix = [("polished_diorite", 0.10), ("polished_andesite", 0.12), ("andesite", 0.04)]
    paving(w, MAIN_X0, WALK_N[0], CROSS_X[0] - 5, WALK_N[1], var=wmix, rng=rng)
    paving(w, CROSS_X[1] + 5, WALK_N[0], HILL_X[0] - 5, WALK_N[1], var=wmix, rng=rng)
    paving(w, HILL_X[1] + 5, WALK_N[0], MAIN_X1 - 12, WALK_N[1], var=wmix, rng=rng)
    paving(w, MAIN_X0, WALK_S[0], CROSS_X[0] - 5, WALK_S[1], var=wmix, rng=rng)
    paving(w, CROSS_X[1] + 5, WALK_S[0], MAIN_X1 - 12, WALK_S[1], var=wmix, rng=rng)
    # pavement strips along the cross street and the hill street
    for zz0, zz1 in ((100, 118),):
        paving(w, CROSS_X[0] - 4, zz0, CROSS_X[0] - 1, zz1 + 1, var=wmix, rng=rng)
        paving(w, CROSS_X[1] + 1, zz0, CROSS_X[1] + 4, zz1 + 1, var=wmix, rng=rng)
        paving(w, HILL_X[0] - 4, zz0 + 6, HILL_X[0] - 1, zz1 + 1, var=wmix, rng=rng)
        paving(w, HILL_X[1] + 1, zz0 + 6, HILL_X[1] + 4, zz1 + 1, var=wmix, rng=rng)
    for zz0, zz1 in ((139, 188),):
        paving(w, CROSS_X[0] - 4, zz0 - 2, CROSS_X[0] - 1, zz1, var=wmix, rng=rng)
        paving(w, CROSS_X[1] + 1, zz0 - 2, CROSS_X[1] + 4, zz1, var=wmix, rng=rng)
    # the forecourt: slab paving with a paler walking line on the centre line and a grid of joints
    x0, x1, z0, z1 = FORE
    for x in range(x0, x1 + 1):
        for z in range(z0, z1 + 1):
            w.set(x, y, z, "stone")
            if abs(z - CL) <= 2:
                b = "polished_diorite"
            elif (x % 8 == 0) or (z % 8 == 0):
                b = "polished_andesite"
            else:
                b = "smooth_stone" if rng.random() < 0.9 else "andesite"
            slab(w, x, GY, z, b)
    # the plaza flows into the main street; the carriageway starts at the plaza edge
    w.fill(FORE[1] + 1, y, ROAD_Z[0], FORE[1] + 1, y, ROAD_Z[1], ROAD)
    # --- markings (flush with the road)
    for x in range(MAIN_X0 + 2, MAIN_X1 - 6):
        if x % 8 < 4 and not (CROSS_X[0] - 1 <= x <= CROSS_X[1] + 1) and not (HILL_X[0] - 1 <= x <= HILL_X[1] + 1):
            w.set(x, y, 128, "white_concrete")
        w.set(x, y, ROAD_Z[0], "white_concrete") if (x % 2 == 0 and not (CROSS_X[0] <= x <= CROSS_X[1]) and not (HILL_X[0] <= x <= HILL_X[1])) else None
        w.set(x, y, ROAD_Z[1], "white_concrete") if (x % 2 == 0 and not (CROSS_X[0] <= x <= CROSS_X[1])) else None
    for x in range(95, 100):                                        # zebra crossing just beyond the forecourt
        for z in range(ROAD_Z[0] + 1, ROAD_Z[1]):
            if z % 2 == 0:
                w.set(x, y, z, "white_concrete")
    for z in list(range(113, 119)) + list(range(138, 144)):         # crossings over the cross street arms
        for x in range(CROSS_X[0] + 1, CROSS_X[1]):
            if x % 2 == 0 and not (115 < z < 140):
                w.set(x, y, z, "white_concrete")
    for z in range(112, 118):                                       # ... and over the hill street
        for x in range(HILL_X[0] + 1, HILL_X[1]):
            if x % 2 == 0:
                w.set(x, y, z, "white_concrete")
    # road edge: bay ending at a sea wall, with a gap for the angel corridor kept clear later
    for x in range(MAIN_X1 - 12, MAIN_X1 + 1):
        S.keep[x, 119:138] = True
    S.road[MAIN_X0:MAIN_X1 + 1, ROAD_Z[0]:ROAD_Z[1] + 1] = True
    S.keep[FORE[0]:FORE[1] + 1, FORE[2]:FORE[3] + 1] = True
    S.keep[MAIN_X0:MAIN_X1 + 1, 117:140] = True
    S.keep[CROSS_X[0] - 5:CROSS_X[1] + 6, 96:192] = True
    S.keep[HILL_X[0] - 5:HILL_X[1] + 6, 100:128] = True


# --------------------------------------------------------------------------------------------- hill road, lookout, tunnel
def surface_y(S, x, z):
    """Feet height standing on the cell (x, z), counting a road slab."""
    t = int(S.T[x, z])
    return t + 1 + (0.5 if S.slab_y[x, z] >= 0 else 0.0) if S.hill_road[x, z] else t + 1


def hill_road(S):
    w, T = S.w, S.T
    dist = S.road_dist
    gx, gz = np.gradient(dist)
    n = np.hypot(gx, gz) + 1e-9
    for x, z in zip(*np.nonzero(S.hill_road)):
        t = int(T[x, z])
        w.set(x, t, z, ROAD)
        if S.slab_y[x, z] >= 0:
            slab(w, x, int(S.slab_y[x, z]), z, "polished_blackstone")
        S.keep[max(0, x - 7):x + 8, max(0, z - 7):z + 8] = True
    for x, z in zip(*np.nonzero(S.shoulder)):
        t = int(T[x, z])
        w.set(x, t, z, "gravel" if (x * 7 + z * 3) % 5 else "coarse_dirt")
        # guard rail where the ground falls away outside the shoulder
        sx = int(round(x + 3.2 * gx[x, z] / n[x, z]))
        sz = int(round(z + 3.2 * gz[x, z] / n[x, z]))
        if 0 <= sx < N and 0 <= sz < N and T[sx, sz] <= t - 2 and dist[x, z] > 4.0 and z < 104 and not (170 < x < 218 and z < 84):
            w.set(x, t + 1, z, "iron_bars")
    # a few white road-edge markers on the surface (every ~6 blocks of path) so the line of the road reads from the town
    A = S.road_path
    for i in range(0, len(A), 9):
        px, pz = int(round(A[i][0])), int(round(A[i][1]))
        if S.hill_road[px, pz] and S.slab_y[px, pz] < 0 and pz < 119:
            w.set(px, int(T[px, pz]), pz, "white_concrete")


def lookout(S):
    """The ridge bench: gravel parking, low wall on the sea side, a viewing scope, a bench, a map board and a vending machine,
    all kept to the north and west verges, clear of the carriageway across the bench and of the car's swept path, so the
    south-east view back to the sea gap stays open."""
    w, T = S.w, S.T
    cx, cz, rx, rz = PLATEAU
    for x in range(cx - rx - 3, cx + rx + 4):
        for z in range(cz - rz - 3, cz + rz + 4):
            d = math.hypot((x - cx) / rx, (z - cz) / rz)
            if d < 0.92 and not S.hill_road[x, z]:
                t = int(T[x, z])
                w.set(x, t, z, "light_gray_concrete" if (x * 3 + z) % 9 else "gravel")
    # low wall on the south-east rim of the bench (knee height), with a wide gap in front of the anchors
    for x in range(cx - rx, cx + rx + 1):
        for z in range(cz - rz, cz + rz + 1):
            d = math.hypot((x - cx) / rx, (z - cz) / rz)
            if 0.88 <= d < 0.97 and z > cz + 2 and x > cx - 14 and not S.hill_road[x, z]:
                if abs(x - RIDGE[0]) > 17:                       # nothing at all in front of the car: only a knee-high kerb further off
                    slab(w, x, int(T[x, z]) + 1, z, "stone_brick")
    # furniture on the verge. The road leaves the bench at its west end (it runs on through x 186..172, z 52..48 and down the
    # hill), so the bench and the map board stand on the north rim, z 45..46, well clear of the carriageway and of the car's
    # swept path (the north rim is also away from the south-east view to the sea)
    y = RIDGE_Y
    for i in range(3):
        slab(w, 184 + i, y, 46, "birch")
        w.set(184 + i, y, 45, bs("birch_trapdoor", facing="south", half="bottom", open=True))
    vending(w, 171, int(T[170:172, 58].max()) + 1, 58, "south", "blue_concrete")      # (on the ground there: the road cut dishes the bench's west end)
    # viewing scope on a post
    for yy in range(y, y + 2):
        w.set(180, yy, 62, "andesite_wall")
    w.set(180, y + 2, 62, "iron_block")
    w.set(181, y + 2, 62, "iron_bars")
    # map board
    w.fill(189, y, 45, 191, y + 1, 45, "white_concrete")
    place_wall_sign(w, 190, y + 1, 46, "south", [jp("展望台"), "LOOKOUT", "", ""], "birch")


def tunnel(S):
    """Retaining cut in the hillside, concrete portal wall with an open hazard-striped blast gate, and the hall behind it
    with a rail platform for the car-carrying train. Local frame: the hall runs along x inside the hill, the platform is
    its south side (z 11..20), the track trough is z 5..10, and the passage from the gate comes in from the south."""
    w, T = S.w, S.T
    FY = HOLLOW_Y - 1                    # top block of the forecourt and of the platform (feet at FY + 1 = 44)
    PX0, PX1, PZ = 176, 206, 22          # portal wall: x range, z of the wall face
    GX0, GX1 = 183, 197                  # the opening through the wall
    # --- level the forecourt in front of the portal (the natural hollow is only roughly flat) and pave it
    # (to z 38: the car turns through here and its swept box reaches z 38.5)
    for x in range(PX0, PX1 + 1):
        for z in range(PZ + 1, 39):
            w.fill(x, FY + 1, z, x, 90, z, "air")
            w.fill(x, FY - 3, z, x, FY - 1, z, "stone")
            w.set(x, FY, z, "light_gray_concrete" if z < 34 else "gray_concrete")
    # --- concrete wall face (with shuttering lines) and wing walls up to the natural ground
    for x in range(PX0, PX1 + 1):
        top = max(int(T[x, PZ - 1]) + 1, FY + 14)
        w.fill(x, FY, PZ, x, top, PZ, "light_gray_concrete")
        for y in range(FY + 4, top, 4):
            w.set(x, y, PZ, "gray_concrete")
        w.set(x, FY + 13, PZ, "white_concrete")
        w.fill(x, FY, PZ + 1, x, FY, PZ + 3, "light_gray_concrete")      # apron step
    for z in range(PZ, 37):
        for x in (PX0, PX1):
            top = int(T[x, z])
            w.fill(x, FY, z, x, max(FY, top), z, "light_gray_concrete")
    # --- the hall: shell, then carve
    HX0, HX1, HZ0, HZ1 = 164, 218, 2, 20
    top_y = FY + 14                                                    # underside of the hall roof
    low = int(T[HX0:HX1 + 1, HZ0:HZ1 + 3].min())
    S.notes.append("hall roof %d, lowest ground over it %d" % (top_y + 1, low))
    w.fill(HX0 - 1, FY - 3, HZ0 - 1, HX1 + 1, top_y + 1, HZ1 + 2, "light_gray_concrete")
    w.fill(HX0, FY, HZ0, HX1, top_y, HZ1, "air")
    # lower wall dark, upper wall pale: panelled
    w.fill(HX0, FY, HZ0 - 1, HX1, FY + 3, HZ0 - 1, "gray_concrete")
    w.fill(HX0, FY, HZ1 + 1, HX1, FY + 3, HZ1 + 1, "gray_concrete")
    # track trough along x at z = 5..10, platform z 11..20 at FY
    w.fill(HX0, FY - 3, HZ0, HX1, FY - 1, HZ1, "gray_concrete")
    w.fill(HX0, FY - 2, 5, HX1, FY - 2, 10, "gravel")
    for x in range(HX0, HX1 + 1):
        w.set(x, FY - 1, 6, bs("rail", shape="east_west"))
        w.set(x, FY - 1, 9, bs("rail", shape="east_west"))
        w.fill(x, FY - 1, 5, x, FY - 1, 5, "gray_concrete")
        w.fill(x, FY - 1, 10, x, FY - 1, 10, "gray_concrete")
        for z in range(11, HZ1 + 1):
            if z == 11:
                b = "yellow_concrete" if (x // 2) % 2 == 0 else "black_concrete"     # hazard lip
            else:
                b = "light_gray_concrete" if (x + z) % 7 else "smooth_stone"
            w.set(x, FY, z, b)
        w.fill(x, FY - 1, 11, x, FY - 1, HZ1, "gray_concrete")
    # columns with hazard feet, ceiling light rows, ceiling pipes
    for x in range(HX0 + 4, HX1, 10):
        w.fill(x, FY + 1, 15, x, top_y - 1, 15, "white_concrete")
        for y in range(FY + 1, FY + 4):
            w.set(x, y, 15, "yellow_concrete" if y % 2 else "black_concrete")
    for x in range(HX0 + 2, HX1, 5):
        for z in (7, 15):
            w.set(x, top_y, z, "sea_lantern")
    w.fill(HX0, top_y - 1, 3, HX1, top_y - 1, 3, "iron_block")
    w.fill(HX0, top_y - 1, 18, HX1, top_y - 1, 18, "iron_block")
    # the tunnels the train comes and goes by, dark
    for x in (HX0 - 1, HX1 + 1):
        w.fill(x, FY, 4, x, FY + 8, 10, "black_concrete")
    # destination boards on the hall wall, either side of the passage, and numbers on the platform edge
    for x in (178, 202):
        w.fill(x - 3, FY + 6, 21, x + 3, FY + 8, 21, "blue_concrete")
        place_wall_sign(w, x, FY + 7, 20, "north", [jp("カートレイン"), "CAR TRAIN", "PLATFORM 1", ""], "birch")
    # --- the passage through the wall into the hall, 15 wide x 10 high, with a white frame. The floor (row FY) stays: it is the
    # platform's own paving for z 12..20 and the wall's footing at z 21..22, so a car rolls from the forecourt onto the platform level
    w.fill(GX0, FY + 1, 12, GX1, FY + 9, PZ, "air")
    w.fill(GX0 - 1, FY, 12, GX0 - 1, FY + 10, PZ, "white_concrete")
    w.fill(GX1 + 1, FY, 12, GX1 + 1, FY + 10, PZ, "white_concrete")
    w.fill(GX0 - 1, FY + 10, 12, GX1 + 1, FY + 10, PZ, "white_concrete")
    w.fill(GX0 - 1, FY + 11, PZ, GX1 + 1, FY + 11, PZ + 1, "yellow_concrete")
    # --- the blast gate: two leaves standing open on the wall face either side of the opening, hazard-striped
    for x in list(range(PX0 + 1, GX0 - 1)) + list(range(GX1 + 2, PX1)):
        for y in range(FY, FY + 11):
            w.set(x, y, PZ + 1, "yellow_concrete" if (x + y) % 4 < 2 else "black_concrete")
            edge = y in (FY, FY + 10) or x in (PX0 + 1, PX1 - 1, GX0 - 2, GX1 + 2)
            w.set(x, y, PZ + 2, "iron_block" if edge else "gray_concrete")
    for x in range(PX0, PX1 + 1):                                      # the gate's track above the leaves
        if x < GX0 - 1 or x > GX1 + 1:
            w.set(x, FY + 11, PZ + 2, "iron_block")
            w.set(x, FY + 12, PZ + 2, "iron_block")
    # floor markings in front of the gate, bollards and lamp posts
    for x in range(GX0, GX1 + 1):
        w.set(x, FY, PZ + 4, "yellow_concrete" if x % 2 == 0 else "black_concrete")
        w.set(x, FY, PZ + 5, "yellow_concrete" if x % 2 == 1 else "black_concrete")
    for x in (GX0 - 3, GX1 + 3):
        w.fill(x, FY + 1, PZ + 7, x, FY + 2, PZ + 7, "yellow_concrete")
    for x in (PX0 + 2, PX1 - 2):
        for dy in range(1, 9):
            w.set(x, FY + dy, 30, "andesite_wall")
        w.set(x, FY + 9, 30, "sea_lantern")
    place_wall_sign(w, 190, FY + 12, PZ + 1, "south", ["NO ENTRY", jp("立入禁止"), "", ""], "birch")
    S.keep[PX0 - 8:PX1 + 9, 14:60] = True


def hall_lighting(S):
    """The car-train hall inside the hill: it used to be a black box (the only lamps sat on the 14-high ceiling, out of reach of their own
    light).  Now: visible industrial lamps low on the walls and hung from chains, hidden light blocks at working height, hazard striping,
    wall panels, sleepers under the rails, a control booth, and lamps in the gate passage with the hall behind it left darker."""
    w = S.w
    FY = HOLLOW_Y - 1
    HX0, HX1, HZ0, HZ1 = 164, 218, 2, 20
    top_y = FY + 14
    GX0, GX1 = 183, 197
    # --- wall panels and hazard skirting on both long walls (north wall z = 1, south wall z = 21 either side of the passage)
    for x in range(HX0, HX1 + 1):
        for z, face in ((HZ0 - 1, "south"), (HZ1 + 1, "north")):
            if z == HZ1 + 1 and GX0 - 1 <= x <= GX1 + 1:
                continue
            seam = (x - HX0) % 6 == 0
            panel = "light_gray_concrete" if ((x - HX0) // 6) % 2 == 0 else "gray_concrete"
            for y in range(FY + 1, top_y - 2):
                w.set(x, y, z, "iron_block" if seam else panel)
            w.set(x, FY + 6, z, "blue_concrete")                                     # the stripe
            w.set(x, FY + 1, z, "yellow_concrete" if (x // 2) % 2 == 0 else "black_concrete")
            w.set(x, FY + 2, z, "yellow_concrete" if (x // 2) % 2 == 1 else "black_concrete")
    # --- lamps: sea lanterns let into the walls at two heights, and lamps hung on chains over the platform and the track
    for x in range(HX0 + 4, HX1 - 2, 6):
        for z in (HZ0 - 1, HZ1 + 1):
            if z == HZ1 + 1 and GX0 - 3 <= x <= GX1 + 3:
                continue
            for y in (FY + 4, FY + 9):
                w.set(x, y, z, "sea_lantern")
                w.set(x + 1, y, z, "sea_lantern")
    for x in range(HX0 + 9, HX1 - 4, 10):
        for z in (7, 16):
            for y in range(top_y - 5, top_y + 1):
                w.set(x, y, z, "iron_chain[axis=y]")
            w.fill(x - 1, top_y - 7, z, x + 1, top_y - 6, z, "sea_lantern")
    # hidden light at working height, a lamp every 6 blocks over the platform and the track (level 14: the hall is lit, not flooded)
    for x in range(HX0 + 2, HX1, 6):
        for z in (4, 8, 12, 16, 19):
            if w.a[x, top_y - 6, z] <= 1:
                w.set(x, top_y - 6, z, "light[level=14]")
        for z in (6, 14):
            if w.a[x, FY + 3, z] <= 1:
                w.set(x, FY + 3, z, "light[level=13]")
    # --- sleepers under the rails
    for x in range(HX0, HX1 + 1, 2):
        w.fill(x, FY - 2, 5, x, FY - 2, 10, "dark_oak_planks")
    # --- column bases keep their hazard feet; add head bands
    for x in range(HX0 + 4, HX1, 10):
        for y in (top_y - 3, top_y - 2):
            w.set(x, y, 15, "yellow_concrete" if y % 2 else "black_concrete")
    # --- the control booth on the platform's west end (clear of the car's way: the car drives x 187..195)
    bx0, bx1, bz0, bz1 = 168, 175, 13, 19
    w.fill(bx0, FY + 1, bz0, bx1, FY + 5, bz1, "light_gray_concrete")
    w.fill(bx0 + 1, FY + 1, bz0 + 1, bx1 - 1, FY + 4, bz1 - 1, "air")
    w.fill(bx0 - 1, FY + 6, bz0 - 1, bx1 + 1, FY + 6, bz1 + 1, "gray_concrete")      # roof with an overhang
    w.fill(bx0, FY + 1, bz0, bx1, FY + 1, bz0, "yellow_concrete")
    for x in range(bx0 + 1, bx1):                                                    # the window band toward the track (north face)
        for y in (FY + 2, FY + 3):
            w.set(x, y, bz0, pane("x"))
    for z in range(bz0 + 1, bz1):
        for y in (FY + 2, FY + 3):
            w.set(bx1, y, z, pane("z"))
    w.fill(bx0 + 2, FY + 1, bz1 - 0, bx0 + 3, FY + 2, bz1, "air")                      # the door, south side
    w.fill(bx0 + 1, FY + 1, bz0 + 1, bx1 - 1, FY + 1, bz0 + 2, "black_concrete")     # the console under the window
    for x in range(bx0 + 2, bx1 - 1):
        w.set(x, FY + 2, bz0 + 1, ["lime_concrete", "red_concrete", "yellow_concrete", "light_blue_concrete"][x % 4])
    w.fill(bx0 + 2, FY + 4, bz0 + 2, bx1 - 2, FY + 4, bz1 - 2, "sea_lantern")        # ceiling light inside
    w.fill(bx0, FY + 5, bz0, bx1, FY + 5, bz0, "blue_concrete")
    place_wall_sign(w, bx0 + 3, FY + 5, bz0 - 1, "north", [jp("管制室"), "CONTROL", "", ""], "birch")
    w.set(bx0 + 3, FY + 7, bz1 - 1, "iron_bars"); w.set(bx0 + 3, FY + 8, bz1 - 1, "iron_bars"); w.set(bx0 + 3, FY + 9, bz1 - 1, "end_rod[facing=up]")
    # --- the gate passage: lamps in the ceiling and on both jambs, hazard stripes on the jambs; the hall behind stays the darker place
    for x in range(GX0 + 1, GX1, 3):
        for z in (14, 17, 20):
            w.set(x, FY + 10, z, "sea_lantern")
    for z in range(12, 23):
        for x in (GX0 - 1, GX1 + 1):
            for y in range(FY + 1, FY + 10):
                if z >= 21:
                    w.set(x, y, z, "yellow_concrete" if (y + z) % 3 else "black_concrete")
                elif z in (14, 18):
                    if y in (FY + 4, FY + 5):
                        w.set(x, y, z, "sea_lantern")
    # floodlights over the gate, on the portal wall's face (the blast gate leaves stand either side)
    for x in range(180, 201, 5):
        w.set(x, FY + 12, 23, "sea_lantern")
    S.keep[HX0:HX1 + 1, HZ0 - 1:HZ1 + 2] = True


# --------------------------------------------------------------------------------------------- buildings
STYLES = [
    # wall, base course, trim, weight
    ("white_concrete", "light_gray_concrete", "gray_concrete", 30),
    ("light_gray_concrete", "gray_concrete", "white_concrete", 22),
    ("white_terracotta", "light_gray_concrete", "white_concrete", 16),
    ("smooth_sandstone", "sandstone", "white_concrete", 12),
    ("calcite", "light_gray_concrete", "gray_concrete", 8),
    ("stone_bricks", "stone", "light_gray_concrete", 5),
    ("mud_bricks", "stone", "white_concrete", 4),
]
BANDS = ["red_concrete", "blue_concrete", "green_concrete", "yellow_concrete", "orange_concrete", "cyan_concrete", "white_concrete", "brown_concrete"]
BLADES = ["acacia", "warped", "crimson", "cherry", "jungle", "mangrove"]
SHOPS = [("酒", "SAKE"), ("米", "RICE"), ("薬", "DRUGS"), ("理容", "BARBER"), ("弁当", "BENTO"),
         ("食堂", "DINER"), ("パン", "BAKERY"), ("喫茶", "CAFE"), ("靴", "SHOES"),
         ("花", "FLOWERS"), ("田中", "TANAKA"), ("中華", "RAMEN"), ("ゆ", "BATH"), ("時計", "WATCH")]
ROOFS = ["deepslate_tile", "deepslate_tile", "deepslate_tile", "mud_brick", "stone_brick"]


def pick_style(rng):
    tot = sum(s[3] for s in STYLES)
    r = rng.random() * tot
    for s in STYLES:
        r -= s[3]
        if r <= 0:
            return s
    return STYLES[0]


class Frame:
    """Building-local coordinates: u runs along the street frontage, v inward from the front wall (v = 0 is the front row)."""

    def __init__(self, w, x0, z0, ex, ez, front):
        self.w, self.x0, self.z0, self.ex, self.ez, self.front = w, x0, z0, ex, ez, front
        self.U, self.V = (ex, ez) if front in ("north", "south") else (ez, ex)
        self.out = front
        self.inn = OPP[front]
        self.along = "x" if front in ("north", "south") else "z"      # world axis the front wall runs along
        self.across = "z" if self.along == "x" else "x"

    def at(self, u, v):
        f = self.front
        if f == "south":
            return self.x0 + u, self.z0 + self.ez - 1 - v
        if f == "north":
            return self.x0 + u, self.z0 + v
        if f == "east":
            return self.x0 + self.ex - 1 - v, self.z0 + u
        return self.x0 + v, self.z0 + u

    def put(self, u, v, y, block):
        x, z = self.at(u, v)
        self.w.set(x, y, z, block)

    def fill(self, u0, v0, y0, u1, v1, y1, block):
        xa, za = self.at(u0, v0)
        xb, zb = self.at(u1, v1)
        self.w.fill(xa, y0, za, xb, y1, zb, block)

    def pane(self, side):
        """pane block for the wall on `side` ('front','back' run along `along`; 'left','right' along `across`)."""
        return pane(self.along if side in ("front", "back") else self.across)


def roof_gable(F, ytop, mat, pitch2, wall):
    V, U = F.V, F.U
    half = V // 2
    for k in range(half):
        if pitch2:
            if k % 2 == 0:
                ys, kind = ytop + k // 2, "slab"
            else:
                ys, kind = ytop + (k - 1) // 2, "stair"
        else:
            ys, kind = ytop + k, "stair"
        for side, v in (("f", k), ("b", V - 1 - k)):
            for u in range(-1, U + 1):                       # 1-block eaves at the gable ends
                if kind == "slab":
                    x, z = F.at(u, v)
                    slab(F.w, x, ys, z, mat)
                else:
                    x, z = F.at(u, v)
                    stair(F.w, x, ys, z, mat, F.inn if side == "f" else F.out)
            if ys > ytop:                                    # close the gable ends under the roof
                for u in (0, U - 1):
                    F.fill(u, v, ytop, u, v, ys - 1, wall)
    if V % 2 == 1:                                           # a ridge row for odd depths
        v = half
        ys = ytop + ((half) // 2 if pitch2 else half)
        for u in range(-1, U + 1):
            x, z = F.at(u, v)
            slab(F.w, x, ys, z, mat)
        for u in (0, U - 1):
            F.fill(u, v, ytop, u, v, ys - 1, wall)
    return ytop + (half // 2 if pitch2 else half)


AWNINGS = [("warped", "birch"), ("red_nether_brick", "quartz"), ("acacia", "birch"), ("prismarine_brick", "quartz"),
           ("mangrove", "birch"), ("cherry", "quartz"), ("crimson", "birch"), ("bamboo", "quartz")]


def building(S, x0, z0, ex, ez, front, floors, style=None, roof=None, shop=True, rng=None, awning=False):
    """A low town building: shuttered shopfront below, windowed floors above, flat or tile roof.
    Footprint [x0, x0+ex) x [z0, z0+ez); `front` is the side facing the street. awning=True hangs a striped shop awning (two rows, a
    stair and a slab, colours from a private random stream so that the town's own random look stays as it was) over the pavement."""
    w = S.w
    rng = rng or S.rng
    F = Frame(w, x0, z0, ex, ez, front)
    U, V = F.U, F.V
    wall, base, trim, _ = style or pick_style(rng)
    y0 = GY
    H = 4 * floors
    S.occ[x0 - 1:x0 + ex + 1, z0 - 1:z0 + ez + 1] = True
    S.keep[x0 - 1:x0 + ex + 1, z0 - 1:z0 + ez + 1] = True
    # --- shell
    for v in range(V):
        for u in range(U):
            edge = u in (0, U - 1) or v in (0, V - 1)
            x, z = F.at(u, v)
            w.set(x, GY - 1, z, "stone")
            if edge:
                w.fill(x, y0, z, x, y0 + H - 1, z, wall)
                w.set(x, y0, z, base)
            else:
                for k in range(floors):
                    w.set(x, y0 + 4 * k + 3, z, "light_gray_concrete" if k < floors - 1 else "light_gray_concrete")
    band = rng.choice(BANDS)
    # --- ground floor front: shutters, a side door, sign band
    door_u = rng.choice([1, U - 3]) if shop else U // 2
    for u in range(1, U - 1):
        if u in (door_u, door_u + 1):
            if u == door_u:
                for dy, half in ((0, "lower"), (1, "upper")):
                    F.put(u, 0, y0 + dy, bs("iron_door", facing=F.inn, half=half, hinge="left", open=False, powered=False))
                F.put(u + 1, 0, y0 + 0, "gray_concrete")
                F.put(u + 1, 0, y0 + 1, "gray_concrete")
            continue
        for dy in (0, 1):
            F.put(u, 0, y0 + dy, bs("iron_trapdoor", facing=F.inn, half="bottom", open=True))
            F.put(u, 1, y0 + dy, "gray_concrete" if (u + dy) % 3 else "light_gray_concrete")
        F.put(u, 0, y0 + 2, band)
    F.put(door_u, 0, y0 + 2, band)
    F.put(door_u + 1, 0, y0 + 2, band)
    F.put(0, 0, y0 + 2, wall)
    F.put(U - 1, 0, y0 + 2, wall)
    # sign text on the band: one or two wall signs
    kind = rng.choice(SHOPS)
    cu = U // 2 if abs(U // 2 - door_u) > 2 else (U - 3 if door_u < 3 else 2)
    x, z = F.at(cu, -1)
    place_wall_sign(w, x, y0 + 2, z, F.out, [jp(kind[0]), kind[1], "", ""], "birch")
    if awning:
        arng = random.Random(x0 * 131 + z0 * 7 + 5)
        c1, c2 = arng.choice(AWNINGS)
        for u in range(1, U - 1):
            mat = c1 if u % 2 == 0 else c2
            x, z = F.at(u, -1)
            stair(w, x, y0 + 3, z, mat, F.inn)
            x, z = F.at(u, -2)
            slab(w, x, y0 + 3, z, mat)
    # protruding blade sign (a coloured trapdoor panel turned edge-on), at one end
    bu = U - 1 if door_u < 3 else 0
    side = RIGHT[F.out] if bu == U - 1 else LEFT[F.out]
    for dy in (3, 4, 5):
        x, z = F.at(bu, -1)
        w.set(x, y0 + dy, z, bs(rng.choice(BLADES) + "_trapdoor", facing=side, half="bottom", open=True))
    # --- upper floors
    for k in range(1, floors):
        b = y0 + 4 * k
        for u in range(1, U - 1):
            if (u - 1) % 3 in (0, 1):
                for dy in (1, 2):
                    F.put(u, 0, b + dy, F.pane("front"))
                if rng.random() < 0.18:                               # outdoor air-conditioner on the sill
                    F.put(u, -1, b + 1, "white_concrete")
            elif rng.random() < 0.2:
                F.put(u, 0, b + 2, trim)
        # back wall windows, fewer
        for u in range(2, U - 2, 3):
            for dy in (1, 2):
                F.put(u, V - 1, b + dy, F.pane("back"))
        # side windows
        for v in range(2, V - 2, 4):
            for dy in (1, 2):
                F.put(0, v, b + dy, F.pane("left"))
                F.put(U - 1, v, b + dy, F.pane("right"))
        # balcony on some storeys
        if rng.random() < 0.35 and U >= 8:
            bu0 = rng.randint(1, U - 6)
            for u in range(bu0, bu0 + 4):
                F.put(u, -1, b, bs("smooth_stone_slab", type="bottom"))
                F.put(u, -2, b + 1, bars(F.along))
            for dv in (-1, -2):
                F.put(bu0, dv, b + 1, "iron_bars")
                F.put(bu0 + 3, dv, b + 1, "iron_bars")
    # spandrel line (trim) between floors on the front
    for k in range(1, floors):
        for u in range(1, U - 1):
            F.put(u, 0, y0 + 4 * k, trim)
    # --- roof
    ytop = y0 + H
    mode = roof or ("tile" if (floors <= 3 and rng.random() < 0.35) else "flat")
    if mode == "flat":
        F.fill(0, 0, ytop, U - 1, 0, ytop, wall)
        F.fill(0, V - 1, ytop, U - 1, V - 1, ytop, wall)
        F.fill(0, 0, ytop, 0, V - 1, ytop, wall)
        F.fill(U - 1, 0, ytop, U - 1, V - 1, ytop, wall)
        F.fill(0, 0, ytop - 1, U - 1, 0, ytop - 1, trim)               # cornice
        for _ in range(rng.randint(1, 3)):                             # roof clutter
            ru, rv = rng.randint(2, max(2, U - 4)), rng.randint(2, max(2, V - 4))
            what = rng.choice(["ac", "tank", "mast", "stairs"])
            if what == "ac":
                F.fill(ru, rv, ytop, ru + 1, rv, ytop + 1, "light_gray_concrete")
                F.put(ru, rv, ytop + 2, "iron_trapdoor[facing=north,half=bottom,open=false]")
            elif what == "tank":
                for lu, lv in ((ru, rv), (ru + 2, rv), (ru, rv + 2), (ru + 2, rv + 2)):
                    F.fill(lu, lv, ytop, lu, lv, ytop + 1, "iron_bars")
                F.fill(ru, rv, ytop + 2, ru + 2, rv + 2, ytop + 3, "light_gray_concrete")
            elif what == "mast":
                F.fill(ru, rv, ytop, ru, rv, ytop + rng.randint(4, 7), "iron_bars")
                F.put(ru, rv, ytop + 3, "iron_bars")
            else:
                F.fill(ru, rv, ytop, ru + 2, rv + 2, ytop + 3, wall)
                for dy, half in ((1, "lower"), (2, "upper")):                  # stair-head with a steel door
                    F.put(ru, rv, ytop + dy, bs("iron_door", facing=F.inn, half=half, hinge="left", open=False, powered=False))
    else:
        mat = rng.choice(ROOFS)
        roof_gable(F, ytop, mat, V >= 9, wall)
    return F


def house(S, x0, z0, ex, ez, front, rng=None):
    """A small detached house: one or two floors, white or timber walls, a tile roof, a front door and a low garden wall."""
    w = S.w
    rng = rng or S.rng
    F = Frame(w, x0, z0, ex, ez, front)
    U, V = F.U, F.V
    floors = rng.choice([1, 2, 2])
    wall = rng.choice(["white_concrete", "white_terracotta", "calcite", "smooth_sandstone", "light_gray_concrete"])
    trim = "dark_oak_planks" if rng.random() < 0.5 else "gray_concrete"
    y0 = GY
    H = 4 * floors
    S.occ[x0 - 2:x0 + ex + 2, z0 - 2:z0 + ez + 2] = True
    S.keep[x0 - 1:x0 + ex + 1, z0 - 1:z0 + ez + 1] = True
    for v in range(V):
        for u in range(U):
            x, z = F.at(u, v)
            w.set(x, GY - 1, z, "stone")
            if u in (0, U - 1) or v in (0, V - 1):
                w.fill(x, y0, z, x, y0 + H - 1, z, wall)
                w.set(x, y0, z, "light_gray_concrete")
            else:
                for k in range(floors):
                    w.set(x, y0 + 4 * k + 3, z, "light_gray_concrete")
    # door and windows
    du = rng.randint(1, max(1, U - 3))
    for dy, half in ((1, "lower"), (2, "upper")):
        F.put(du, 0, y0 + dy - 1, bs("iron_door", facing=F.inn, half=half, hinge="left", open=False, powered=False))
    for k in range(floors):
        b = y0 + 4 * k
        for u in range(1, U - 1):
            if abs(u - du) > 1 and (u % 3) != 0:
                for dy in (1, 2):
                    F.put(u, 0, b + dy, F.pane("front"))
        for u in range(2, U - 2, 3):
            for dy in (1, 2):
                F.put(u, V - 1, b + dy, F.pane("back"))
        for v in range(2, V - 2, 3):
            for dy in (1, 2):
                F.put(0, v, b + dy, F.pane("left"))
                F.put(U - 1, v, b + dy, F.pane("right"))
    # dark timber band under the eaves
    F.fill(0, 0, y0 + H - 1, U - 1, 0, y0 + H - 1, trim)
    F.fill(0, V - 1, y0 + H - 1, U - 1, V - 1, y0 + H - 1, trim)
    roof_gable(F, y0 + H, rng.choice(ROOFS), V >= 9, wall)
    # a tiny step and a potted shrub at the door
    return F


# --------------------------------------------------------------------------------------------- cars
CAR_COLORS = {            # body block, roof carpet
    "white": ("white_concrete", "white_carpet"), "silver": ("light_gray_concrete", "light_gray_carpet"),
    "black": ("black_concrete", "black_carpet"), "blue": ("blue_concrete", "blue_carpet"),
    "red": ("red_concrete", "red_carpet"), "yellow": ("yellow_concrete", "yellow_carpet"),
    "green": ("green_concrete", "green_carpet"), "gray": ("gray_concrete", "gray_carpet"),
    "lightblue": ("light_blue_concrete", "light_blue_carpet"), "orange": ("orange_concrete", "orange_carpet"),
}


def _carmap(x, z, facing, W, L):
    """(u, v) -> world (x, z) for a car whose bounding box has min corner (x, z); u across (to the right), v forward."""
    if facing == "east":
        return lambda u, v: (x + v, z + u)
    if facing == "west":
        return lambda u, v: (x + L - 1 - v, z + W - 1 - u)
    if facing == "south":
        return lambda u, v: (x + W - 1 - u, z + v)
    return lambda u, v: (x + u, z + L - 1 - v)


def parked_car(w, x, y, z, facing, color="white"):
    """An abandoned family car, 2 wide x 5 long x 2 high (+ carpet roof). (x, z) is the bounding box's min corner;
    y is the first air row above the ground."""
    body, roof = CAR_COLORS[color]
    m = _carmap(x, z, facing, 2, 5)
    for u in range(2):
        for v in range(5):
            px, pz = m(u, v)
            b = {0: "red_concrete", 1: "black_concrete", 3: "black_concrete", 4: "light_gray_concrete"}.get(v, body)
            if v in (1, 3):
                b = "black_concrete"                                 # wheels
            w.set(px, y, pz, b)
            if 1 <= v <= 3:
                w.set(px, y + 1, pz, "tinted_glass")
                w.set(px, y + 2, pz, roof)
    # body-coloured arch fillers: bonnet, boot lid, doors between the wheels
    for u in range(2):
        for v, b in ((2, body), (4, body)):
            px, pz = m(u, v)
            w.set(px, y, pz, b)


def car(w, x, y, z, facing, color="blue"):
    """The heroine's small blue sports coupe: 4 wide x 7 long x 2 high (a carpet roof makes it 2 + 1/16).
    Lowest block row at `y`; (x, z) is the PASSENGER-SEAT cell (the left-centre cell as seen from behind: u = 1, v = 3 counted from the
    left-rear). The driver sits at u = 2. Cabin air is 2 x 2 x 2 (rows y, y + 1) with the seat cushions one cell behind the
    seat cell, so an eye at y + 1.62 over the seat cell looks out through the glass band.  Returns a dict of positions."""
    body, roof = CAR_COLORS[color]
    r = RIGHT[facing]
    # bounding-box min corner from the seat cell
    W, L = 4, 7
    # find min corner such that map(1, 3) == (x, z)
    probe = _carmap(0, 0, facing, W, L)(1, 3)
    ox, oz = x - probe[0], z - probe[1]
    m = _carmap(ox, oz, facing, W, L)

    def P(u, v, yy, b):
        px, pz = m(u, v)
        w.set(px, yy, pz, b)
    for u in range(W):
        for v in range(L):
            side = u in (0, W - 1)
            b = body
            if side and v in (1, 5):
                b = "black_concrete"                                  # wheels
            if v == 0 and side:
                b = "red_concrete"                                    # tail lamps
            if v == L - 1 and side:
                b = "white_concrete"                                  # head lamps
            if not side and v >= 4:
                b = "white_concrete" if v >= 5 else body              # racing stripe on the bonnet
            if not side and v == 6:
                b = "light_gray_concrete"
            P(u, v, y, b)
            P(u, v, y + 1, "air")
    # cabin: hollow in the middle, dash and shelves, glass band
    for u in (1, 2):
        for v in (2, 3):
            P(u, v, y, "air")
    for u in (1, 2):
        P(u, 4, y, "black_concrete")                                  # dashboard
        P(u, 1, y, body)                                              # rear shelf
        P(u, 2, y, bs("polished_blackstone_slab", type="bottom"))     # seat cushions behind the seat cell
    for v in (1, 2, 3, 4):
        for u in range(W):
            if (u in (0, W - 1)) and v in (1, 4):
                P(u, v, y + 1, body)                                  # pillars
            elif (u in (0, W - 1)) or v in (1, 4):
                P(u, v, y + 1, "light_blue_stained_glass")
            else:
                P(u, v, y + 1, "air")
            P(u, v, y + 2, roof)
    P(2, 3, y + 1, "air")
    # steering wheel on the driver's side: a trapdoor tilted toward the driver
    px, pz = m(2, 4)
    w.set(px, y + 1, pz, bs("dark_oak_trapdoor", facing=OPP[facing], half="bottom", open=True))
    sx, sz = m(1, 3)
    # footprint centre: average of the bounding box
    xs = [m(u, v)[0] for u in (0, W - 1) for v in (0, L - 1)]
    zs = [m(u, v)[1] for u in (0, W - 1) for v in (0, L - 1)]
    return {"centre": ((min(xs) + max(xs)) / 2 + 0.5, y, (min(zs) + max(zs)) / 2 + 0.5),
            "passenger": (sx + 0.5, y, sz + 0.5), "driver": (m(2, 3)[0] + 0.5, y, m(2, 3)[1] + 0.5),
            "yaw": YAW[facing], "facing": facing}


# --------------------------------------------------------------------------------------------- the town: population
def lanes_and_lots(S):
    w, rng = S.w, S.rng
    for z0, z1 in ((98, 101), (155, 158)):                      # back lanes behind the two frontages
        w.fill(92, GY - 1, z0, 146, GY - 1, z1, ROAD)

    def row(xa, xb, front, zf, dmin, dmax, gap=0.2, floors=(2, 3, 4), fw=(4, 4, 2), awnings=True):
        x = xa
        while xb - x + 1 >= 6:
            wd = rng.randint(8, 14)
            if xb - (x + wd) + 1 < 6:
                wd = xb - x + 1
            d = rng.randint(dmin, dmax)
            fl = rng.choices(floors, fw)[0]
            z0 = zf - d + 1 if front == "south" else zf
            building(S, x, z0, wd, d, front, fl, awning=awnings)
            x += wd
            if rng.random() < gap:
                x += 2

    row(92, 107, "south", FRONT_N, 13, 17)
    row(125, 139, "south", FRONT_N, 12, 17)
    row(157, 170, "south", FRONT_N, 8, 10, floors=(2, 3), fw=(3, 2))
    row(92, 107, "north", FRONT_S, 12, 17)
    row(125, 150, "north", FRONT_S, 12, 17)
    row(154, 171, "north", FRONT_S, 9, 11, floors=(2, 3), fw=(3, 2))
    # the forecourt's two flanks: longer shuttered arcades facing the plaza
    row(58, 90, "south", 97, 13, 13, gap=0.0, floors=(2, 3), fw=(1, 1))
    row(58, 90, "north", 159, 13, 13, gap=0.0, floors=(2, 3), fw=(1, 1))
    # houses behind the lanes
    x = 93
    while x < 108:
        wd = rng.randint(7, 9)
        house(S, x, 97 - 10 + 1, wd, 10, "south")
        x += wd + 1
    x = 121
    while x < 143:
        wd = rng.randint(7, 9)
        house(S, x, 97 - rng.randint(9, 11) + 1, wd, 10, "south")
        x += wd + 1
    x = 93
    while x < 108:
        wd = rng.randint(7, 9)
        house(S, x, 159, wd, 10, "north")
        x += wd + 1
    x = 121
    while x < 144:
        wd = rng.randint(7, 9)
        house(S, x, 159, wd, 10, "north")
        x += wd + 1


def pole(S, x, z, h=11, arm="z", transformer=False):
    """Concrete utility pole with a timber cross-arm; returns the wire attachment points."""
    w = S.w
    for y in range(GY, GY + h):
        w.set(x, y, z, "andesite_wall")
    ya = GY + h - 2
    if arm == "z":
        for dz in range(-2, 3):
            w.set(x, ya, z + dz, bs("dark_oak_fence", north=True, south=True) if dz else bs("dark_oak_fence", north=True, south=True))
        w.set(x, ya + 1, z, "light_gray_concrete")
        pts = [(x, ya + 1, z - 2), (x, ya + 1, z), (x, ya + 1, z + 2)]
        for pz in (z - 2, z + 2):
            w.set(x, ya + 1, pz, "light_gray_concrete")
    else:
        for dx in range(-2, 3):
            w.set(x + dx, ya, z, bs("dark_oak_fence", east=True, west=True))
        pts = [(x - 2, ya + 1, z), (x, ya + 1, z), (x + 2, ya + 1, z)]
    if transformer:
        w.fill(x + 1, ya - 3, z, x + 1, ya - 2, z, "gray_concrete") if arm == "z" else None
    S.occ[x, z] = True
    return pts


def wires(S, a, b, sag=1.5):
    for pa, pb in zip(a, b):
        chain_line(S.w, pa[0], pa[1], pa[2], pb[0], pb[1], pb[2], sag=sag)


def signal(S, x, z, arm_to, facing_head):
    """Traffic-signal mast on the pavement at (x, z) with an arm over the carriageway to z = arm_to; the heads face `facing_head`."""
    w = S.w
    # a thin mast, a short arm that reaches only over the kerb lane (never toward the middle of the carriageway), and one compact
    # head 1 x 3 hanging from its end: black housing with three small dark lenses (power is off) on both faces
    for y in range(GY, GY + 8):
        w.set(x, y, z, "andesite_wall")
    step = 1 if arm_to > z else -1
    zend = z + 3 * step
    for zz in range(z + step, zend + step, step):
        w.set(x, GY + 7, zz, bs("iron_bars", north=True, south=True))
    for dy, lens in ((6, "crimson_button"), (5, "bamboo_button"), (4, "warped_button")):
        w.set(x, GY + dy, zend, "black_concrete")
        w.set(x + 1, GY + dy, zend, bs(lens, face="wall", facing="east", powered=False))
        w.set(x - 1, GY + dy, zend, bs(lens, face="wall", facing="west", powered=False))
    w.set(x, GY + 3, zend, "light_gray_concrete") if False else None
    S.occ[x, z] = True


def bike(S, x, z, axis="x", y=None):
    """A leaning bicycle: wheels as open iron trapdoors, a black saddle and handlebars."""
    w = S.w
    y = GY if y is None else y
    if axis == "x":
        w.set(x, y, z, bs("iron_trapdoor", facing="north", half="bottom", open=True))
        w.set(x + 2, y, z, bs("iron_trapdoor", facing="north", half="bottom", open=True))
        w.set(x + 1, y, z, "iron_bars[east=true,west=true]")
        w.set(x + 1, y + 1, z, "end_rod[facing=up]")
        w.set(x + 2, y + 1, z, "iron_bars")
    else:
        w.set(x, y, z, bs("iron_trapdoor", facing="east", half="bottom", open=True))
        w.set(x, y, z + 2, bs("iron_trapdoor", facing="east", half="bottom", open=True))
        w.set(x, y, z + 1, "iron_bars[north=true,south=true]")
        w.set(x, y + 1, z + 1, "end_rod[facing=up]")
        w.set(x, y + 1, z + 2, "iron_bars")
    if axis == "x":
        S.occ[x:x + 3, z] = True
    else:
        S.occ[x, z:z + 3] = True


def notice_board(S, x, z, facing="south", wide=5):
    """An evacuation notice board: two posts, a white panel with a red head band, and the notice as sign text."""
    w = S.w
    y = GY
    h = DIRS[RIGHT[facing]]
    for k in (0, wide - 1):
        for dy in range(4):
            w.set(x + h[0] * k, y + dy, z + h[1] * k, "andesite_wall")
    for k in range(wide):
        px, pz = x + h[0] * k, z + h[1] * k
        w.set(px, y + 2, pz, "red_concrete")
        w.set(px, y + 1, pz, "white_concrete")
    f = DIRS[facing]
    mid = wide // 2
    px, pz = x + h[0] * mid + f[0], z + h[1] * mid + f[1]
    place_wall_sign(w, px, y + 2, pz, facing, [jp("避難命令"), "EVACUATION", "ORDER", ""], "birch")
    px2, pz2 = x + h[0] * (mid - 1) + f[0], z + h[1] * (mid - 1) + f[1]
    place_wall_sign(w, px2, y + 1, pz2, facing, [jp("特別非常事態宣言"), "STATE OF", "EMERGENCY", ""], "birch")
    S.occ[min(x, x + h[0] * wide):max(x, x + h[0] * wide) + 1, min(z, z + h[1] * wide):max(z, z + h[1] * wide) + 1] = True


def tree(S, x, y, z, kind="oak", h=None):
    """A planted tree: trunk and persistent leaves. kind: oak (round), cedar (tall cone), birch (slim)."""
    w, rng = S.w, S.rng
    if kind == "cedar":
        h = h or rng.randint(11, 17)
        for yy in range(y, y + h):
            w.set(x, yy, z, bs("spruce_log", axis="y"))
        for i, yy in enumerate(range(y + 3, y + h + 2)):
            r = max(0, min(3, (h + 2 - (yy - y)) // 3))
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if dx * dx + dz * dz <= r * r + 1 and (dx or dz or yy >= y + h):
                        put_if_air(w, x + dx, yy, z + dz, "spruce_leaves[persistent=true]")
    elif kind == "birch":
        h = h or rng.randint(6, 9)
        for yy in range(y, y + h):
            w.set(x, yy, z, bs("birch_log", axis="y"))
        for yy in range(y + h - 4, y + h + 2):
            r = 2 if yy < y + h + 1 else 1
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if dx * dx + dz * dz <= r * r + 1 and (dx or dz or yy >= y + h):
                        put_if_air(w, x + dx, yy, z + dz, "birch_leaves[persistent=true]")
    else:
        h = h or rng.randint(5, 8)
        for yy in range(y, y + h):
            w.set(x, yy, z, bs("oak_log", axis="y"))
        r0 = rng.choice([3, 3, 4])
        for yy in range(y + h - 3, y + h + 3):
            r = r0 - max(0, abs(yy - (y + h)) - 1)
            for dx in range(-r, r + 1):
                for dz in range(-r, r + 1):
                    if dx * dx + dz * dz <= r * r + 1 and (dx or dz or yy >= y + h):
                        put_if_air(w, x + dx, yy, z + dz, "oak_leaves[persistent=true]")


def phone_booth(S, x0, z0):
    """A glass payphone booth, outer 4 wide x 5 deep, open on the south side; the green telephone is on the north wall
    with a shelf in front of it. Returns (stand position, phone position)."""
    w = S.w
    y = GY                                                   # forecourt slabs raise the walking level to 32.5; props start at the slab cell
    D = 5
    for dx in range(4):
        for dz in range(D):
            x, z = x0 + dx, z0 + dz
            w.set(x, GY - 1, z, "stone")
            slab(w, x, GY, z, "polished_andesite")
            edge = dx in (0, 3) or dz in (0, D - 1)
            corner = dx in (0, 3) and dz in (0, D - 1)
            if edge:
                for yy in range(y, y + 3):
                    if corner:
                        w.set(x, yy, z, "light_gray_concrete")
                    elif dz == D - 1 and dx in (1, 2):
                        w.set(x, yy, z, "air")               # the doorway
                    else:
                        w.set(x, yy, z, pane("x") if dz in (0, D - 1) else pane("z"))
            w.set(x, y + 3, z, "light_gray_concrete")
    w.fill(x0, y + 4, z0, x0 + 3, y + 4, z0 + D - 1, "white_concrete")
    # a booth you cannot miss: a bright white back wall with a lime telephone on it at eye level (two blocks tall: the body, a cyan
    # display, a black handset cradle and a yellow coin box), a lamp over it, a yellow mat on the floor, and a lit green blade sign
    px = x0 + 1
    for xx in (px, px + 1):
        for yy in range(y + 1, y + 3):
            w.set(xx, yy, z0 + 1, "white_concrete")                    # back panel behind and beside the phone
    w.set(px, y + 1, z0 + 1, "lime_concrete")                          # the telephone body (eye level: 33.5 .. 34.5 for a 34.1 eye)
    w.set(px, y + 2, z0 + 1, "lime_concrete")
    w.set(px + 1, y + 2, z0 + 1, bs("polished_blackstone_stairs", facing="east", half="top", shape="straight"))   # the handset on its cradle
    w.set(px + 1, y + 1, z0 + 1, "yellow_concrete")                    # coin box
    w.set(px, y + 3, z0 + 1, "sea_lantern")                            # lamp over the phone (in the roof row)
    w.set(px + 1, y + 3, z0 + 1, "sea_lantern")
    # the sign: a green blade on the south front, lit, with the name on it
    for yy in range(y + 5, y + 9):
        w.set(x0, yy, z0 + D - 1, "green_concrete")
    w.set(x0, y + 9, z0 + D - 1, "sea_lantern")
    place_wall_sign(w, x0 + 1, y + 5, z0 + D - 1, "east", [jp("公衆電話"), "PUBLIC", "TELEPHONE", ""], "birch")
    place_wall_sign(w, x0 - 1, y + 5, z0 + D - 1, "west", [jp("公衆電話"), "PUBLIC", "TELEPHONE", ""], "birch")
    S.occ[x0 - 1:x0 + 5, z0 - 1:z0 + D + 1] = True
    return (x0 + 1.5, y + 0.5, z0 + 3.5), (x0 + 1.5, y + 1.5, z0 + 1.5)


def street_scene(S, with_car=False):
    """Everything that makes the town look abandoned in the middle of its day: poles and wires, signals, cars, bikes,
    drink machines, notice boards, the payphone, a bus stop, a closed kiosk, planters, the sea-front."""
    w, rng = S.w, S.rng
    wmix = [("polished_diorite", 0.10), ("polished_andesite", 0.12)]
    # corners of the two junctions that the pavement strips miss
    for xa, xb in ((108, 111), (121, 124), (140, 143), (153, 156)):
        paving(w, xa, WALK_N[0], xb, WALK_N[1], var=wmix, rng=rng)
    for xa, xb in ((108, 111), (121, 124)):
        paving(w, xa, WALK_S[0], xb, WALK_S[1], var=wmix, rng=rng)
    paving(w, 140, WALK_S[0], 156, WALK_S[1], var=wmix, rng=rng)

    # --- utility poles and wires along both pavements
    north = [pole(S, x, 121, 11) for x in (101, 129, 157)]
    south = [pole(S, x, 135, 11) for x in (105, 133, 161)]
    # one clean, level run per side (the middle conductor only), no service drops across the road: wires of chain links read as
    # dotted dashes, so there are as few of them as can be and none cross the centre of the street's views
    for a, b in zip(north, north[1:]):
        wires(S, a[1:2], b[1:2], sag=0.0)
    for a, b in zip(south, south[1:]):
        wires(S, a[1:2], b[1:2], sag=0.0)
    # stub poles into the forecourt and the back lanes
    pole(S, 60, 156, 10)
    pole(S, 60, 100, 10)
    # --- traffic signals at the two junctions
    signal(S, 124, 135, 125, "west")
    signal(S, 108, 121, 131, "east")
    signal(S, 141, 121, 131, "west")                    # (not on the junction corner: the car turns into the hill street across it)
    signal(S, 156, 135, 125, "east")
    # --- parked cars along the kerbs (left-hand traffic: eastbound on the north side)
    cols = ["white", "silver", "black", "blue", "red", "yellow", "green", "gray", "lightblue", "orange", "white", "silver"]
    spots_n = [104, 124, 158, 164]
    spots_s = [106, 126, 145, 162]
    # (tucked right against the kerbs: the story drives the middle of the street, a car 4 wide and 0.5 clear on each side)
    for x in spots_n:
        if x + 5 < 140 and x > 108 and x < 122:
            continue
        parked_car(w, x, GY, ROAD_Z[0], "east", rng.choice(cols))
    for x in spots_s:
        parked_car(w, x, GY, ROAD_Z[1] - 1, "west", rng.choice(cols))
    # a car left half onto the pavement on the cross street, one in the lane behind the shops
    parked_car(w, 114, GY, 150, "south", "silver")
    parked_car(w, 117, GY, 109, "north", "blue")
    # lane parking
    parked_car(w, 125, GY, 99, "east", "gray")
    parked_car(w, 100, GY, 156, "east", "white")
    # --- bicycles at the station and along the shop fronts
    for z in (106, 108, 110, 112):
        bike(S, 56, z, "x")
    for x in (96, 102, 129, 153):                                             # (153: on the pavement, not on the hill street)
        bike(S, x, 120, "x")
    for x in (98, 128, 166):
        bike(S, x, 136, "x")
    # --- vending machines against the shop fronts, and on the forecourt
    for x in (94, 131, 161):
        vending(w, x, GY, 119, "south", rng.choice(["red_concrete", "blue_concrete", "white_concrete"]))
    for x in (96, 135, 168):
        vending(w, x, GY, 137, "north", rng.choice(["red_concrete", "blue_concrete", "light_blue_concrete"]))
    vending(w, 58, GY, 134, "east", "red_concrete")
    vending(w, 58, GY, 124, "east", "blue_concrete")
    # --- evacuation notice boards
    notice_board(S, 57, 100, "south")
    notice_board(S, 80, 100, "south")
    notice_board(S, 138, 136, "north", 4)
    notice_board(S, 74, 158, "north", 5)
    notice_board(S, 164, 120, "south", 4)
    # --- payphone booth on the north side of the forecourt
    stand, phone = phone_booth(S, 64, 112)
    S.stand, S.phone = stand, phone
    # --- bus stop in the south-west corner of the forecourt
    for dz in range(3):
        for dy in range(4):
            pass
    for x in (58, 62):
        for dy in range(0, 4):
            w.set(x, GY + dy, 150, "andesite_wall")
            w.set(x, GY + dy, 153, "andesite_wall")
    w.fill(57, GY + 4, 150, 63, GY + 4, 153, "light_gray_concrete")
    for x in (59, 60, 61):
        w.set(x, GY + 1, 153, pane("x")) ; w.set(x, GY + 2, 153, pane("x"))
        slab(w, x, GY, 152, "birch")
    for dy in range(5):
        w.set(64, GY + dy, 150, "iron_bars")
    w.fill(64, GY + 4, 150, 65, GY + 5, 150, "blue_concrete")
    S.occ[56:66, 148:156] = True
    # --- closed kiosk on the forecourt, west of the crash site
    building(S, 60, 138, 7, 5, "east", 1, style=("white_concrete", "light_gray_concrete", "gray_concrete", 1), roof="flat")
    # --- planters with trees
    for px, pz in ((60, 104), (76, 104), (76, 130 - 24 + 50)):
        for dx in range(3):
            for dz in range(3):
                x, z = px + dx, pz + dz
                w.set(x, GY, z, "stone_bricks" if (dx, dz) != (1, 1) else "grass_block")
        tree(S, px + 1, GY + 1, pz + 1, rng.choice(["oak", "birch"]))
        S.occ[px - 1:px + 4, pz - 1:pz + 4] = True
    # --- the sea-front: promenade, rail, benches and low lamps (nothing tall in the angel corridor)
    for x in range(172, 184):
        for z in range(106, 151):
            w.set(x, GY - 1, z, "stone")
            slab(w, x, GY, z, "polished_andesite" if (x + z) % 5 else "smooth_stone")
    for z in list(range(106, 121)) + list(range(137, 151)):
        w.set(184, GY, z, "iron_bars")
        w.set(184, GY - 1, z, "stone")
    for z in (110, 116, 140, 146):
        for i in range(3):
            slab(w, 178, GY, z + i, "birch")
            w.set(177, GY, z + i, bs("birch_trapdoor", facing="east", half="bottom", open=True))
    for z in (108, 148):
        for dy in range(4):
            w.set(176, GY + dy, z, "andesite_wall")
        w.set(176, GY + 4, z, "lantern[hanging=false]")
    # a closed bait shop and a drinks machine on the promenade's end
    S.keep[170:200, 96:162] = True
    # --- the optional heroine's car
    if with_car:
        info = car(w, 97, GY, 130, "east", "blue")
        S.car_info = info


def planter(S, x, z, sx, sz, kind=0):
    """A raised brick planter sx x sz blocks with soil and flowers, a flowering shrub in the middle of the longer ones, brick corners."""
    w = S.w
    flowers = [("red_tulip", "orange_tulip", "pink_tulip"), ("cornflower", "azure_bluet", "allium"),
               ("oxeye_daisy", "dandelion", "white_tulip"), ("poppy", "orange_tulip", "red_tulip")][kind % 4]
    for dx in range(sx):
        for dz in range(sz):
            xx, zz = x + dx, z + dz
            edge = dx in (0, sx - 1) or dz in (0, sz - 1)
            w.set(xx, GY - 1, zz, "stone")
            w.set(xx, GY, zz, "bricks" if edge else "grass_block")
            if not edge:
                w.set(xx, GY + 1, zz, flowers[(dx + dz) % 3])
    if sx >= 4 or sz >= 4:
        w.set(x + sx // 2, GY + 1, z + sz // 2, "flowering_azalea")
    for dx in (0, sx - 1):
        for dz in (0, sz - 1):
            w.set(x + dx, GY + 1, z + dz, "bricks")
    S.occ[x - 1:x + sx + 1, z - 1:z + sz + 1] = True


def forecourt_dressing(S):
    """Foreground interest for the view west from the street back to the station and along the forecourt, all kept off the car's
    routes (the forecourt's south-east corner, x 74..98, z 129..146, stays empty): planters, a taxi rank with a lit sign, a bicycle rack,
    banners on the arcades, bollards at the plaza's edge."""
    w = S.w
    for i, (x, z, sx) in enumerate(((72, 120, 5), (84, 120, 5), (65, 121, 4), (60, 134, 4))):
        planter(S, x, z, sx, 3, i)
    # lamp posts flanking the walking line: vertical rhythm along the forecourt (north side all the way, south side only west of the
    # car's way)
    for (x, z) in ((64, 125), (72, 125), (80, 125), (88, 125), (62, 131), (68, 131)):
        for yy in range(GY, GY + 6):
            w.set(x, yy, z, "andesite_wall")
        w.set(x, GY + 6, z, "lantern[hanging=false]")
        S.occ[x, z] = True
    # taxi rank on the north side: bay lines first, then three yellow taxis under a lit sign
    for xx in range(69, 92):
        slab(w, xx, GY, 110, "smooth_sandstone")
        slab(w, xx, GY, 113, "smooth_sandstone")
    for xx in (70, 76, 83, 90):
        for zz in (111, 112):
            slab(w, xx, GY, zz, "smooth_sandstone")
    for x in (71, 78, 85):
        parked_car(w, x, GY, 111, "east", "yellow")
        w.set(x + 2, GY + 3, 111, "sea_lantern")                       # the lit roof sign of a taxi
    for yy in range(GY, GY + 5):                                       # the rank sign: a post, a blue board, a lamp
        w.set(68, yy, 114, "andesite_wall")
    w.fill(67, GY + 5, 114, 69, GY + 6, 114, "blue_concrete")
    w.set(68, GY + 7, 114, "sea_lantern")
    place_wall_sign(w, 68, GY + 6, 115, "south", [jp("タクシー"), "TAXI", "", ""], "birch")
    place_wall_sign(w, 68, GY + 6, 113, "north", [jp("タクシー"), "TAXI", "", ""], "birch")
    S.occ[66:93, 109:116] = True
    # a bicycle rack in front of the hall exit
    for z in (116, 118, 120, 122):
        bike(S, 60, z, "x")
    # banners on the arcade fronts (wall banners need a solid block behind them)
    cols = ["red", "blue", "yellow", "green", "orange", "cyan", "white", "purple"]
    k = 0
    for x in range(61, 90, 5):
        for (z, face, zb) in ((98, "south", 97), (158, "north", 159)):
            y = GY + 6
            bid = int(w.a[x, y, zb])
            nm = (w.palette[bid] or "") if bid > 1 else ""
            if any(t in nm for t in ("concrete", "terracotta", "calcite", "sandstone")) and "pane" not in nm:
                w.set(x, y, z, bs("%s_wall_banner" % cols[k % len(cols)], facing=face))
                k += 1
    # slim bollards along the plaza's edge toward the street
    for z in range(100, 156, 6):
        if z < 118 or z > 150:
            w.set(90, GY, z, "andesite_wall")
            slab(w, 90, GY + 1, z, "red_nether_brick")


def clutter(S):
    """Small things at eye level: potted plants and bins by the shop fronts, bollards at the crossing, curve mirrors."""
    w, rng = S.w, S.rng
    pots = ["potted_red_tulip", "potted_azure_bluet", "potted_cornflower", "potted_dandelion", "potted_poppy"]
    for x in (99, 105, 127, 136, 160, 166):
        w.set(x, GY, 119, rng.choice(pots))
    for x in (94, 103, 128, 140, 148, 156, 160, 171):
        w.set(x, GY, 137, rng.choice(pots))
    for x, z in ((97, 119), (133, 119), (163, 119), (98, 137), (137, 137), (170, 137)):
        w.set(x, GY, z, "cauldron")                                       # a grey bin
    for x in (95, 99):                                                    # bollards at the crossing, red and white
        for z in (122, 135):                                              # (south pair one cell in from the kerb: the car slides in past it)
            w.set(x, GY, z, "andesite_wall")                                   # slim bollards: they used to be fat red-and-white cubes
            w.set(x, GY + 1, z, "andesite_wall")
            slab(w, x, GY + 2, z, "red_nether_brick")
    for x, z in ((111, 98), (121, 155)):                                  # curve mirrors at the lane corners
        for dy in range(4):
            w.set(x, GY + dy, z, "andesite_wall")
        w.set(x, GY + 4, z, "orange_concrete")
        w.set(x + 1, GY + 4, z, "light_blue_stained_glass")
    # shop front plants and a few crates in the lanes
    for x in range(95, 106, 3):
        w.set(x, GY, 101, "barrel[facing=up]")
    for x in range(127, 140, 4):
        w.set(x, GY, 155, "barrel[facing=up]")


def pylon(S, cx, cz, H=30):
    """Lattice power pylon (iron-bars frame, three cross-arms). Legs reach down to the local ground. Returns arm tips."""
    w, T = S.w, S.T
    y0 = int(max(T[cx + dx, cz + dz] for dx in (-4, 4) for dz in (-4, 4))) + 1
    for lv in range(0, H + 1):
        hw = int(round(4 - 3 * lv / H))
        y = y0 + lv
        for sx in (-1, 1):
            for sz in (-1, 1):
                w.set(cx + sx * hw, y, cz + sz * hw, "iron_bars")
        if lv % 6 == 0 or lv == H:
            for t in range(-hw + 1, hw):
                for s in (-hw, hw):
                    w.set(cx + t, y, cz + s, "iron_bars[east=true,west=true]")
                    w.set(cx + s, y, cz + t, "iron_bars[north=true,south=true]")
    for sx in (-1, 1):                                       # legs down to the ground
        for sz in (-1, 1):
            lx, lz = cx + sx * 4, cz + sz * 4
            t = int(T[lx, lz])
            if t + 1 < y0:
                w.fill(lx, t + 1, lz, lx, y0 - 1, lz, "iron_bars")
    tips = []
    for k, ya in enumerate((y0 + H - 4, y0 + H - 9, y0 + H - 14)):
        for dz in range(-7, 8):
            w.set(cx, ya, cz + dz, "iron_bars[north=true,south=true]")
        tips.append([(cx, ya - 1, cz - 7), (cx, ya - 1, cz + 7)])
    for dy in range(1, 5):
        w.set(cx, y0 + H + dy, cz, "iron_bars")
    w.set(cx, y0 + H + 5, cz, "lightning_rod[facing=up]")
    S.keep[cx - 6:cx + 7, cz - 6:cz + 7] = True
    return tips


def pylons(S):
    spots = [(34, 223), (92, 213), (150, 205), (206, 198)]
    tips = [pylon(S, x, z) for x, z in spots]
    for a, b in zip(tips, tips[1:]):
        for ka in range(3):
            for side in range(2):
                pa, pb = a[ka][side], b[ka][side]
                chain_line(S.w, pa[0], pa[1], pa[2], pb[0], pb[1], pb[2], sag=3.5)
    # a short northern pair beyond the north-west hills
    spots = [(48, 57), (112, 50)]
    tips = [pylon(S, x, z, 26) for x, z in spots]
    for ka in range(3):
        for side in range(2):
            pa, pb = tips[0][ka][side], tips[1][ka][side]
            chain_line(S.w, pa[0], pa[1], pa[2], pb[0], pb[1], pb[2], sag=3.0)


def keep_clear(S):
    """Cells where no trees or grass clutter may stand: the angel's corridor, the view from the ridge, anchors."""
    X, Z = np.meshgrid(np.arange(N), np.arange(N), indexing="ij")
    S.keep |= (X > 168) & (Z > 94) & (Z < 162) & (X < 232)
    # sight cone from the ridge to the sea gap
    a = np.array(RIDGE, float)
    b = np.array([230.0, 128.0])
    d = b - a
    L = np.hypot(*d)
    tt = np.clip(((X - a[0]) * d[0] + (Z - a[1]) * d[1]) / L ** 2, 0, 1)
    dist = np.hypot(X - (a[0] + tt * d[0]), Z - (a[1] + tt * d[1]))
    S.keep |= dist < 14
    S.keep[168:210, 40:68] = True                      # the lookout bench
    S.keep[164:200, 30:60] |= True


def vegetation(S):
    """Forest on the hills (cedar on the heights, oak and birch below), grass tufts and a few wild flowers."""
    w, rng, T = S.w, S.rng, S.T
    gy, gx = np.gradient(T.astype(float))
    slope = np.hypot(gx, gy)
    grass_id = w._id("grass_block")
    for x in range(2, N - 2, 3):
        for z in range(2, N - 2, 3):
            x2, z2 = x + rng.randint(-1, 1), z + rng.randint(-1, 1)
            if S.keep[x2, z2] or S.occ[x2, z2] or S.wet[x2, z2] or w.a[x2, T[x2, z2], z2] != grass_id:
                continue
            t = int(T[x2, z2])
            if slope[x2, z2] > 1.7:
                continue
            p = 0.62 if t > 44 else (0.34 if t > 34 else 0.12)
            if x2 < 14 or z2 < 66 or z2 > 190:
                p = max(p, 0.5)
            if rng.random() > p:
                continue
            kind = "cedar" if (t > 48 and rng.random() < 0.7) or rng.random() < 0.15 else rng.choice(["oak", "oak", "birch"])
            tree(S, x2, t + 1, z2, kind)
            S.keep[x2 - 1:x2 + 2, z2 - 1:z2 + 2] = True
    # grass and flowers on any open grass
    flowers = ["dandelion", "poppy", "cornflower", "azure_bluet", "oxeye_daisy"]
    for x in range(N):
        for z in range(N):
            if S.keep[x, z] or S.occ[x, z] or S.wet[x, z]:
                continue
            t = int(T[x, z])
            if w.a[x, t, z] != grass_id or w.a[x, t + 1, z] > 1:
                continue
            r = rng.random()
            if r < 0.10:
                w.set(x, t + 1, z, "short_grass")
            elif r < 0.125:
                w.set(x, t + 1, z, "tall_grass[half=lower]")
                w.set(x, t + 2, z, "tall_grass[half=upper]")
            elif r < 0.135:
                w.set(x, t + 1, z, rng.choice(flowers))


def anchors(S):
    w, T = S.w, S.T
    A = w.anchor

    def y_at(x, z):
        return surface_y(S, int(x), int(z))
    A("start", 37.5, PLAT_TOP + 1, 128.5, yaw=YAW["east"])
    A("phone", S.phone[0], S.phone[1], S.phone[2], yaw=YAW["north"])
    A("phone_use", S.stand[0], S.stand[1], S.stand[2], yaw=YAW["north"])
    A("street", 93.5, GY, 128.5, yaw=YAW["east"])
    A("vision", 133.5, GY, 128.5, yaw=YAW["west"])
    A("crash", 84.5, GY + 0.5, 142.5, yaw=YAW["west"])
    A("car_arrive", 97.5, GY, 131.0, yaw=YAW["east"])
    A("car_seat", 97.5, GY, 130.5, yaw=YAW["east"])
    rx, rz = RIDGE
    A("ridge", rx + 0.5, y_at(rx, rz), rz + 0.5, yaw=-26.6)
    A("ridge_blast", rx - 14.5, y_at(rx - 15, rz), rz + 0.5, yaw=-26.6)
    A("angel_spawn", 228.5, 31, 128.5, yaw=YAW["west"])
    for i, x in enumerate((212.5, 196.5, 184.5, 174.5), 1):
        A("angel_walk_%d" % i, x, max(31, int(T[int(x), 128]) + 1), 128.5, yaw=YAW["west"])
    A("gate", 190.5, HOLLOW_Y, 31.5, yaw=YAW["north"])
    A("cartrain", 191.5, HOLLOW_Y, 15.5, yaw=YAW["north"])


# <<SCENE4>>

# ============================================================================================= build
def dirt_under_cover(w):
    """Grass, podzol and mycelium with a solid block on top turn to dirt in the game, so draw them as dirt: the canvas
    then shows what the game will (under roads and buildings nobody sees the difference).  Same test as build.py:
    a full cube above, not glass or ice."""
    import compile as comp                      # tools/world is on sys.path (build.py and main() both put it there)
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


def build(w, with_car=False):
    """Build the whole set into World `w`. with_car=True also draws the heroine's coupe at anchor "car_arrive"."""
    S = Site(w)
    terrain(S)
    lay_terrain(S)
    cutting(S)
    platform(S)
    canopy(S)
    hall(S)
    train(S)
    catenary(S)
    platform_furniture(S)
    road_paint(S)
    hill_road(S)
    lookout(S)
    tunnel(S)
    hall_lighting(S)
    lanes_and_lots(S)
    street_scene(S, with_car)
    forecourt_dressing(S)
    clutter(S)
    pylons(S)
    keep_clear(S)
    vegetation(S)
    dirt_under_cover(w)
    anchors(S)
    return S


# ============================================================================================= dev tools
_COLORS = (
    ("tinted_glass", (50, 52, 62)), ("light_blue_stained_glass", (150, 200, 235)), ("stained_glass", (170, 200, 215)), ("glass", (190, 225, 235)),
    ("water", (50, 110, 190)), ("sea_lantern", (210, 235, 225)), ("iron_door", (200, 200, 205)),
    ("iron_trapdoor", (150, 150, 155)), ("iron_bars", (120, 120, 125)), ("iron_chain", (60, 60, 65)),
    ("rail", (130, 100, 80)), ("black_concrete", (25, 26, 30)), ("light_gray_concrete", (150, 150, 145)),
    ("gray_concrete", (60, 64, 68)), ("white_concrete", (225, 225, 220)), ("blue_concrete", (45, 70, 160)),
    ("light_blue_concrete", (80, 160, 210)), ("red_concrete", (170, 40, 35)), ("yellow_concrete", (235, 195, 40)),
    ("orange_concrete", (225, 110, 20)), ("green_concrete", (70, 120, 40)), ("lime_concrete", (110, 180, 30)),
    ("cyan_concrete", (30, 130, 150)), ("brown_concrete", (100, 65, 40)), ("pink_concrete", (215, 120, 160)),
    ("purple_concrete", (110, 45, 160)), ("magenta_concrete", (180, 60, 170)),
    ("grass_block", (100, 150, 60)), ("short_grass", (95, 150, 55)), ("tall_grass", (95, 150, 55)), ("fern", (80, 135, 55)),
    ("leaves", (50, 110, 40)), ("spruce_log", (60, 45, 30)), ("log", (100, 80, 50)), ("podzol", (95, 70, 40)),
    ("coarse_dirt", (115, 85, 60)), ("dirt", (120, 90, 65)), ("sandstone", (215, 200, 150)), ("sand", (220, 205, 155)),
    ("gravel", (130, 125, 120)), ("deepslate_tile", (55, 55, 58)), ("deepslate", (70, 70, 74)),
    ("polished_andesite", (135, 135, 135)), ("andesite", (125, 125, 125)), ("polished_diorite", (200, 200, 200)),
    ("diorite", (190, 190, 190)), ("smooth_stone", (160, 160, 160)), ("stone_brick", (120, 120, 120)), ("stone", (120, 120, 120)),
    ("calcite", (225, 225, 220)), ("quartz", (232, 228, 220)), ("terracotta", (150, 90, 60)), ("planks", (170, 135, 85)),
    ("wool", (200, 200, 200)), ("prismarine", (50, 110, 100)), ("lantern", (240, 200, 110)), ("barrel", (140, 105, 60)),
    ("moss", (90, 120, 50)), ("copper", (80, 160, 130)), ("tuff", (110, 110, 100)), ("mud", (110, 80, 60)),
    ("sign", (150, 120, 70)), ("fence", (140, 110, 70)), ("wall", (130, 130, 130)), ("lightning_rod", (200, 120, 70)),
    ("end_rod", (230, 230, 230)), ("iron_block", (200, 200, 200)), ("cauldron", (60, 60, 60)), ("flower", (230, 90, 120)),
    ("poppy", (200, 30, 30)), ("dandelion", (240, 220, 40)), ("cornflower", (70, 100, 220)), ("banner", (230, 230, 230)),
    ("dark_oak", (70, 50, 32)), ("birch", (205, 190, 140)), ("oak", (160, 130, 80)), ("acacia", (170, 90, 50)), ("warped", (40, 120, 110)),
    ("crimson", (110, 40, 60)), ("cherry", (225, 170, 175)), ("jungle", (150, 110, 70)), ("mangrove", (120, 50, 45)),
    ("polished_blackstone", (58, 54, 62)), ("smooth_sandstone", (225, 210, 160)), ("bricks", (150, 80, 60)), ("white_terracotta", (210, 180, 165)),
    ("campfire", (90, 70, 50)), ("lectern", (150, 120, 70)), ("composter", (110, 80, 50)), ("bell", (230, 190, 40)),
)


def _rgb(name):
    n = name.replace("minecraft:", "").split("[")[0]
    for key, rgb in _COLORS:
        if key in n:
            return rgb
    return (200, 80, 200)


_THIN = ("glass", "bars", "chain", "rail", "carpet", "short_grass", "tall_grass", "fern", "poppy", "dandelion", "cornflower", "allium",
         "bluet", "tulip", "sign", "vine", "lever", "button", "lantern", "end_rod", "lightning_rod", "water", "banner",
         "trapdoor", "door", "pressure_plate", "torch", "sapling", "flower", "kelp", "seagrass", "lily", "barrier")


def see_through(name):
    if name is None:
        return True
    n = name.replace("minecraft:", "")
    return n == "air" or n.startswith("light[") or (any(t in n for t in _THIN) and n != "tinted_glass")


def _opaque_table(w):
    return np.array([False, False] + [not see_through(b) for b in w.palette[2:]], dtype=bool)


def march(w, eye, d, maxd=400.0, opaque=None):
    """Voxel ray walk from `eye` along unit vector d. Returns (hit cell or None, distance travelled, None)."""
    if opaque is None:
        opaque = _opaque_table(w)
    pos = np.array(eye, float)
    cell = np.floor(pos).astype(int)
    step = np.where(d > 0, 1, -1)
    with np.errstate(divide="ignore", invalid="ignore"):
        tdelta = np.where(d != 0, np.abs(1.0 / d), 1e30)
        nxt = np.where(d > 0, cell + 1 - pos, pos - cell)
        tmax = np.where(d != 0, nxt * tdelta, 1e30)
    t = 0.0
    while t < maxd:
        i = int(np.argmin(tmax))
        t = tmax[i]
        cell[i] += step[i]
        tmax[i] += tdelta[i]
        if cell[1] >= w.size[1]:
            return None, t, None                 # left through the top: nothing can block any more
        if w.inside(*cell) and opaque[w.a[cell[0], cell[1], cell[2]]]:
            nm = w.palette[w.a[cell[0], cell[1], cell[2]]] or ""
            if "_slab[type=bottom" in nm and eye[1] + d[1] * t - cell[1] >= 0.5:      # a ray entering over the half block passes it
                continue
            return cell.copy(), t, None
    return None, maxd, None


def sightline(w, a, b, opaque=None):
    """True if the straight line from point a to point b (local coordinates) is not blocked by an opaque block."""
    a, b = np.array(a, float), np.array(b, float)
    d = b - a
    L = float(np.linalg.norm(d))
    hit, t, _ = march(w, a, d / L, maxd=L, opaque=opaque)
    return (hit is None or t >= L - 1e-6), (None if hit is None else tuple(int(v) for v in hit), t)


def render_view(w, eye, yaw, pitch, path, fov=80.0, size=(480, 270), maxd=360.0):
    """Perspective render of the voxel set (face-shaded, fogged, glass and water translucent) for eye-level checks."""
    from PIL import Image
    wpx, hpx = size
    names = w.palette
    col = np.array([(0, 0, 0), (0, 0, 0)] + [_rgb(b) for b in names[2:]], dtype=np.float32)
    clear = np.array([True, True] + [see_through(b) for b in names[2:]])
    glassy = np.array([False, False] + [("glass" in b and "pane" not in b) or "water" in b or "pane" in b for b in names[2:]])
    yr, pr = math.radians(yaw), math.radians(pitch)
    # Minecraft yaw 0 looks +z, yaw -90 looks +x
    fwd = np.array([-math.sin(yr) * math.cos(pr), -math.sin(pr), math.cos(yr) * math.cos(pr)])
    right = np.array([-math.cos(yr), 0.0, -math.sin(yr)])
    up = np.cross(right, fwd)
    up = up if up[1] > 0 else -up
    aspect = wpx / hpx
    th = math.tan(math.radians(fov) / 2)
    us = (np.arange(wpx) + 0.5) / wpx * 2 - 1
    vs = 1 - (np.arange(hpx) + 0.5) / hpx * 2
    U, V = np.meshgrid(us * th * aspect, vs * th)
    dirs = fwd[None, None, :] + U[..., None] * right[None, None, :] + V[..., None] * up[None, None, :]
    dirs = dirs.reshape(-1, 3)
    dirs /= np.linalg.norm(dirs, axis=1)[:, None]
    n = dirs.shape[0]
    pos = np.tile(np.array(eye, float), (n, 1))
    cell = np.floor(pos).astype(np.int64)
    step = np.where(dirs > 0, 1, -1)
    with np.errstate(divide="ignore"):
        tdelta = np.where(dirs != 0, np.abs(1.0 / dirs), 1e30)
    nxt = np.where(dirs > 0, cell + 1 - pos, pos - cell)
    tmax = np.where(dirs != 0, nxt * tdelta, 1e30)
    sky = np.array([170, 205, 240], np.float32)
    acc = np.zeros((n, 3), np.float32)
    trans = np.ones(n, np.float32)
    done = np.zeros(n, bool)
    final = np.tile(sky, (n, 1))
    tcur = np.zeros(n)
    sx, sy, sz = w.size
    for _ in range(int(maxd * 3)):
        act = np.nonzero(~done)[0]
        if act.size == 0:
            break
        tm = tmax[act]
        ax = np.argmin(tm, axis=1)
        t = tm[np.arange(act.size), ax]
        tcur[act] = t
        c = cell[act]
        c[np.arange(act.size), ax] += step[act, ax]
        cell[act] = c
        tmax[act, ax] += tdelta[act, ax]
        out = (c[:, 0] < 0) | (c[:, 0] >= sx) | (c[:, 2] < 0) | (c[:, 2] >= sz) | (c[:, 1] < 0) | (c[:, 1] >= sy)
        far = t > maxd
        inb = ~out
        ids = np.zeros(act.size, np.int64)
        ids[inb] = w.a[c[inb, 0], c[inb, 1], c[inb, 2]]
        hit = inb & (ids > 1) & ~clear[ids]
        gl = inb & (ids > 1) & glassy[ids]
        if gl.any():
            gi = act[gl]
            fogg = np.exp(-t[gl] / 260.0)[:, None]
            tint = col[ids[gl]] * fogg + sky * (1 - fogg)
            acc[gi] += trans[gi][:, None] * 0.38 * tint
            trans[gi] *= 0.62
        if hit.any():
            hi = act[hit]
            shade = np.where(ax[hit] == 1, np.where(step[hi, 1] < 0, 1.0, 0.55), np.where(ax[hit] == 0, 0.8, 0.68))
            base = col[ids[hit]] * shade[:, None]
            fogg = np.exp(-t[hit] / 260.0)[:, None]
            final[hi] = base * fogg + sky * (1 - fogg)
            done[hi] = True
        done[act[far | (out & (c[:, 1] >= sy))]] = True
        # leaving the box sideways or below: stop (void)
        done[act[out & ~(c[:, 1] >= sy)]] = True
    img = acc + trans[:, None] * final
    img = np.clip(img, 0, 255).astype(np.uint8).reshape(hpx, wpx, 3)
    Image.fromarray(img).resize((wpx * 2, hpx * 2), Image.NEAREST).save(path)


def plan_view(w, path, x0=0, x1=256, z0=0, z1=256, scale=4):
    """Top-down plan with real block colours, cropped; a fresh look at layout rather than at height."""
    from PIL import Image
    sub = w.a[x0:x1, :, z0:z1]
    solid = (sub > 1)
    col = np.array([(0, 0, 0), (0, 0, 0)] + [_rgb(b) for b in w.palette[2:]], dtype=np.float32)
    h = sub.shape[1] - 1 - np.argmax(solid[:, ::-1, :], axis=1)
    ids = np.take_along_axis(sub, h[:, None, :], axis=1)[:, 0, :]
    img = np.where(solid.any(axis=1)[..., None], col[ids] * np.clip(0.45 + 0.55 * (h - 28) / 36.0, 0.35, 1.15)[..., None], 0)
    Image.fromarray(np.clip(img, 0, 255).astype(np.uint8).transpose(1, 0, 2)).resize(((x1 - x0) * scale, (z1 - z0) * scale), Image.NEAREST).save(path)


def slice_view(w, path, axis, at, a0=0, a1=256, y0=20, y1=110, scale=6):
    """A vertical cut with real colours: axis 'z' cuts at z = at (x across), axis 'x' cuts at x = at (z across)."""
    from PIL import Image
    sub = w.a[a0:a1, y0:y1, at] if axis == "z" else w.a[at, y0:y1, a0:a1].T
    col = np.array([(235, 244, 252), (235, 244, 252)] + [_rgb(b) for b in w.palette[2:]], dtype=np.float32)
    img = col[sub].transpose(1, 0, 2)[::-1]
    Image.fromarray(img.astype(np.uint8)).resize(((a1 - a0) * scale, (y1 - y0) * scale), Image.NEAREST).save(path)


def validate(w):
    """Check every block id in the palette against the 26.3 block report; returns the list of problems."""
    import json
    path = r"D:\genesis-vr\work\mcdata\out\reports\blocks.json"
    if not os.path.exists(path):
        return ["blocks.json not found"]
    rep = json.load(open(path))
    bad = []
    for b in w.palette[1:]:
        name, _, rest = b.partition("[")
        if name not in rep:
            bad.append(b)
            continue
        props = rep[name].get("properties", {})
        if rest:
            for kv in rest.rstrip("]").split(","):
                k, _, v = kv.partition("=")
                if k not in props or v not in props[k]:
                    bad.append(b)
                    break
    return bad


def void_check(w, eye, step_deg=3.0):
    """Cast a sphere of rays from `eye`; return (fraction, worst direction) of DOWNWARD-looking rays that leave the
    set through its sides or bottom without hitting a block, i.e. directions in which the player would see the void."""
    opaque = _opaque_table(w)
    sx, sy, sz = w.size
    bad = []
    total = 0
    for pit in np.arange(0.5, 60.1, step_deg):                       # Minecraft pitch: positive looks down
        for yaw in np.arange(-180.0, 180.0, step_deg):
            yr, pr = math.radians(yaw), math.radians(pit)
            d = np.array([-math.sin(yr) * math.cos(pr), -math.sin(pr), math.cos(yr) * math.cos(pr)])
            hit, t, _ = march(w, eye, d, maxd=600.0, opaque=opaque)
            total += 1
            if hit is None:
                bad.append((yaw, pit))
    return len(bad) / max(1, total), bad


def bay_check(w, up=1.62, yaw_span=4.0, pitch_max=3.0):
    """Rays from the 'street' eye toward the bay, yaw within +-yaw_span degrees of east, pitch 0..pitch_max degrees below the horizon
    (the street is only 11 wide, so that is the window the buildings leave): every ray must end on the water (or its edge barrier) or
    leave the set over water - never on a hill, a tree or a building.  Returns (rays, failures[(yaw_off, pitch, cell, block)])."""
    ox, oy, oz = w.origin
    a = w.anchors["street"]
    eye = np.array([a["x"] - ox, a["y"] - oy + up, a["z"] - oz])
    op = np.array([False, False] + [not (b is None or b.replace("minecraft:", "") == "air") for b in w.palette[2:]])
    # solid for this test: everything that is not air or a plant-like thin thing; water and the barrier count as the sea
    thin = ("short_grass", "tall_grass", "fern", "dandelion", "poppy", "cornflower", "azure_bluet", "oxeye_daisy", "allium", "lily_pad",
            "iron_bars", "chain", "glass_pane", "end_rod", "lantern", "sign")
    op = np.array([False, False] + [not any(t in b for t in thin) for b in w.palette[2:]])
    fails, n = [], 0
    for dy in np.arange(-yaw_span, yaw_span + 0.01, 1.0):
        for pit in np.arange(0.0, pitch_max + 0.01, 0.5):
            yr, pr = math.radians(-90.0 + dy), math.radians(pit)
            d = np.array([-math.sin(yr) * math.cos(pr), -math.sin(pr), math.cos(yr) * math.cos(pr)])
            hit, t, _ = march(w, eye, d, maxd=400.0, opaque=op)
            n += 1
            if hit is None:
                continue
            nm = (w.palette[w.a[tuple(hit)]] or "").replace("minecraft:", "")
            if nm.startswith("water") or nm == "barrier":
                continue
            if hit[0] < 185:            # a steeper ray dips onto the street or the promenade before the sea: the town, not a hill
                continue
            fails.append((float(dy), float(pit), tuple(int(v) for v in hit), nm))
    return n, fails


def checks(w):
    """Eye-level sightline checks from the anchors, in local coordinates; prints and returns a list of (label, ok, hit)."""
    ox, oy, oz = w.origin
    A = {k: np.array([v["x"] - ox, v["y"] - oy, v["z"] - oz]) for k, v in w.anchors.items()}
    eye = np.array([0, 1.62, 0])
    opaque = _opaque_table(w)
    res = []

    def check(label, a, b):
        ok, info = sightline(w, a, b, opaque)
        res.append((label, ok, info))
        print("  %-52s %s %s" % (label, "clear" if ok else "BLOCKED", "" if ok else "at %s after %.1f" % info))
    s = A["start"] + eye
    check("start -> hall exit (53.5, 34.6, 128.5)", s, (53.5, 34.6, 128.5))
    check("start -> street anchor head height", s, A["street"] + eye)
    check("start -> vision head height (far end of the street)", s, A["vision"] + eye)
    st = A["street"] + eye
    for lab, dy in (("head", 1.7), ("chest", 1.2), ("feet", 0.2)):
        check("street -> vision girl (%s)" % lab, st, A["vision"] + np.array([0, dy, 0]))
    check("street -> angel_spawn +40", st, A["angel_spawn"] + np.array([0, 40, 0]))
    r = A["ridge"] + eye
    for h in (60, 40, 20, 8, 1):
        check("ridge -> angel_spawn +%d" % h, r, A["angel_spawn"] + np.array([0, h, 0]))
    for i in range(1, 5):
        check("ridge -> angel_walk_%d +30" % i, r, A["angel_walk_%d" % i] + np.array([0, 30, 0]))
    check("ridge -> ridge_blast (car on the bench)", r, A["ridge_blast"] + np.array([0, 1.0, 0]))
    check("phone_use -> phone front face", A["phone_use"] + eye, A["phone"] + np.array([0, 0.2, 0.6]))
    check("street -> crash site", st, A["crash"] + np.array([0, 3, 0]))
    check("street -> car_arrive", st, A["car_arrive"] + np.array([0, 1.0, 0]))
    check("gate -> gate opening (190.5, 48, 22.5)", A["gate"] + eye, (190.5, 48, 22.5))
    check("gate -> cartrain platform", A["gate"] + eye, A["cartrain"] + eye)
    return res


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(here))
    from voxel import World, preview
    from layout import SETS
    origin, size = SETS["outskirts"]
    w = World("outskirts", origin, size)
    S = build(w)
    out = os.path.join(os.path.dirname(here), "preview", "outskirts")
    os.makedirs(out, exist_ok=True)
    bad = validate(w)
    print("palette", len(w.palette) - 1, "blocks; invalid:", bad)
    print("anchors:")
    for k, v in sorted(w.anchors.items()):
        print("  %-14s x=%-7s y=%-7s z=%-7s yaw=%s" % (k, v["x"] - origin[0], v["y"] - origin[1], v["z"] - origin[2], v["yaw"]))
    print("sightline checks:")
    checks(w)
    n_rays, fails = bay_check(w)
    print("bay check (street eye, yaw east +-4, pitch 0..-3: every ray must end on the sea or leave over it): %d rays, %d fail" % (n_rays, len(fails)))
    for f in fails[:6]:
        print("   FAIL", f)
    print("void checks (fraction of downward rays that leave the set):")
    for n in ("start", "street", "vision", "phone_use", "crash", "car_seat", "ridge", "ridge_blast", "gate", "cartrain", "angel_walk_4"):
        A = w.anchors[n]
        f, bad = void_check(w, (A["x"] - origin[0], A["y"] - origin[1] + 1.62, A["z"] - origin[2]), 5.0)
        print("  %-14s %.3f" % (n, f))
    preview(w, os.path.join(out, "top.png"), "y")
    plan_view(w, os.path.join(out, "plan_full.png"), scale=4)
    plan_view(w, os.path.join(out, "plan_town.png"), 40, 200, 80, 180, 6)
    plan_view(w, os.path.join(out, "plan_ridge_tunnel.png"), 150, 230, 0, 100, 8)
    slice_view(w, os.path.join(out, "slice_station_z128.png"), "z", 128, 0, 100, 25, 62, 9)
    slice_view(w, os.path.join(out, "slice_street_x125.png"), "x", 125, 90, 170, 25, 62, 9)
    slice_view(w, os.path.join(out, "slice_street_z125.png"), "z", 125, 85, 190, 25, 62, 8)
    slice_view(w, os.path.join(out, "slice_tunnel_x190.png"), "x", 190, 0, 60, 30, 80, 12)
    A = w.anchors
    eyes = (("eye_start_east", "start", None, 0, 100), ("eye_street_east", "street", None, 0, 75),
            ("eye_street_back", "street", 90.0, 0, 100), ("eye_phone_use", "phone_use", None, 0, 90),
            ("eye_ridge_sea", "ridge", -16.0, 14, 100), ("eye_gate", "gate", None, 6, 85),
            ("eye_cartrain", "cartrain", None, 0, 100), ("eye_angel_walk_1_to_town", "angel_walk_1", None, 0, 80))
    for name, anc, yaw, pitch, fov in eyes:
        a = A[anc]
        render_view(w, (a["x"] - origin[0], a["y"] - origin[1] + 1.62, a["z"] - origin[2]), a["yaw"] if yaw is None else yaw,
                    pitch, os.path.join(out, name + ".png"), fov=fov)
    return w, S


if __name__ == "__main__":
    main()








