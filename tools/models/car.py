"""The roadster: a small blue open-top two-seater, right-hand drive (driver on the RIGHT, x < 0), as item models.

Rig space: +x left (the passenger's side and door), +y up, +z forward.  Same footprint, seats, door line and windscreen height as the old box car:
3.0 wide over the body, 3.64 over the wheels, 6.76 long, door tops at 0.75, windscreen top at 1.08, rider's feet (0.72, 0.17, -0.12) and (-0.72, 0.17, 0.12).

Every model is limited to 3 blocks in each axis (26.3: from/to in -16..32), so the car is a set of display parts:
nose, wing_fl, wing_fr, tub, door_l, dash, seat_l, seat_r, screen, tail, wing_rl, wing_rr and one wheel model used four times.
"""
import math
from functools import partial

import numpy as np

from . import car_paint as cp
from . import paint as pt
from .mdl import Model, Sheet
from .shapes import Bld, catmull, smoothstep
from .vmath import I3, rax

# ------------------------------------------------------------------------------------------------ the numbers
TOP = 0.74                       # the scuttle's top at the centre line
ZW = 1.10                        # the foot of the windscreen
WR, WYC = 0.40, 0.40             # wheel radius and axle height
WZF, WZR = 2.0, -2.3             # axle positions
WX0, WX1 = 1.46, 1.82            # tyre x range (left); the right wheels mirror it
ARCH_R = 0.44                    # the wheel arch's inner radius
SEAT_P = (0.72, 0.17, -0.12)
SEAT_D = (-0.72, 0.17, 0.12)
DOOR_Z = (-1.2, 0.86)
RIGHT_AO = []

hood_y = catmull([(1.05, 0.725), (1.4, 0.675), (1.9, 0.585), (2.4, 0.50), (2.8, 0.445), (3.05, 0.41), (3.2, 0.37), (3.3, 0.30), (3.38, 0.22)])
deck_y = catmull([(-1.10, 0.84), (-1.5, 0.86), (-2.0, 0.83), (-2.5, 0.74), (-2.9, 0.63), (-3.2, 0.52), (-3.36, 0.44)])

SHEET_REF = [None]

ARCHES = [(WZF, WYC, ARCH_R), (WZR, WYC, ARCH_R)]


def S(f, **k):
    return partial(f, **k)


BODY = S(cp.blue, hard="", ao_arch=ARCHES)
BODY_EDGE = S(cp.blue, hard="tblr", ao_arch=ARCHES)
BODY_NS = S(cp.blue, hard="", stripe=False, ao_arch=ARCHES)
SHUT = S(cp.blue, hard="", stripe=False, shut="tblr", ao_arch=ARCHES)
CHROME = S(pt.metal)
CHROME_D = S(pt.metal, base="#9ea3ab", dark=0.15)
BLACK = S(pt.vinyl, base="#1c1c1f", hard="tblr")
BLACK_S = S(pt.vinyl, base="#1c1c1f", hard="")
RUBBER = S(pt.rubber)
LEATHER = S(pt.leather, base="#bd8650", piping="#4a2f1a")
LEATHER_S = S(pt.leather, base="#bd8650", piping="#4a2f1a", stitch=False, hard="")
LEATHER_D = S(pt.leather, base="#8d5f36", piping="#3a2414")
CARPET = S(cp.carpet, base="#3a4152")
UNDER = S(cp.underbody)
GLASSP = S(cp.glass_clear)
DASH_BLUE = S(cp.blue, hard="tblr", stripe=False, wear=0.1, tone=0.95)
ALU = S(pt.metal, base="#b9bdc4", bands=False)


def new_model(name, sheet):
    return Model(name), Bld(Model(name), sheet)


# ================================================================================================ wheels
def wheel_model(sheet):
    """One left wheel at the origin, axle along x, hubcap towards +x: 16-sided tyre (tread and sidewalls), alloy face with brake disc behind,
    spinner hubcap.  Right wheels turn the same model half a turn about y."""
    m = Model("car_wheel", center=(0, 0, 0))
    b = Bld(m, sheet, density=110)
    C = (0.0, 0.0, 0.0)
    wd = 0.34
    # tyre: 16 tangent slabs, tread outside, sidewall rings on both axial faces
    b.ring("x", C, WR, WR - 0.12, -wd / 2, wd / 2, 16, {"out": S(cp.tyre_tread, centre=C), "a1": S(cp.tyre_wall, centre=C, r_out=WR),
                                                          "a0": S(cp.tyre_wall, centre=C, r_out=WR), "in": S(pt.rubber)}, faces=("out", "a0", "a1"))
    # the rim: a flat disc a little inside the sidewall face, painted as the alloy wheel; plus an inner dark barrel
    b.disc("x", C, WR - 0.115, 0.05, 0.07, 16, {"a1": S(cp.rim_face, centre=C, r_rim=WR - 0.125, side=1.0), "a0": S(cp.rim_face, centre=C, r_rim=WR - 0.125, side=-1.0)})
    b.ring("x", C, WR - 0.115, WR - 0.135, -0.10, 0.07, 16, S(pt.rubber), faces=("out",))
    b.disc("x", C, 0.17, -0.12, -0.10, 12, S(cp.rim_face, centre=C, r_rim=0.12, side=-1.0), faces=("a0",))
    # the spinner hubcap
    b.disc("x", C, 0.085, 0.07, 0.11, 12, {"a1": S(cp.hub_cap, centre=C), "a0": S(pt.metal)})
    b.ring("x", C, 0.085, 0.07, 0.07, 0.11, 12, S(pt.metal), faces=("out",))
    return m


