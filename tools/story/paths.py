"""The drivable paths of scenes 1-3, derived from the sets' roads (tools/world/sets/outskirts.py HILL_ROAD, the main street, the portal
forecourt; geofront.py's rail line P) with heights read from the built voxel worlds, so that a car never floats or sinks.

Every route is a Route (movers.py): frames of (x, y, z, yaw, pitch), one per tick.  The checker (sim.py) replays them against the voxel
worlds frame by frame.
"""
import math

import numpy as np

from motion import Path, arc, catmull, join, line

# the hill road's waypoints in the outskirts set (copied from sets/outskirts.py HILL_ROAD: x, z, local feet y); the set's own x, z are
# already absolute because the set's origin is x = 0, z = 0.
HILL_ROAD_XZ = [(148, 128), (148, 108), (154, 94), (168, 86), (184, 80), (198, 72), (204, 62), (194, 56), (186, 52), (172, 46), (170, 36),
                (182, 32), (192, 32), (192, 40)]


def tracked_surface(probe, xz, y_ref, up=1.6, down=8):
    """Standing-surface height under each (x, z), continuity-tracked from y_ref.  Returns (raw heights, warnings)."""
    raw, warns = [], []
    ref = y_ref
    for (x, z) in xz:
        y = probe.surface(x, z, ref, up=up, down=down)
        if y is None:
            warns.append(f"no surface under ({x:.1f}, {z:.1f}) near y {ref:.1f}")
            y = ref
        raw.append(y)
        ref = y
    return np.array(raw), warns


def axle_mean(raw, k, light=2):
    """Height of the model's centre for a rigid body resting on two contact points k samples ahead and behind, then lightly smoothed.
    At the ends the missing side is taken from the other (the ground there is the ground at the end)."""
    n = len(raw)
    hi = np.minimum(np.arange(n) + k, n - 1)
    lo = np.maximum(np.arange(n) - k, 0)
    y = 0.5 * (raw[hi] + raw[lo])
    if light:
        y = np.convolve(np.pad(y, light, mode="edge"), np.ones(2 * light + 1) / (2 * light + 1), mode="valid")
    return y


def grounded(probe, xz, y_ref, axle=2.0, step=0.5, up=1.6):
    """A path (x, y, z) that follows the ground the way a car does: the centre rides at the mean height of the ground under the two
    axles `axle` blocks ahead of and behind it (the pitch then follows from the path's slope over the same distance)."""
    base = Path([(x, 0.0, z) for x, z in xz])
    n = int(base.L / step) + 1
    pts = [base.pos(i * base.L / (n - 1)) for i in range(n)]
    sxz = [(p[0], p[2]) for p in pts]
    raw, warns = tracked_surface(probe, sxz, y_ref, up=up)
    y = axle_mean(raw, int(round(axle / (base.L / (n - 1)))))
    steps = np.abs(np.diff(raw)).max() if len(raw) > 1 else 0
    if steps > 1.25:
        i = int(np.argmax(np.abs(np.diff(raw))))
        warns.append(f"the ground steps by {steps:.2f} blocks at ({sxz[i][0]:.1f}, {sxz[i][1]:.1f}): too abrupt for a car")
    return [(p[0], float(yy), p[2]) for p, yy in zip(pts, y)], warns


def xz_of(pts):
    return [(p[0], p[2]) for p in pts]


def flat(xz_points):
    return [(x, 0.0, z) for x, z in xz_points]


# --------------------------------------------------------------------------------------------------- scene 1: the car slides in
def slide_in_xz(ctx):
    a = ctx.anchor("outskirts.car_arrive")
    ex, ez = a["x"], a["z"]
    # out of the smoke on the forecourt, across the pavement edge into the street, stopping at the anchor
    pts = catmull([(76.0, 0, 141.0), (84.0, 0, 137.0), (91.5, 0, 133.0), (ex, 0, ez), (ex + 7.0, 0, ez)], 0.5)
    out = []
    for p in pts:
        out.append((p[0], p[2]))
        if p[0] >= ex - 1e-6:
            break
    out[-1] = (ex, ez)
    return out


# --------------------------------------------------------------------------------------------------- scene 2: town to ridge
def to_ridge_xz(ctx):
    a = ctx.anchor("outskirts.car_arrive")
    town = catmull([(a["x"], 0, a["z"]), (100.0, 0, 129.8), (103.0, 0, 128.5), (108.0, 0, 128.3), (116.0, 0, 128.3), (124.0, 0, 128.3), (136.0, 0, 128.3)], 0.5)
    turn = arc(136.0, 116.3, 12.0, 90.0, 0.0, 0.0)
    north = line((148.0, 0, 116.3), (148.0, 0, 108.0))
    hill = catmull([(x, 0, z) for x, z in HILL_ROAD_XZ[1:8]], 0.5)     # (148,108) ... (194,56)
    return xz_of(join(town, turn, north, hill))


def ridge_to_gate_xz(ctx):
    a = ctx.anchor("outskirts.ridge_blast")
    g = ctx.anchor("outskirts.gate")
    start = [(a["x"], 0, a["z"]), (181.5, 0, 53.6), (180.0, 0, 50.8), (176.5, 0, 49.2), (173.5, 0, 48.9), (171.3, 0, 47.6), (170.4, 0, 45.0),
             (170.2, 0, 41.5), (170.6, 0, 38.2), (173.0, 0, 36.4), (177.0, 0, 35.4), (181.5, 0, 35.8), (186.0, 0, 36.0)]
    head = catmull(start, 0.5)
    turn = arc(186.0, g["z"], 4.5, 90.0, 0.0, 0.0)
    # the turn runs from (186, g.z + 4.5) to (186 + 4.5, g.z) = (190.5, g.z), left, ending heading north
    return xz_of(join(head, turn))


def gate_to_cartrain_xz(ctx):
    g = ctx.anchor("outskirts.gate")
    c = ctx.anchor("outskirts.cartrain")
    return xz_of(catmull([(g["x"], 0, g["z"]), (g["x"] + 0.2, 0, g["z"] - 7.0), (c["x"] - 0.4, 0, c["z"] + 8.0), (c["x"], 0, c["z"])], 0.5))


# --------------------------------------------------------------------------------------------------- scene 3: the geofront rail line
def geofront_line(ctx, bogie=2.8):
    """(x, y_feet, z, dist) along the rail line, one sample per half block: y is the standing height on the wagon bed (deck + 1), as a rigid
    wagon riding on two bogies `bogie` blocks ahead of and behind its centre."""
    probe = ctx.probe("geofront")
    g = probe.built
    P = g.P
    ox, oy, oz = probe.o
    xs = P["x"] + ox
    zs = P["z"] + oz
    hq = P["hq"]
    warns = []
    raw = []
    for x, z, h in zip(xs, zs, hq):
        y = probe.surface(x, z, h + 0.5, up=0.9, down=4)
        if y is None:
            y = float(h)
            warns.append(f"geofront: no deck under ({x:.1f}, {z:.1f})")
        raw.append(y)
    raw = np.array(raw)
    ys = axle_mean(raw, int(round(bogie / 0.5)), light=3) + 1.0
    return xs, ys, zs, np.array(P["dist"]), warns, g
