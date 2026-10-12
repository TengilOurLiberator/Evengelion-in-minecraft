"""The rail wagon the car rides: a flat steel deck (5 wide, 9 long, deck at y 0, bed 1.0 deep) with hazard-striped edges, tread plate, bogies with spoked wheels,
couplers with buffers, tie-down rings and chocks, a tubular rail on the sides and the front (left out on the low side), a low striped kerb on the open
side, a lamp on the front-left corner and a loading ramp.

Authored in the wagon's rig space (+x left, +z forward).  Left/right and front/back variants are separate models built with a mirrored builder; the
parts carry flags (`only`) so that wagon_parts(ramp, low_side) can pick the ones it needs.
"""
import math

import numpy as np

from . import car_paint as cp
from . import paint as pt
from .car import PartSpec, Vehicle
from .mdl import Model, Sheet
from .paint import edge_fx, fbm, grain, mix, rgb, smooth, vnoise, white_noise
from .shapes import Bld
from .vmath import rax
from functools import partial

DECK_Z = (-4.5, 4.5)
HALF_W = 2.5


def S(f, **k):
    return partial(f, **k)


# ---------------------------------------------------------------------------------------------------- painters
def tread_plate(ctx, base="#5b6670", seed=21, **kw):
    """Steel deck: diamond tread plate, wear paths and oil stains."""
    x, z = ctx.P[..., 0], ctx.P[..., 2]
    c = np.broadcast_to(rgb(base), (ctx.h, ctx.w, 3)).copy()
    u, v = (x + z) / 0.16, (x - z) / 0.16
    fu, fv = np.mod(u, 1.0), np.mod(v, 1.0)
    d = np.minimum(np.abs(fu - 0.5), np.abs(fv - 0.5))
    bump = smooth(0.34, 0.1, np.abs(fu - 0.5) + np.abs(fv - 0.5) - 0.2)
    c = c * (0.78 + 0.34 * bump)[..., None]
    n = fbm(ctx.P, 2.5, seed, 4)
    c = c * (0.75 + 0.5 * n)[..., None]
    wear = smooth(0.55, 0.9, fbm(ctx.P, 5.0, seed + 3, 3))
    c = mix(c, rgb("#8d949a"), 0.35 * wear)
    oil = smooth(0.64, 0.78, fbm(ctx.P, 3.0, seed + 8, 3))
    c = c * (1 - 0.45 * oil)[..., None]
    c = c * (1 - 0.2 * white_noise(ctx, seed))[..., None]
    return np.clip(c, 0, 1)


def hazard_world(ctx, a="#e8b81c", b="#1b1b1b", w=0.32, seed=22, dirt=0.4, **kw):
    """Hazard stripes by world position (so the stripes run through neighbouring pieces without a seam)."""
    x, z = ctx.P[..., 0], ctx.P[..., 2]
    s = np.mod((z + x) / (2 * w), 1.0) < 0.5
    c = np.where(s[..., None], rgb(a), rgb(b)).astype(np.float32)
    n = fbm(ctx.P, 6.0, seed, 3)
    c = c * (1 - dirt * (0.4 + 0.6 * n) * (0.5 + 0.5 * white_noise(ctx, seed)))[..., None]
    return np.clip(c, 0, 1)


def deck_top(ctx, seed=23, **kw):
    """Tread plate with the hazard border on the outer 0.34 of the sides and ends."""
    x, z = ctx.P[..., 0], ctx.P[..., 2]
    c = tread_plate(ctx, seed=seed)
    h = hazard_world(ctx)
    edge = (np.abs(x) > HALF_W - 0.34) | (z > DECK_Z[1] - 0.34) | (z < DECK_Z[0] + 0.34)
    inner = (np.abs(np.abs(x) - (HALF_W - 0.34)) < 0.02) | (np.abs(z - (DECK_Z[1] - 0.34)) < 0.02) | (np.abs(z - (DECK_Z[0] + 0.34)) < 0.02)
    c = np.where(edge[..., None], h, c)
    c = np.where((inner & ~edge)[..., None], c * 0.45, c)
    # the join between deck sections: a dark line
    return c