# ================================================================================================ shared body parts
def _wing(m, sheet, sheet_g, front=True, side=1, name="wing"):
    """One wing (mirrored for the right): top surface, outer wall with the arch cut out, arch lip and liner, lamp pod (front)."""
    b = Bld(m, sheet, side)
    zc = WZF if front else WZR
    sgn = 1 if front else -1

    def xo(z):
        if front:
            return 1.5 + 0.32 * smoothstep(0.95, 1.65, z) * (1 - 0.0 * z) - 0.10 * smoothstep(2.9, 3.3, z)
        return 1.5 + 0.32 * smoothstep(-1.2, -1.85, z) - 0.40 * smoothstep(-2.7, -3.34, z)

    def crest(z):
        return 0.265 * math.exp(-((z - zc) / 0.50) ** 2)

    def base(z):
        return hood_y(z) if front else float(deck_y(z)) - 0.05

    z0, z1 = (1.04, 3.3) if front else (-3.32, -1.14)
    zs = list(np.linspace(z0, z1, 25))
    us = [0.0, 0.14, 0.28, 0.42, 0.58, 0.72, 0.84, 0.93, 1.0]

    def xin(z):
        # the wing starts where the deck/bonnet ends: the rear deck narrows towards the tail
        return 1.0 if front else 1.0 * (1.0 - 0.18 * smoothstep(-2.5, -3.3, z))

    def top(u, z):
        x = xin(z) + u * (xo(z) - xin(z))
        s = smoothstep(0.30, 0.52, u)
        rise = crest(z) * s
        roll = (0.03 + 0.14 * (1 - math.exp(-((z - zc) / 0.95) ** 2))) * smoothstep(0.62, 1.0, u) ** 1.7
        return (x, base(z) + rise - roll, z)

    def cell(i, j, ni, nj):
        return (BODY, {})
    b.loft(top, us, zs, 0.045, BODY, hint=(0, 1, 0))
    # outer wall: vertical slices, with the arch cut out
    lowy = 0.17
    nz = 44
    zz = np.linspace(z0, z1, nz + 1)
    for k in range(nz):
        za, zb = zz[k], zz[k + 1]
        zm = (za + zb) / 2
        xa, xb = xo(za), xo(zb)
        ytop = base(zm) + crest(zm) - (0.03 + 0.14 * (1 - math.exp(-((zm - zc) / 0.95) ** 2))) - 0.012
        dz = zm - zc
        if abs(dz) < ARCH_R + 0.02:
            ya = WYC + math.sqrt(max(ARCH_R ** 2 - min(abs(dz) + 0.045, ARCH_R) ** 2, 0.0))
        else:
            ya = lowy
        if ytop - ya < 0.02:
            continue
        b.strip((xa, ya, za), (xa, ytop, za), (xb, ya, zb), (xb, ytop, zb), 0.035, BODY, "u", hint=(1, 0, 0), grow=0.02)
        if ya <= lowy + 1e-6:
            # a dark rubber valance along the foot of the wall: hides the saw-tooth where the slices turn with the wing's sweep
            b.strip((xa + 0.012, lowy - 0.04, za), (xa + 0.012, lowy + 0.05, za), (xb + 0.012, lowy - 0.04, zb), (xb + 0.012, lowy + 0.05, zb), 0.03,
                    S(pt.rubber, base="#18181b", hard=""), "u", hint=(1, 0, 0), grow=0.06)
    # the lip of the arch: body-coloured ring segments, and the dark liner behind them
    start, sweep = -102.0, 204.0
    ring_a = (xo(zc) - 0.075, xo(zc) + 0.035)
    cc = (0.0, WYC, zc)
    b.ring("x", cc, ARCH_R + 0.04, ARCH_R, ring_a[0], ring_a[1], 14, {"out": BODY, "a1": BODY, "a0": BODY, "in": S(cp.arch_liner)}, start=start if front else start, sweep=sweep,
           faces=("out", "a1", "in"))
    b.ring("x", cc, ARCH_R, ARCH_R - 0.02, 1.43, ring_a[0], 14, S(cp.arch_liner), start=start, sweep=sweep, faces=("in",))
    if front:
        # a chrome-framed side vent behind the front wheel
        xv = xo(1.33) + 0.012
        b.box((xv, 0.43, 1.18), (xv + 0.02, 0.63, 1.48), S(cp.slats, n=7, horizontal=False), "l", R=rax("y", math.degrees(math.atan2(xo(1.48) - xo(1.18), 0.30))), pivot=(xv, 0.53, 1.33))
        b.box((xv - 0.004, 0.41, 1.16), (xv + 0.016, 0.645, 1.50), CHROME, "l", R=rax("y", math.degrees(math.atan2(xo(1.48) - xo(1.18), 0.30))), pivot=(xv, 0.53, 1.33))
        # the front end of the wing and the lamp pod
        b.box((1.0, 0.18, 3.22), (1.82 - 0.1, 0.36, 3.3), BODY, "fu")
        pod = (1.28, 0.385, 3.08)
        b.ring("z", pod, 0.15, 0.124, 3.02, 3.26, 16, {"out": CHROME, "a1": CHROME}, faces=("out", "a1"))
        b.disc("z", pod, 0.124, 3.18, 3.2, 16, {"a1": S(cp.head_lens), "a0": CHROME}, faces=("a1",), emit=12)
        b.disc("z", pod, 0.15, 3.0, 3.02, 16, S(pt.rubber), faces=("a0",))
        b.box((1.24, 0.22, 3.04), (1.32, 0.26, 3.12), CHROME, "fl")
        # an indicator and a side repeater
        b.box((1.50, 0.30, 3.24), (1.74, 0.37, 3.30), S(pt.painted, base="#e8a020", hard="tblr", dirt=0.0), "f", emit=6)
        b.box((1.80, 0.50, 2.45), (1.835, 0.58, 2.60), S(pt.painted, base="#e8a020", hard="tblr", dirt=0.0), "l", emit=4)
    else:
        # a side marker and the wing's tail end
        b.box((1.80, 0.52, -2.85), (1.835, 0.60, -2.72), S(pt.painted, base="#c42820", hard="tblr", dirt=0.0), "l", emit=4)
    return m


def wing_model(name, front, side, sheet, sheet_g):
    m = Model(name)
    _wing(m, sheet, sheet_g, front, side, name)
    m.auto_center()
    return m


# ================================================================================================ the nose
def nose_model(sheet):
    m = Model("car_nose")
    b = Bld(m, sheet)
    xs = [-1.05, -0.86, -0.64, -0.40, -0.18, 0.0, 0.18, 0.40, 0.64, 0.86, 1.05]
    zs = [1.04, 1.28, 1.55, 1.85, 2.15, 2.45, 2.75, 2.98, 3.14, 3.27, 3.35]

    def hood(x, z):
        crown = 0.03 * (1 - (x / 1.05) ** 2)
        dome = 0.02 * math.exp(-((x / 0.36) ** 2)) * smoothstep(1.4, 1.9, z) * (1 - smoothstep(2.4, 3.0, z))
        return (x, float(hood_y(z)) + crown + dome, z)

    b.loft(hood, xs, zs, 0.045, BODY, hint=(0, 1, 0))
    # under the bonnet: the engine bay's dark roof and the radiator cowl seen from the grille
    b.box((-1.0, 0.14, 1.0), (1.0, 0.2, 3.2), UNDER, "d")
    # front panel under the leading edge: grille opening, lower valance, side panels
    b.box((-1.02, 0.12, 3.12), (-0.62, 0.40, 3.30), BODY_NS, "fu", )
    b.box((0.62, 0.12, 3.12), (1.02, 0.40, 3.30), BODY_NS, "fu")
    b.box((-0.62, 0.12, 3.12), (0.62, 0.19, 3.32), BODY_NS, "fud")
    b.box((-0.62, 0.38, 3.12), (0.62, 0.43, 3.30), BODY_NS, "f")
    # the grille: dark mesh in a chrome surround (an oval made of a ring around a flat panel)
    b.box((-0.58, 0.19, 3.20), (0.58, 0.38, 3.23), S(cp.mesh, pitch=0.05), "f")
    for sx in (-1, 1):
        b.box((sx * 0.58 - 0.03, 0.16, 3.2), (sx * 0.58 + 0.03, 0.41, 3.30), CHROME, "fu")
    b.box((-0.61, 0.38, 3.2), (0.61, 0.425, 3.31), CHROME, "fu")
    b.box((-0.61, 0.155, 3.2), (0.61, 0.20, 3.31), CHROME, "fd")
    # the emblem in the middle of the top bar
    b.box((-0.07, 0.425, 3.28), (0.07, 0.505, 3.31), S(cp.emblem), "f")
    # front plate on a bracket
    b.box((-0.32, 0.20, 3.34), (0.32, 0.36, 3.345), S(cp.plate, text="TK3 015", rear=False), "f")
    # bumper: a chrome blade across the nose with two overriders
    b.box((-1.02, 0.14, 3.34), (1.02, 0.26, 3.40), CHROME, "fud", )
    for sx in (-0.62, 0.62):
        b.box((sx - 0.05, 0.12, 3.34), (sx + 0.05, 0.30, 3.45), CHROME, "fu")
    # bonnet louvres are paint; the bonnet's hinge strips are paint too (see car_paint.blue)
    m.auto_center()
    return m