def ramp_top(ctx, seed=26, **kw):
    """The loading ramp: tread plate, hazard stripes along both sides and at the foot."""
    x, z = ctx.P[..., 0], ctx.P[..., 2]
    c = tread_plate(ctx, seed=seed)
    h = hazard_world(ctx)
    edge = (np.abs(x) > 2.3 - 0.3) | (z < -8.5 + 0.3)
    return np.where(edge[..., None], h, c)


def girder(ctx, base="#3d444c", seed=24, **kw):
    c = pt.painted(ctx, base=base, hard="tblr", seed=seed, dirt=0.4)
    # rivets: a row of dots near the top and bottom edges
    rv = (np.abs(np.mod(ctx.dl / 0.18, 1.0) - 0.5) < 0.16) & ((np.abs(ctx.dt - 0.06) < 0.02) | (np.abs(ctx.db - 0.06) < 0.02))
    c = np.where(rv[..., None], c * 1.35 + 0.04, c)
    return np.clip(c, 0, 1)


def rail_paint(ctx, seed=25, **kw):
    """Tube rail: yellow with scuffs."""
    c = np.broadcast_to(rgb("#d9a91a"), (ctx.h, ctx.w, 3)).copy()
    n = fbm(ctx.P, 12.0, seed, 3)
    c = c * (0.75 + 0.4 * n)[..., None]
    c = mix(c, rgb("#3a3a3a"), 0.45 * smooth(0.72, 0.9, fbm(ctx.P, 20.0, seed + 1, 3)))
    return edge_fx(ctx, c, "tblr", ao=0.18, ao_w=0.03, hl=0.15)


def wheel_face(ctx, centre=(0, 0, 0), r=0.35, side=1.0, **kw):
    """A rail wheel seen along its axle: tyre rim, web with lightening holes, hub."""
    d = ctx.P - np.array(centre, np.float32)
    rr = np.sqrt(d[..., 1] ** 2 + d[..., 2] ** 2)
    th = np.arctan2(d[..., 2], d[..., 1])
    c = np.broadcast_to(rgb("#4a4f56"), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.8 + 0.4 * fbm(ctx.P, 20.0, 3, 3))[..., None]
    holes = (rr > 0.12) & (rr < 0.27) & (np.abs(np.mod(th / (2 * math.pi) * 6, 1.0) - 0.5) < 0.28)
    c = np.where(holes[..., None], c * 0.25, c)
    c = np.where((rr < 0.09)[..., None], rgb("#6e747c"), c)
    c = np.where(((rr > r - 0.045) & (rr < r + 0.01))[..., None], rgb("#6f757d") * (0.9 + 0.1 * np.cos(th * 3))[..., None], c)
    c = np.where((rr >= r + 0.01)[..., None], rgb("#2a2c30"), c)
    return np.clip(c, 0, 1)


def lamp_amber(ctx, **kw):
    c = np.broadcast_to(rgb("#ffc24a"), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.8 + 0.3 * np.cos(ctx.U * 20.0))[..., None]
    return edge_fx(ctx, c, "tblr", ao=0.25, ao_w=0.04, hl=0.2)


def stud(ctx, **kw):
    c = np.broadcast_to(rgb("#e6e8ea"), (ctx.h, ctx.w, 3)).copy()
    return edge_fx(ctx, c, "tblr", ao=0.3, ao_w=0.03, hl=0.2)


DECK = S(deck_top)
GIRDER = S(girder)
STEEL = S(pt.painted, base="#4d545c", hard="tblr", dirt=0.45)
DARK = S(pt.painted, base="#2b2e33", hard="tblr", dirt=0.5)
CHROME = S(pt.metal, base="#9ea3ab", dark=0.1)
YELLOW = S(pt.painted, base="#d9a91a", hard="tblr", dirt=0.35)
RAIL = S(rail_paint)
HAZ = S(hazard_world)