# ================================================================================================ the cockpit tub
def tub_model(sheet):
    m = Model("car_tub")
    b = Bld(m, sheet)
    # floor and underbody
    b.box((-1.3, 0.06, -1.3), (1.3, 0.17, 0.92), {"u": CARPET, "d": UNDER, "*": UNDER}, "ud")
    b.box((-1.2, 0.0, -1.0), (-1.1, 0.07, 0.9), UNDER, "lrd")
    b.box((1.1, 0.0, -1.0), (1.2, 0.07, 0.9), UNDER, "lrd")
    # transmission tunnel: a carpeted hump with chamfered sides, a leather gaiter round the gear lever
    b.box((-0.2, 0.17, -1.0), (0.2, 0.5, 0.88), {"u": CARPET, "*": CARPET}, "ufb")
    b.ob((0.265, 0.34, -0.06), (0.15, 0.34, 1.9), rax("z", -22), S(cp.carpet), "ul")
    b.ob((-0.265, 0.34, -0.06), (0.15, 0.34, 1.9), rax("z", 22), S(cp.carpet), "ur")
    # left door sill and the sill plate
    b.box((1.22, 0.10, DOOR_Z[0]), (1.5, 0.27, DOOR_Z[1]), {"l": S(pt.vinyl, base="#17171a", hard="t"), "u": ALU, "f": BLACK_S, "*": UNDER}, "lud")
    b.box((1.24, 0.27, -0.95), (1.46, 0.275, 0.65), S(pt.metal, base="#9aa0a8", bands=False), "u")
    # right door (fixed): outer skin, inner card, top roll
    xr = (-1.5, -1.22)
    b.box((xr[0], 0.12, DOOR_Z[0]), (xr[1], 0.72, DOOR_Z[1]), {"r": S(cp.blue, hard="", stripe=False, shut="tblr", ao_arch=ARCHES), "l": S(pt.leather, base="#bd8650", hard="tb"),
                                                               "u": S(pt.vinyl, base="#17171a", hard="")}, "rlu")
    b.box((xr[0], 0.69, DOOR_Z[0] + 0.02), (xr[0] + 0.02, 0.715, DOOR_Z[1] - 0.02), CHROME, "ru")
    b.box((xr[0], 0.52, -0.78), (xr[0] + 0.03, 0.60, -0.5), CHROME, "rfu")             # outer handle
    b.box((-1.40, 0.46, -0.78), (xr[1], 0.55, -0.05), S(pt.leather, base="#a97440", hard="tblr"), "lu")     # armrest
    b.box((-1.40, 0.58, 0.05), (xr[1] + 0.01, 0.64, 0.40), S(pt.metal, base="#c0c4cb", bands=False), "lu")     # door pull
    b.box((-1.40, 0.22, -0.55), (xr[1] + 0.01, 0.40, 0.45), S(cp.slats, n=9), "l")                               # speaker grille
    # cowl sides and the scuttle
    for sx in (1, -1):
        lo, hi = ((1.22, 0.14, DOOR_Z[1]), (1.5, 0.74, 1.12)) if sx > 0 else ((-1.5, 0.14, DOOR_Z[1]), (-1.22, 0.74, 1.12))
        b.box(lo, hi, {"l": BODY, "r": BODY, "u": S(pt.vinyl, base="#17171a", hard="t"), "b": S(pt.vinyl, base="#17171a", hard="")}, "lrub" if sx > 0 else "lrub")
    # dash: painted fascia, a padded top with a lip, the glovebox lid
    b.box((-1.22, 0.14, 0.90), (1.22, 0.62, 1.1), {"b": DASH_BLUE, "u": BODY_NS, "*": UNDER}, "bu")
    # the padded top slopes 16 degrees down towards the seats: low enough that the rider's view over it stays as open as the old scuttle's
    b.box((-1.5, 0.62, 0.86), (1.5, 0.74, 1.12), {"u": S(pt.vinyl, base="#16161a", hard="", tex=0.09), "b": BLACK_S, "l": BLACK_S, "r": BLACK_S}, "ublr",
          R=rax("x", -16.0), pivot=(0.0, 0.74, 1.12))
    b.box((0.33, 0.28, 0.885), (1.12, 0.56, 0.9), S(cp.blue, hard="", stripe=False, shut="tblr", wear=0.1, tone=0.92), "b")
    b.box((0.69, 0.395, 0.865), (0.77, 0.445, 0.885), CHROME, "bu")
    for vx in (0.22, 1.14):
        b.disc("z", (vx, 0.58, 0.87), 0.05, 0.86, 0.89, 12, S(cp.slats, n=4, horizontal=True), faces=("a0",))
    # behind the seats: the bulkhead with its leather-trimmed face and the shelf
    b.box((-1.5, 0.14, -1.3), (1.5, 0.86, -1.1), {"f": S(cp.pleats, across="u", pitch=0.22, base="#b27c47"), "u": S(pt.leather, base="#bd8650", hard="t"), "*": BODY_NS}, "fu")
    # the cross member and chassis rails seen from below
    b.box((-1.2, -0.06, -1.3), (-1.0, 0.06, 0.9), UNDER, "lrd")
    b.box((1.0, -0.06, -1.3), (1.2, 0.06, 0.9), UNDER, "lrd")
    m.center = np.array([0.0, 0.4, -0.09])
    return m


# ================================================================================================ the left door
def door_model(sheet):
    m = Model("car_door_l")
    b = Bld(m, sheet)
    z0, z1 = DOOR_Z
    # outer skin (upper part leans in 5 degrees), inner card, top roll, handle, mirror-line chrome
    b.box((1.43, 0.26, z0), (1.5, 0.52, z1), {"l": S(cp.blue, hard="", stripe=False, shut="tblr", ao_arch=ARCHES), "u": BODY_NS, "d": UNDER, "*": UNDER}, "lud")
    b.box((1.43, 0.52, z0), (1.485, 0.74, z1), {"l": S(cp.blue, hard="", stripe=False, shut="tr", ao_arch=ARCHES), "u": BODY_NS}, "lu", R=rax("z", -4.5), pivot=(1.465, 0.52, 0))
    b.box((1.478, 0.505, z0 + 0.02), (1.508, 0.525, z1 - 0.02), CHROME, "lu")                       # the belt moulding
    b.box((1.48, 0.50, -0.80), (1.545, 0.585, -0.45), CHROME, "lfbu")                                # the handle
    b.box((1.50, 0.545, -0.62), (1.51, 0.555, -0.60), S(pt.rubber), "l")
    # inner card and its trim
    b.box((1.22, 0.26, z0 + 0.02), (1.43, 0.70, z1 - 0.02), {"r": S(pt.leather, base="#bd8650", hard="tb"), "u": S(pt.vinyl, base="#17171a", hard=""), "*": UNDER}, "ru")
    b.box((1.22, 0.26, z0 + 0.02), (1.30, 0.34, z1 - 0.02), BLACK, "ru")
    b.box((1.22, 0.46, -0.78), (1.40, 0.55, -0.05), S(pt.leather, base="#a97440", hard="tblr"), "ru")      # armrest
    b.box((1.22, 0.58, 0.05), (1.34, 0.64, 0.40), S(pt.metal, base="#c0c4cb", bands=False), "ru")          # door pull
    b.box((1.22, 0.22, -0.55), (1.30, 0.40, 0.45), S(cp.slats, n=9), "r")
    m.center = np.array([1.36, 0.5, (z0 + z1) / 2])
    m.auto_center()
    return m


# ================================================================================================ the dash: dials, wheel, controls
def dash_model(sheet):
    m = Model("car_dash")
    b = Bld(m, sheet, density=96)
    dial_z = 0.795
    # binnacle in front of the driver, carrying the two big dials
    b.box((-1.25, 0.60, 0.80), (-0.18, 0.80, 1.0), {"b": S(pt.vinyl, base="#19191c", hard="tblr"), "u": S(pt.vinyl, base="#19191c", hard=""), "l": BLACK_S, "r": BLACK_S}, "bulr")
    for cx_, kind in ((-0.93, "speedo"), (-0.50, "rev")):
        c = (cx_, 0.725, dial_z)
        b.disc("z", c, 0.168, dial_z - 0.004, dial_z + 0.0, 16, S(cp.dial, kind=kind, centre=c, right=(-1, 0, 0), up=(0, 1, 0), radius=0.168), faces=("a0",), emit=9)
        b.ring("z", c, 0.205, 0.168, dial_z - 0.03, dial_z + 0.0, 16, {"out": CHROME, "a0": CHROME, "in": S(pt.rubber)}, faces=("out", "a0"))
    # the small gauges and the switch panel on the fascia (z = 0.9 plane)
    for gx, kind in ((-0.10, "fuel"), (0.10, "temp"), (0.30, "oil"), (0.50, "amp")):
        c = (gx, 0.43, 0.898)
        b.disc("z", c, 0.072, 0.893, 0.897, 12, S(cp.dial, kind=kind, centre=c, right=(-1, 0, 0), up=(0, 1, 0), radius=0.072), faces=("a0",), emit=8)
        b.ring("z", c, 0.092, 0.072, 0.88, 0.897, 12, {"out": CHROME, "a0": CHROME}, faces=("out", "a0"))
    b.box((-0.40, 0.355, 0.885), (-0.20, 0.45, 0.9), S(cp.switch_panel), "b")
    b.box((0.60, 0.5, 0.885), (1.05, 0.54, 0.9), S(pt.metal, base="#b7bcc4", bands=False), "b")                  # a trim strip above the glovebox
    # steering column and wheel: the wheel's plane is tilted 35 degrees, its normal pointing at the driver's chest
    hub = np.array([-0.72, 1.10, 0.52])
    d = np.array([0.0, 0.82, -0.57])
    colc = np.array([-0.72, 0.58, 0.89]) + (hub - np.array([-0.72, 0.58, 0.89])) * 0.5
    b.ob(colc, (0.10, 0.10, 0.66), rax("x", 55), S(pt.vinyl, base="#141416", hard=""), "fblrud")
    b.box((-0.84, 0.46, 0.86), (-0.60, 0.64, 0.97), S(pt.vinyl, base="#141416", hard="tblr"), "fbu")
    R0 = rax("x", 55)
    rim_c = tuple(hub)
    b.ring("z", rim_c, 0.285, 0.235, hub[2] - 0.03, hub[2] + 0.03, 16, {"out": S(pt.vinyl, base="#15151a", hard="", tex=0.12), "a0": S(pt.vinyl, base="#15151a", hard="", tex=0.12),
                                                                    "a1": S(pt.vinyl, base="#15151a", hard="", tex=0.12), "in": S(pt.vinyl, base="#15151a", hard="")},
           faces=("out", "a0", "a1", "in"), R0=R0)
    for k in range(3):
        ang = k * 120.0 + 90.0
        b.ob(rim_c, (0.045, 0.25, 0.03), R0 @ rax("z", ang), S(pt.metal, base="#b4b8c0"), "fblrud") if False else None
        # three spokes: slabs from the hub to the rim, each its own oriented box in the wheel's plane
        cen = np.array(rim_c) + R0 @ (rax("z", ang) @ np.array([0.0, 0.135, 0.0]))
        b.ob(cen, (0.05, 0.27, 0.03), R0 @ rax("z", ang), S(pt.metal, base="#b4b8c0"), "fblrud")
    b.disc("z", rim_c, 0.075, hub[2] - 0.04, hub[2] + 0.04, 12, {"a0": S(cp.emblem), "a1": S(pt.metal), "out": S(pt.metal)}, faces=("a0", "a1", "out"), R0=R0)
    # pedals under the dash on the driver's side: clutch, brake, accelerator
    for px, w in ((-1.0, 0.1), (-0.78, 0.1), (-0.5, 0.07)):
        b.ob((px, 0.28, 0.60), (w, 0.2, 0.025), rax("x", -25), S(pt.rubber, base="#252528", hard="tblr"), "fbu")
        b.box((px - 0.01, 0.30, 0.64), (px + 0.01, 0.45, 0.66), CHROME, "fbl")
    # gear lever: a gaiter, a stalk leaning forward and a leather knob; the handbrake beside it
    b.box((-0.085, 0.48, 0.14), (0.085, 0.54, 0.30), S(pt.leather, base="#2a2a2e", hard="t"), "fbul")
    b.ob((0.0, 0.70, 0.22), (0.035, 0.38, 0.035), rax("x", 8), S(pt.metal, base="#9ea3ab", bands=False), "fblrud")
    b.box((-0.05, 0.875, 0.14), (0.05, 0.965, 0.26), S(pt.leather, base="#1d1d20", hard="", stitch=False), "fblrud")
    b.ob((0.20, 0.60, -0.35), (0.04, 0.34, 0.06), rax("x", -30), S(pt.metal, base="#9ea3ab", bands=False), "fblrud")
    b.box((0.17, 0.74, -0.46), (0.23, 0.78, -0.40), S(pt.rubber), "fblrud") if False else None
    m.auto_center()
    return m