# ---------------------------------------------------------------------------------------------------- models
def deck_model(name, xs, zs, sheet):
    """One deck section: top plate with the border stripes, a side girder and skirt on the outer edge, the underside, rivet rows, tie-down rings and chocks."""
    m = Model(name)
    b = Bld(m, sheet, density=48)
    x0, x1 = xs
    z0, z1 = zs
    b.box((x0, -0.2, z0), (x1, 0.0, z1), {"u": DECK, "d": DARK, "f": GIRDER, "b": GIRDER, "l": GIRDER, "r": GIRDER}, "ufbd")
    # underframe: a deep web under the deck, ribs
    b.box((x0, -1.0, z0 + 0.02), (x1, -0.2, z1 - 0.02), {"d": DARK, "f": GIRDER, "b": GIRDER}, "dfb")
    if x1 > 0 and x1 >= HALF_W - 1e-6:
        b.box((x1 - 0.04, -1.0, z0), (x1, -0.2, z1), GIRDER, "l")
    if x0 < 0 and x0 <= -HALF_W + 1e-6:
        b.box((x0, -1.0, z0), (x0 + 0.04, -0.2, z1), GIRDER, "r")
    # transverse ribs seen from the sides
    k = int((z1 - z0) / 0.75)
    for i in range(k + 1):
        zz = z0 + 0.05 + i * (z1 - z0 - 0.1) / max(k, 1)
        for sx, xe in ((1, x1), (-1, x0)):
            if (sx > 0 and x1 >= HALF_W - 1e-6) or (sx < 0 and x0 <= -HALF_W + 1e-6):
                b.box((min(xe, xe - sx * 0.0) - (0.02 if sx > 0 else -0.0), -0.95, zz - 0.05), (xe + (0.0 if sx > 0 else 0.02), -0.25, zz + 0.05), STEEL, "l" if sx > 0 else "r")
    # lashing rings and chocks at the car's wheel positions (outer sides): D-rings just inside the border stripes
    for zz in (2.0, -2.3, 2.3, -2.0):
        if z0 + 0.3 < zz < z1 - 0.3:
            for sx in (1, -1):
                xc = 2.0 * sx
                if x0 <= xc <= x1:
                    b.box((xc - 0.1, 0.0, zz - 0.28), (xc + 0.1, 0.001, zz + 0.28), S(pt.painted, base="#c9a415", hard="tblr", dirt=0.2), "u")
                    # a wedge chock: a tilted slab
                    b.ob((xc, 0.07, zz), (0.2, 0.12, 0.5), rax("x", 0), YELLOW, "u")
                    b.ob((xc, 0.09, zz - 0.12), (0.2, 0.08, 0.3), rax("x", 25), YELLOW, "ufb")
    m.auto_center()
    return m


def bogie_model(sheet):
    m = Model("wagon_bogie")
    b = Bld(m, sheet, density=64)
    # frame: two side frames, a bolster, springs; wheelsets with spoked wheels
    for sx in (1, -1):
        b.box((sx * 1.38 - 0.09, -1.34, -0.65), (sx * 1.38 + 0.09, -1.02, 0.65), DARK, "fblrud")
    b.box((-1.38, -1.15, -0.1), (1.38, -1.02, 0.1), DARK, "fbud")
    for sx in (1, -1):
        for zz in (-0.45, 0.45):
            b.ring("y", (sx * 1.0, 0.0, zz), 0.085, 0.06, -1.1, -1.02, 8, S(pt.painted, base="#7a5a2a", hard="", dirt=0.2), faces=("out",))
    for zz in (-0.45, 0.45):
        c = (0.0, -1.18, zz)
        b.box((-1.3, -1.2, zz - 0.04), (1.3, -1.16, zz + 0.04), CHROME, "fbud")      # axle
        for sx in (1, -1):
            xc = sx * 1.28
            C = (xc, -1.18, zz)
            b.ring("x", C, 0.36, 0.30, xc - 0.07, xc + 0.07, 12, {"out": S(pt.painted, base="#454a50", hard="", dirt=0.3), "a0": S(wheel_face, centre=C, r=0.36),
                                                              "a1": S(wheel_face, centre=C, r=0.36)}, faces=("out", "a0", "a1"))
            b.ring("x", C, 0.40, 0.36, xc - (0.075 if sx > 0 else 0.0), xc + (0.0 if sx > 0 else 0.075), 12, S(pt.painted, base="#3c4046", hard="", dirt=0.3), faces=("out",))
            b.disc("x", C, 0.30, xc + 0.05, xc + 0.065, 12, {"a1": S(wheel_face, centre=C, r=0.3), "a0": S(wheel_face, centre=C, r=0.3)})
    m.auto_center()
    return m