# ================================================================================================ the seats
def seat_model(name, xc, z0, sheet, flip=1):
    """A bucket seat for a rider whose feet are at (xc, 0.17, z0): frame, crowned cushion with rolled bolsters, a pleated back leaning 10 degrees with curled
    bolsters and a shoulder roll, a padded headrest on two posts."""
    m = Model(name)
    b = Bld(m, sheet, density=72)
    TAN = "#cfa468"
    L = S(pt.leather, base=TAN, stitch=False, hard="tblr", ao=0.22, pipe=0.22)
    LE = S(pt.leather, base=TAN, hard="tblr", pipe=0.25)
    LP = S(cp.pleats, across="u", pitch=0.19, base=TAN, hard="")
    LD = S(pt.leather, base="#a97a48", hard="", stitch=False)
    BK = S(cp.blue, hard="tblr", stripe=False, wear=0.1)
    VIN = S(pt.vinyl, base="#202024", hard="tblr")
    zf, zr = z0 + 0.44, z0 - 0.46
    zm = (zf + zr) / 2
    # frame and runners
    b.box((xc - 0.27, 0.17, zr + 0.08), (xc + 0.27, 0.38, zf - 0.22), VIN, "fblr")
    for s in (-1, 1):
        b.box((xc + s * 0.27 - 0.02, 0.17, zr + 0.1), (xc + s * 0.27 + 0.02, 0.23, zf - 0.12), CHROME, "lru")
    # cushion: a flat base slab, a crowned seat pad (two halves), side bolsters tilted in, a rolled front edge
    b.box((xc - 0.31, 0.38, zr), (xc + 0.31, 0.58, zf - 0.04), {"f": LD, "b": LD, "l": LD, "r": LD, "d": LD}, "fblrd")
    for s in (-1, 1):
        b.ob((xc + s * 0.11, 0.60, zm - 0.01), (0.23, 0.16, zf - zr - 0.06), rax("z", -s * 4.5), L, "u")
        b.ob((xc + s * 0.265, 0.66, zm - 0.03), (0.12, 0.22, zf - zr - 0.08), rax("z", s * 12), L, "ulrf")
    b.ob((xc, 0.62, zf - 0.07), (0.60, 0.14, 0.14), rax("x", 0), LD, "fu")
    for k in range(6):          # a rolled edge: slabs fanned about the x axis
        pass
    b.ring("x", (xc, 0.60, zf - 0.07), 0.085, 0.0, xc - 0.30, xc + 0.30, 8, L, start=-30.0, sweep=150.0, faces=("out",))
    # the back leans 10 degrees: everything on it is built upright and rotated about (xc, 0.72, zr)
    pv = np.array([xc, 0.72, zr + 0.02])
    Rb = rax("x", -10)

    def on_back(c):
        return pv + Rb @ (np.array(c) - pv)

    b.box((xc - 0.21, 0.72, zr - 0.04), (xc + 0.21, 1.30, zr + 0.06), {"f": LP, "b": BK, "u": L, "l": LD, "r": LD}, "fbu", R=Rb, pivot=pv)
    for s in (-1, 1):
        # the back's bolsters curl round the rider: three stacked slabs, each turned a little further forward
        for k in range(3):
            b.ob(on_back((xc + s * (0.262 - 0.012 * k), 0.84 + 0.19 * k, zr + 0.015 + 0.012 * k)), (0.10, 0.20, 0.17), Rb @ rax("y", s * (10 + 12 * k)), L, "fblru")
        b.ob(on_back((xc + s * 0.19, 1.30, zr + 0.02)), (0.15, 0.12, 0.12), Rb @ rax("y", s * 24), L, "fu")
    b.box((xc - 0.21, 1.27, zr - 0.05), (xc + 0.21, 1.35, zr + 0.07), L, "fbul", R=Rb, pivot=pv)
    # headrest on two posts, a padded roll behind the head
    for s in (-1, 1):
        b.box((xc + s * 0.10 - 0.016, 1.30, zr - 0.04), (xc + s * 0.10 + 0.016, 1.46, zr - 0.012), CHROME, "fblr", R=Rb, pivot=pv)
    b.box((xc - 0.18, 1.42, zr - 0.11), (xc + 0.18, 1.74, zr + 0.03), {"f": LP, "b": BK, "u": L, "l": L, "r": L}, "fbulr", R=Rb, pivot=pv)
    b.ob(on_back((xc, 1.745, zr - 0.04)), (0.34, 0.07, 0.12), Rb @ rax("x", 14), L, "fu")
    m.auto_center()
    return m

# ================================================================================================ windscreen
def screen_model(sheet, sheet_g):
    m = Model("car_screen")
    b = Bld(m, sheet, density=72)
    pv = (0.0, TOP, ZW)
    R = rax("x", -35)
    gl = Bld(m, sheet_g)
    H = 0.45
    # glass (both sides, thin) and the black fritted border is part of the glass paint
    gl.box((-1.34, TOP + 0.02, ZW - 0.005), (1.34, TOP + H - 0.004, ZW + 0.015), GLASSP, "fb", R=R, pivot=pv)
    for s in (-1, 1):
        b.box((1.35 if s > 0 else -1.41, TOP - 0.02, ZW - 0.025), (1.41 if s > 0 else -1.35, TOP + H + 0.008, ZW + 0.035), CHROME, "fblrud", R=R, pivot=pv)
    # no top rail: the glass ends in a bare, chrome-painted edge (a rail across the view would cost the rider a tenth of his forward frame)
    b.box((-1.41, TOP - 0.02, ZW - 0.025), (1.41, TOP + 0.008, ZW + 0.03), CHROME, "fblrud", R=R, pivot=pv)
    # wipers parked at the foot of the glass: a blade and an arm each, lying on the screen
    m.auto_center()
    return m


def mirror_model(name, side):
    """A wing mirror: chrome stalk off the screen post, a dark housing turned back at the rider with a glass face.  side=+1 left, -1 right."""
    m = Model(name)
    b = Bld(m, SHEET_REF[0], side, density=96)
    x = 1.44
    b.box((x - 0.01, 0.80, ZW - 0.03), (x + 0.27, 0.835, ZW + 0.03), CHROME, "fblrud")
    hx = x + 0.29
    R = rax("y", -8)
    b.box((hx - 0.035, 0.77, ZW - 0.085), (hx + 0.035, 0.87, ZW + 0.085), S(pt.vinyl, base="#202024", hard="tblr"), "flrud", R=R, pivot=(hx, 0.82, ZW))
    b.box((hx - 0.03, 0.78, ZW - 0.0896), (hx + 0.03, 0.86, ZW - 0.0846), S(cp.mirror_glass), "b", R=R, pivot=(hx, 0.82, ZW))
    m.auto_center()
    return m


# ================================================================================================ the tail
def tail_model(sheet):
    m = Model("car_tail")
    b = Bld(m, sheet)
    z0, z1 = -3.34, -1.12
    xs = list(np.linspace(-1.0, 1.0, 17))
    zs = list(np.linspace(z1, z0, 19))

    def deck(x, z):
        crown = 0.04 * (1 - x * x)
        narrow = 1.0 - 0.18 * smoothstep(-2.5, -3.3, z)
        y = float(deck_y(z)) + crown - 0.05 * smoothstep(0.6, 1.0, abs(x)) ** 1.6
        for xc in (0.70, -0.70):                  # teardrop fairings behind the headrests
            dx = (abs(x) - 0.70) / 0.27
            dz = (-1.14 - z) / 1.5
            if dx * dx < 1 and dz < 1:
                y += 0.40 * (1 - dx * dx) ** 0.9 * max(0.0, 1 - max(dz, 0.0)) ** 1.5 * (1 if x * xc > 0 else 0)
        return (x * narrow, y, z)

    b.loft(deck, xs, zs, 0.05, BODY, hint=(0, 1, 0))    # the rear panel (face 'b' towards the rear): lower panel, lamps, plate, exhausts
    b.box((-1.12, 0.14, -3.36), (1.12, 0.50, -3.30), {"b": BODY_NS, "d": UNDER, "l": BODY_NS, "r": BODY_NS}, "bd")
    b.box((-1.12, 0.46, -3.36), (1.12, 0.52, -3.28), BODY_NS, "bu")
    for sx in (1, -1):
        b.box((sx * 0.78 - 0.17, 0.27, -3.385), (sx * 0.78 + 0.17, 0.46, -3.34), S(cp.tail_lens), "b", emit=11)
        b.box((sx * 0.78 - 0.19, 0.25, -3.37), (sx * 0.78 + 0.19, 0.48, -3.33), CHROME, "bud")
        # twin exhausts: rings with a dark bore
        c = (sx * 0.42, 0.22, -3.40)
        b.ring("z", c, 0.065, 0.045, -3.52, -3.30, 12, {"out": CHROME, "a0": CHROME, "in": S(pt.rubber, base="#0a0a0b")}, faces=("out", "a0", "in"))
    b.box((-0.28, 0.22, -3.40), (0.28, 0.38, -3.37), S(cp.plate, text="TK3 015", rear=True), "b")
    b.box((-0.30, 0.21, -3.38), (0.30, 0.39, -3.365), CHROME, "bu")
    # bumper blade with overriders
    b.box((-1.08, 0.12, -3.44), (1.08, 0.18, -3.38), CHROME, "bud")
    for sx in (-0.74, 0.74):
        b.box((sx - 0.05, 0.1, -3.50), (sx + 0.05, 0.28, -3.38), CHROME, "bu")
    # fuel cap and the boot's seam are on the deck: a chrome disc on the left
    b.disc("y", (0.55, 0.0, -2.2), 0.08, float(deck_y(-2.2)) + 0.045, float(deck_y(-2.2)) + 0.06, 12, S(pt.metal), faces=("a1",))
    # underbody: rear axle, differential housing and exhaust pipes
    b.box((-1.2, 0.05, -2.9), (1.2, 0.09, -1.15), UNDER, "d")
    b.ring("x", (0.0, WYC, WZR), 0.06, 0.04, -1.45, 1.45, 8, S(cp.underbody), faces=("out",))
    b.box((-0.2, 0.22, -2.45), (0.2, 0.5, -2.15), S(cp.underbody), "fblrud")
    for sx in (-0.42, 0.42):
        b.box((sx - 0.04, 0.16, -3.3), (sx + 0.04, 0.22, -1.5), S(pt.metal, base="#6a6d72", bands=False), "udlr")
    m.auto_center()
    return m