def hitch_model(sheet):
    m = Model("wagon_hitch")
    b = Bld(m, sheet, density=64)
    # draw bar, coupler head, two buffers with their round plates
    b.box((-0.18, -0.75, 4.5), (0.18, -0.42, 5.1), DARK, "fblrud")
    b.box((-0.26, -0.78, 5.0), (0.26, -0.36, 5.5), STEEL, "fblrud")
    b.box((-0.1, -0.7, 5.5), (0.1, -0.44, 5.62), CHROME, "fud")
    for sx in (1, -1):
        b.box((sx * 0.9 - 0.04, -0.7, 4.5), (sx * 0.9 + 0.04, -0.5, 4.95), STEEL, "fblrud")
        b.ring("z", (sx * 0.9, -0.6, 4.9), 0.2, 0.0, 4.88, 5.0, 12, {"out": CHROME, "a1": CHROME}, faces=("out", "a1"))
    m.auto_center()
    return m


def rail_model(name, side, z0, z1, sheet, posts=(True, True), lamp=False, front=False):
    """Side rail segment on the +x side (mirrored for side=-1): top and mid tube, posts at the ends; the front-left corner carries the lamp."""
    m = Model(name)
    b = Bld(m, sheet, side, density=64)
    xr = 2.42
    b.box((xr - 0.07, 0.80, z0), (xr + 0.07, 0.95, z1), RAIL, "fblrud")
    b.box((xr - 0.06, 0.42, z0), (xr + 0.06, 0.52, z1), RAIL, "fblrud")
    for (pz, on) in ((z0 + 0.075, posts[0]), (z1 - 0.075, posts[1])):
        if on:
            b.box((xr - 0.1, 0.0, pz - 0.075), (xr + 0.1, 0.95, pz + 0.075), RAIL, "fblrud")
    if lamp:
        zl = z1 - 0.075
        b.box((xr - 0.12, 0.95, zl - 0.12), (xr + 0.12, 1.02, zl + 0.12), DARK, "fblrud")
        b.box((xr - 0.1, 1.02, zl - 0.1), (xr + 0.1, 1.2, zl + 0.1), {"f": S(lamp_amber), "b": S(lamp_amber), "l": S(lamp_amber), "r": S(lamp_amber), "u": DARK}, "fblru", emit=14)
        b.box((xr - 0.13, 1.2, zl - 0.13), (xr + 0.13, 1.24, zl + 0.13), DARK, "fblrud")
    m.auto_center()
    return m


def rail_front_model(name, x0, x1, sheet, lamp=False):
    m = Model(name)
    b = Bld(m, sheet, 1, density=64)
    zf = 4.22
    b.box((x0, 0.80, zf - 0.075), (x1, 0.95, zf + 0.075), RAIL, "fblrud")
    b.box((x0, 0.42, zf - 0.06), (x1, 0.52, zf + 0.06), RAIL, "fblrud")
    for px in (x0 + 0.075, x1 - 0.075):
        if abs(abs(px) - 2.425) < 0.2 or abs(px) < 0.2:
            b.box((px - 0.075, 0.0, zf - 0.075), (px + 0.075, 0.95, zf + 0.075), RAIL, "fblrud")
    m.auto_center()
    return m


def kerb_model(name, side, z0, z1, sheet):
    """The low striped kerb on the open side (0.22 high), with reflector studs; side=+1 builds it on the left (x > 0)."""
    m = Model(name)
    b = Bld(m, sheet, side, density=64)
    b.box((2.28, 0.0, z0), (2.5, 0.22, z1), {"u": HAZ, "l": HAZ, "r": HAZ, "f": HAZ, "b": HAZ}, "ulr")
    for zz in np.arange(z0 + 0.3, z1, 0.75):
        b.box((2.36, 0.22, zz - 0.04), (2.42, 0.235, zz + 0.04), S(stud), "u")
    m.auto_center()
    return m