# ================================================================================================ nose underbody
def front_axle(m, sheet):
    b = Bld(m, sheet)
    b.ring("x", (0.0, WYC, WZF), 0.055, 0.035, -1.45, 1.45, 8, S(cp.underbody), faces=("out",))
    b.box((-0.22, 0.2, 1.8), (0.22, 0.4, 2.1), S(cp.underbody), "fblrud")


# ================================================================================================ the whole car
class PartSpec:
    def __init__(self, name, model, group="body", at=None, R=None, scale=1.0, bright=None, only=None):
        self.name, self.model, self.group, self.at, self.R, self.scale, self.bright, self.only = name, model, group, at, R, scale, bright, only


class Vehicle:
    def __init__(self, name):
        self.name = name
        self.sheets = []
        self.models = {}
        self.parts = []

    def add_model(self, m):
        self.models[m.name] = m
        return m


def build_car(painted=True):
    v = Vehicle("car")
    main = Sheet("car_main", density=56, pad=2, max_size=4096)
    glass = Sheet("car_glass", density=64, pad=2, min_size=64, translucent=True)
    v.sheets = [main, glass]
    SHEET_REF[0] = main
    nose = v.add_model(nose_model(main))
    front_axle(nose, main)
    nose.auto_center()
    wf = {}
    for nm, side in (("fl", 1), ("fr", -1)):
        wf[nm] = v.add_model(wing_model(f"car_wing_{nm}", True, side, main, glass))
    wr = {}
    for nm, side in (("rl", 1), ("rr", -1)):
        wr[nm] = v.add_model(wing_model(f"car_wing_{nm}", False, side, main, glass))
    tub = v.add_model(tub_model(main))
    door = v.add_model(door_model(main))
    dash = v.add_model(dash_model(main))
    sl = v.add_model(seat_model("car_seat_l", SEAT_P[0], SEAT_P[2], main))
    sr = v.add_model(seat_model("car_seat_r", SEAT_D[0], SEAT_D[2], main))
    scr = v.add_model(screen_model(main, glass))
    mil = v.add_model(mirror_model("car_mirror_l", 1))
    mir = v.add_model(mirror_model("car_mirror_r", -1))
    tail = v.add_model(tail_model(main))
    wheel = v.add_model(wheel_model(main))
    v.parts = [PartSpec("nose", nose), PartSpec("wingFL", wf["fl"]), PartSpec("wingFR", wf["fr"]), PartSpec("wingRL", wr["rl"]), PartSpec("wingRR", wr["rr"]),
               PartSpec("tub", tub), PartSpec("doorL", door, group="door"), PartSpec("dash", dash), PartSpec("seatL", sl), PartSpec("seatR", sr),
               PartSpec("screen", scr), PartSpec("mirrorL", mil), PartSpec("mirrorR", mir), PartSpec("tail", tail)]
    for nm, x, z in (("FL", WX0 + (WX1 - WX0) / 2, WZF), ("RL", WX0 + (WX1 - WX0) / 2, WZR)):
        v.parts.append(PartSpec(f"wheel{nm}", wheel, group="wheel", at=(x, WYC, z)))
    for nm, x, z in (("FR", -(WX0 + (WX1 - WX0) / 2), WZF), ("RR", -(WX0 + (WX1 - WX0) / 2), WZR)):
        v.parts.append(PartSpec(f"wheel{nm}", wheel, group="wheel", at=(x, WYC, z), R=rax("y", 180)))
    return v