def ramp_model(name, xs, zs, sheet):
    """One half of the loading ramp, flat in the model (the part tilts it); 4.0 long, deck-plate top with edge stripes and a kerb on the outside."""
    m = Model(name)
    b = Bld(m, sheet, 1, density=48)
    x0, x1 = xs
    zl, zh = zs
    b.box((x0, -0.12, zl), (x1, 0.0, zh), {"u": S(ramp_top), "d": DARK, "l": GIRDER, "r": GIRDER, "b": GIRDER, "f": GIRDER}, "udlrbf")
    for zz in np.arange(zl + 0.1, zh - 0.05, 0.3):
        b.box((x0, 0.0, zz), (x1, 0.012, zz + 0.07), S(pt.painted, base="#2d3035", hard="", dirt=0.3), "u")
    m.auto_center()
    return m


def build_wagon():
    v = Vehicle("wagon")
    sheet = Sheet("wagon_main", density=48, pad=2, max_size=2048)
    v.sheets = [sheet]
    P = v.parts

    def add(name, m, only=None, **kw):
        ps = PartSpec(name, m, group="wagon", **kw)
        ps.only = only
        P.append(ps)
        return ps

    xsplit = {"L": (0.0, HALF_W), "R": (-HALF_W, 0.0)}
    for k, zs in enumerate([(-4.5, -1.5), (-1.5, 1.5), (1.5, 4.5)]):
        for sd, xs in xsplit.items():
            add(f"deck{k}{sd}", v.add_model(deck_model(f"wagon_deck_{k}{sd}", xs, zs, sheet)))
    bg = v.add_model(bogie_model(sheet))
    c = bg.center
    add("bogieB", bg, at=(c[0], c[1], -2.8 + c[2]))
    add("bogieF", bg, at=(c[0], c[1], 2.8 + c[2]))
    ht = v.add_model(hitch_model(sheet))
    add("hitchF", ht)
    add("hitchB", ht, at=(-ht.center[0], ht.center[1], -ht.center[2]), R=rax("y", 180))
    segs = {"F": (1.5, 4.3, (False, True)), "M": (-1.5, 1.5, (False, False)), "B": (-4.3, -1.5, (True, False))}
    for sd, sg in (("L", 1), ("R", -1)):
        for nm, (z0, z1, posts) in segs.items():
            m = v.add_model(rail_model(f"wagon_rail_{nm}{sd}", sg, z0, z1, sheet, posts, lamp=(nm == "F" and sd == "L")))
            add(f"rail{nm}{sd}", m, only=("rail", sd))
        for k, (z0, z1) in enumerate([(-4.5, -1.5), (-1.5, 1.5), (1.5, 4.5)]):
            m = v.add_model(kerb_model(f"wagon_kerb_{k}{sd}", sg, z0, z1, sheet))
            add(f"kerb{k}{sd}", m, only=("kerb", sd))
    for nm, (x0, x1) in (("L", (0.0, 2.5)), ("R", (-2.5, 0.0))):
        add(f"railF{nm}x", v.add_model(rail_front_model(f"wagon_railfront_{nm}", x0, x1, sheet)))
    # the loading ramp: two halves, tilted down towards the rear about the rear edge of the bed
    ang = math.degrees(math.atan2(1.0, 4.0))
    R = rax("x", -ang)
    pv = np.array([0.0, 0.0, -4.5])
    for nm, xs in (("L", (0.0, 2.3)), ("R", (-2.3, 0.0))):
        for k, zs in enumerate([(-6.5, -4.5), (-8.5, -6.5)]):
            m = v.add_model(ramp_model(f"wagon_ramp_{nm}{k}", xs, zs, sheet))
            at = pv + R @ (np.array(m.center) - pv)
            add(f"ramp{nm}{k}", m, only=("ramp",), at=tuple(at), R=R)
    return v


def parts_for(veh, ramp=False, low_side=None):
    """The PartSpecs of a wagon: rails on the sides that are not the low side, the kerb on the low side, the ramp when asked for."""
    out = []
    for ps in veh.parts:
        o = getattr(ps, "only", None)
        if o is None:
            out.append(ps)
        elif o[0] == "rail" and low_side != o[1]:
            out.append(ps)
        elif o[0] == "kerb" and low_side == o[1]:
            out.append(ps)
        elif o[0] == "ramp" and ramp:
            out.append(ps)
    return out