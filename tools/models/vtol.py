"""A military VTOL of our own design: a stubby fuselage with a bubble canopy and a chin cannon, short swept wings, two ducted fans on tilting nacelles
at the wing tips (shown tilted 35 degrees up and forward, as in the transition to forward flight), and a V-tail; grey with invented markings (a
roundel with a red chevron, tail numerals, a red nose band so that it reads at a hundred blocks, orange lift glows).  Plus the burning wreck in four pieces.

Authored in "raw" units (nose +z, +x left, 4.2 long): the rig shows it at a scale (ride_air: 3.2 -> 13.4 blocks long, 17.4 across the fans).  Each model is
at most 3 raw units in every direction (one model's elements are limited to a 48-unit box).
"""
import math
from functools import partial

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import car_paint as cp
from . import paint as pt
from .car import PartSpec, Vehicle
from .mdl import Model, Sheet
from .paint import edge_fx, fbm, grain, mix, rgb, smooth, vnoise, white_noise
from .shapes import Bld, catmull, smoothstep
from .vmath import rax

DENS = 100


def S(f, **k):
    return partial(f, **k)


# ---------------------------------------------------------------------------------------------------- decals
_decal_cache = {}


def _roundel(size=256):
    key = ("roundel", size)
    if key not in _decal_cache:
        im = Image.new("RGBA", (size * 2, size * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        c = size
        d.ellipse((0, 0, 2 * size - 1, 2 * size - 1), fill=(230, 232, 236, 255))
        d.ellipse((size * 0.12, size * 0.12, 2 * size - 1 - size * 0.12, 2 * size - 1 - size * 0.12), fill=(24, 44, 110, 255))
        d.ellipse((size * 0.42, size * 0.42, 2 * size - 1 - size * 0.42, 2 * size - 1 - size * 0.42), fill=(230, 232, 236, 255))
        # a red chevron pointing forward (up in the decal)
        d.polygon([(c, size * 0.24), (c + size * 0.46, c + size * 0.5), (c + size * 0.26, c + size * 0.5), (c, size * 0.74), (c - size * 0.26, c + size * 0.5), (c - size * 0.46, c + size * 0.5)],
                  fill=(200, 32, 36, 255))
        _decal_cache[key] = np.asarray(im.resize((size, size), Image.LANCZOS), np.float32) / 255.0
    return _decal_cache[key]


def _text(text, size=256, aspect=2.0, color=(230, 232, 236)):
    key = ("text", text, size, aspect, color)
    if key not in _decal_cache:
        w, h = int(size * aspect), size
        im = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(cp.FONT_BOLD, int(h * 1.5))
        tw = d.textlength(text, font=f)
        d.text(((w * 2 - tw) / 2, h * 0.1), text, fill=color + (255,), font=f)
        _decal_cache[key] = np.asarray(im.resize((w, h), Image.LANCZOS), np.float32) / 255.0
    return _decal_cache[key]


def decal_apply(ctx, c, img, centre, right, up, w, h, normal):
    """Blend a decal onto texels whose position lies within the w x h rectangle (in the plane through `centre` with axes right/up) and whose
    face looks along `normal`."""
    if float(np.dot(ctx.N, normal)) < 0.55:
        return c
    d = ctx.P - np.array(centre, np.float32)
    a = d @ np.array(right, np.float32) / w
    b = d @ np.array(up, np.float32) / h
    inside = (np.abs(a) < 0.5) & (np.abs(b) < 0.5)
    if not inside.any():
        return c
    H, W = img.shape[:2]
    ix = np.clip(((a + 0.5) * W).astype(int), 0, W - 1)
    iy = np.clip(((0.5 - b) * H).astype(int), 0, H - 1)
    px = img[iy, ix]
    al = (px[..., 3] * inside)[..., None]
    return c * (1 - al) + px[..., :3] * al


DECALS = []     # (img, centre, right, up, w, h, normal)


def _init_decals():
    if DECALS:
        return
    ro = _roundel()
    for sx in (1, -1):
        # fuselage sides, forward of the wing
        DECALS.append((ro, (0.52 * sx, 0.05, 0.95), (0, 0, -sx), (0, 1, 0), 0.34, 0.34, (sx, 0, 0)))
        # tail numerals on the sides of the rear fuselage and the fins
        DECALS.append((_text("07", 192, 1.4), (0.5 * sx, 0.12, -1.35), (0, 0, -sx), (0, 1, 0), 0.50, 0.28, (sx, 0, 0)))
    # roundels on the top of the wings
    for sx in (1, -1):
        DECALS.append((ro, (1.02 * sx, 0.13, -0.25), (-1, 0, 0), (0, 0, 1), 0.42, 0.42, (0, 1, 0)))
        DECALS.append((_text("SK-3", 192, 1.9, (40, 44, 50)), (1.18 * sx, 0.13, -0.55), (-1, 0, 0), (0, 0, 1), 0.50, 0.17, (0, 1, 0)))
    DECALS.append((_text("SORA", 160, 2.4, (60, 64, 70)), (0.0, 0.5, -0.2), (-1, 0, 0), (0, 0, 1), 0.5, 0.2, (0, 1, 0)))


def air_skin(ctx, base="#9ba2a9", seed=31, panel=0.46, dirt=1.0, nose_band=True, **kw):
    """Fuselage / wing skin: light grey, a darker belly, panel lines and rivet rows, soot streaks aft of the fans, the red nose band and the decals."""
    _init_decals()
    P, N = ctx.P, ctx.N
    x, y, z = P[..., 0], P[..., 1], P[..., 2]
    c = np.broadcast_to(rgb(base), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.86 + 0.20 * smooth(-0.3, 0.5, y) + 0.06 * max(N[1], 0.0))[..., None]
    # a darker belly
    c = c * (1 - 0.28 * (N[1] < -0.3))
    n = fbm(P, 3.5, seed, 3)
    c = c * (0.92 + 0.16 * n)[..., None]
    # panel lines: across the body every `panel` and along it at a few heights
    pl = np.exp(-((np.mod(z / panel + 0.37, 1.0) - 0.5) / 0.012 / (panel / 0.46)) ** 2) * 0.0
    gz = np.abs(np.mod(z + 0.11, panel) - panel / 2)
    line_z = (gz > panel / 2 - 0.012)
    gx = np.abs(np.mod(x + 0.07, 0.62) - 0.31)
    line_x = (gx > 0.31 - 0.010) & (abs(N[1]) > 0.6)
    gy = np.abs(np.mod(y + 0.05, 0.32) - 0.16)
    line_y = (gy > 0.16 - 0.010) & (abs(N[1]) < 0.6)
    lines = (line_z | line_x | line_y)
    c = np.where(lines[..., None], c * 0.62, c)
    rivets = (np.abs(np.mod(z * 22.0, 1.0) - 0.5) < 0.12) & (np.abs(gz - (panel / 2 - 0.035)) < 0.006)
    c = np.where(rivets[..., None], c * 0.72, c)
    # soot streaks behind the nacelles and the gun, grime low down
    soot = smooth(0.62, 0.9, fbm(P * np.array([1.0, 1.0, 0.25], np.float32), 6.0, seed + 4, 3)) * 0.55
    c = c * (1 - soot * 0.55 * dirt)[..., None]
    c = c * (1 - 0.25 * smooth(0.1, -0.3, y) * (0.5 + n) * dirt)[..., None]
    # the red nose band and a white pinstripe either side
    if nose_band:
        band = (z > 1.52) & (z < 1.78) & (z < 2.4)
        edge = ((z > 1.46) & (z <= 1.52)) | ((z >= 1.78) & (z < 1.84))
        c = np.where(band[..., None], rgb("#c2262a") * (0.85 + 0.2 * n)[..., None], c)
        c = np.where(edge[..., None], rgb("#eceef0") * (0.9 + 0.1 * n)[..., None], c)
    for img, cen, right, upv, w, h, nrm in DECALS:
        c = decal_apply(ctx, c, img, cen, right, upv, w, h, np.array(nrm, np.float32))
    c = grain(ctx, c, 0.03, 90, seed)
    return edge_fx(ctx, c, "", ao=0.0, hl=0.0) if False else np.clip(c, 0, 1)


def dark_panel(ctx, base="#2a2e33", seed=32, **kw):
    c = pt.painted(ctx, base=base, hard="", seed=seed, dirt=0.3)
    return c


def fan_face(ctx, centre=(0, 0, 0), axis=(0, 1, 0), r=0.53, seed=33, **kw):
    """A ducted fan seen down its axis: 11 swept blades, a hub and a stator ring, in grey-blue metal with a darker well."""
    d = ctx.P - np.array(centre, np.float32)
    ax = np.array(axis, np.float32)
    ax = ax / np.linalg.norm(ax)
    dd = d - (d @ ax)[..., None] * ax
    rr = np.linalg.norm(dd, axis=-1)
    e1 = np.cross(ax, [1.0, 0.0, 0.0])
    e1 = e1 / np.linalg.norm(e1)
    e2 = np.cross(ax, e1)
    th = np.arctan2(dd @ e2, dd @ e1)
    c = np.broadcast_to(rgb("#262a30"), (ctx.h, ctx.w, 3)).copy()
    nb = 11
    ph = np.mod(th / (2 * math.pi) * nb + 0.55 * (rr / r), 1.0)
    blade = (np.abs(ph - 0.5) < 0.34) & (rr > 0.1) & (rr < r)
    shade = 0.55 + 0.5 * np.cos(th * nb + 3.0 * rr / r)
    c = np.where(blade[..., None], rgb("#8b939c") * shade[..., None], c)
    c = np.where((rr < 0.1)[..., None], rgb("#c9ced4"), c)
    c = np.where(((rr > r * 0.92) & (rr <= r))[..., None], rgb("#6b7279"), c)
    c = np.where((rr > r)[..., None], rgb("#33373d"), c)
    return np.clip(c * (0.9 + 0.2 * vnoise(ctx.P, 25.0, seed)[..., None]), 0, 1)


def glow(ctx, **kw):
    c = np.broadcast_to(rgb("#ff8a22"), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.85 + 0.25 * vnoise(ctx.P, 18.0, 2)[..., None])
    return np.clip(c, 0, 1)


def glass_amber(ctx, **kw):
    return pt.glass(ctx, tint="#4a6a80", alpha=0.55, hard="", streak=True)


def scorch(ctx, base="#6a6f74", seed=41, soot=0.8, **kw):
    """The wreck's skin: the grey paint burnt black and brown, blistered, with cracked panel lines and the odd bright scrap."""
    P = ctx.P
    c = air_skin(ctx, base=base, seed=seed, dirt=1.5, nose_band=False)
    n = fbm(P, 3.0, seed, 4)
    burn = smooth(0.35, 0.7, n + 0.15 * (1 - np.clip(P[..., 1] / 0.4 + 0.5, 0, 1)))
    c = mix(c, rgb("#161412") * (0.7 + 0.5 * vnoise(P, 30.0, seed))[..., None] if False else rgb("#161412"), burn * soot)
    rust = smooth(0.55, 0.8, fbm(P, 7.0, seed + 2, 3))
    c = mix(c, rgb("#5a3a22"), rust * 0.35 * (1 - burn * soot))
    # embers: small bright flecks in the deepest burn
    em = (fbm(P, 22.0, seed + 5, 2) > 0.78) & (burn > 0.85)
    c = np.where(em[..., None], np.array([1.0, 0.45, 0.12], np.float32) * (0.6 + 0.4 * white_noise(ctx, seed))[..., None], c)
    return np.clip(c, 0, 1)


def exposed(ctx, seed=42, **kw):
    """The inside of a torn fuselage: dark ribs and insulation, singed."""
    c = np.broadcast_to(rgb("#2a2420"), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.6 + 0.9 * fbm(ctx.P, 8.0, seed, 3))[..., None]
    hot = smooth(0.7, 0.86, fbm(ctx.P, 12.0, seed + 2, 3))
    c = mix(c, np.array([0.95, 0.4, 0.1], np.float32), hot * 0.55)
    return np.clip(c, 0, 1)


SKIN = S(air_skin)
DARK = S(dark_panel)
STEEL = S(pt.metal, base="#8a9097", bands=True)
SOOT = S(pt.vinyl, base="#17181a", hard="")


# ---------------------------------------------------------------------------------------------------- geometry
def section(z, w, yt, yb, c=0.2, n=8):
    """A rounded-rectangle cross-section (8 points) at station z: half width w, top yt, bottom yb, corner cut c."""
    cc = c * w
    return z, [(w - cc, yt), (w, yt - 2 * cc), (w, yb + 2 * cc), (w - cc, yb), (-(w - cc), yb), (-w, yb + 2 * cc), (-w, yt - 2 * cc), (-(w - cc), yt)]


def tube(b, secs, style, t=0.04, hint_sign=1, closed=True, centre_fn=None, **kw):
    """Skin between successive sections (each (z, [(x, y)...])): one slab per quad, hint pointing away from the section's centre."""
    for (z0, p0), (z1, p1) in zip(secs[:-1], secs[1:]):
        n = len(p0)
        rng = range(n) if closed else range(n - 1)
        for j in rng:
            j2 = (j + 1) % n
            A = (p0[j][0], p0[j][1], z0)
            B = (p0[j2][0], p0[j2][1], z0)
            C = (p1[j][0], p1[j][1], z1)
            D = (p1[j2][0], p1[j2][1], z1)
            cx = sum(p[0] for p in p0) / n
            cy = sum(p[1] for p in p0) / n
            mx = (A[0] + B[0] + C[0] + D[0]) / 4 - cx
            my = (A[1] + B[1] + C[1] + D[1]) / 4 - cy
            h = (mx * hint_sign, my * hint_sign, 0.0)
            if abs(h[0]) + abs(h[1]) < 1e-6:
                h = (0, 1, 0)
            b.strip(A, B, C, D, t, style, "u", h, grow=0.10, **kw)


def fuselage_secs(z0, z1):
    prof = {
        "w": catmull([(-2.25, 0.16), (-1.85, 0.34), (-1.0, 0.46), (-0.2, 0.50), (0.6, 0.50), (1.2, 0.46), (1.7, 0.34), (2.05, 0.2), (2.3, 0.1)]),
        "yt": catmull([(-2.25, 0.20), (-1.85, 0.30), (-1.0, 0.40), (-0.2, 0.44), (0.6, 0.46), (1.2, 0.40), (1.7, 0.26), (2.05, 0.10), (2.3, 0.02)]),
        "yb": catmull([(-2.25, -0.16), (-1.85, -0.24), (-1.0, -0.31), (-0.2, -0.32), (0.6, -0.30), (1.2, -0.27), (1.7, -0.21), (2.05, -0.12), (2.3, -0.05)]),
    }
    zs = np.linspace(z0, z1, max(3, int(abs(z1 - z0) / 0.3) + 1))
    return [section(float(z), float(prof["w"](z)), float(prof["yt"](z)), float(prof["yb"](z))) for z in zs]


def fuselage_model(sheet, sheet_g):
    m = Model("vtol_fuselage")
    b = Bld(m, sheet, density=DENS)
    secs = fuselage_secs(-2.25, 0.5)
    tube(b, secs, SKIN)
    # tail cone: the exhaust nozzle at the rear, glowing
    zt, pts = secs[0]
    b.ring("z", (0.0, 0.02, -2.28), 0.15, 0.11, -2.42, -2.2, 12, {"out": S(pt.metal, base="#5b6168"), "a0": S(pt.metal, base="#5b6168"), "in": SOOT}, faces=("out", "a0", "in"))
    b.disc("z", (0.0, 0.02, -2.28), 0.115, -2.30, -2.28, 12, S(glow), faces=("a0",), emit=15)
    # the spine fairing and the intake scoops on the shoulders
    b.ob((0.0, 0.46, -0.55), (0.34, 0.1, 1.6), rax("x", 0), SKIN, "ufblr")
    for sx in (1, -1):
        b.ob((0.52 * sx, 0.22, -0.2), (0.14, 0.2, 0.5), rax("z", 0), DARK, "fulr")
    m.auto_center()
    return m


def nose_model(sheet, sheet_g):
    m = Model("vtol_nose")
    b = Bld(m, sheet, density=DENS)
    gl = Bld(m, sheet_g, density=DENS)
    secs = fuselage_secs(0.5, 2.3)
    tube(b, secs, SKIN)
    # canopy: a glass bubble over z 0.45..1.55 on a dark sill, with a frame
    cz = [0.42, 0.62, 0.9, 1.2, 1.45, 1.62]
    cw = [0.30, 0.36, 0.38, 0.36, 0.28, 0.14]
    csecs = []
    for z, w in zip(cz, cw):
        ybase = 0.44 - 0.05 * (z - 0.4)
        top = ybase + 0.30 * (w / 0.38)
        pts = [(w, ybase), (w * 0.86, ybase + 0.55 * (top - ybase)), (w * 0.45, top - 0.02), (0.0, top), (-w * 0.45, top - 0.02), (-w * 0.86, ybase + 0.55 * (top - ybase)), (-w, ybase)]
        csecs.append((z, pts))
    tube(gl, csecs, S(glass_amber), t=0.02, closed=False)
    for z, pts in csecs[1:-1:1]:
        # frame ribs: thin dark bars along the canopy's outline, one per station
        for j in range(len(pts) - 1):
            p, q = pts[j], pts[j + 1]
            mx, my = (p[0] + q[0]) / 2, (p[1] + q[1]) / 2
            ln = math.hypot(q[0] - p[0], q[1] - p[1])
            ang = math.degrees(math.atan2(q[1] - p[1], q[0] - p[0]))
            b.ob((mx, my, z), (ln * 1.05, 0.025, 0.03), rax("z", ang), DARK, "ufblrd")
    b.box((-0.34, 0.40, 0.42), (0.34, 0.45, 1.62), DARK, "u")
    # chin: a sensor ball and the cannon with its blast tube
    b.ring("x", (0.0, -0.20, 1.75), 0.11, 0.0, -0.1, 0.1, 10, S(pt.metal, base="#2c3036"), faces=("out",), start=0.0, sweep=360.0)
    b.box((-0.09, -0.32, 1.4), (0.09, -0.18, 1.95), DARK, "fblrud")
    b.ring("z", (0.0, -0.25, 2.2), 0.055, 0.03, 1.9, 2.75, 8, {"out": S(pt.metal, base="#41464c"), "a1": S(pt.metal, base="#41464c"), "in": SOOT}, faces=("out", "a1", "in"))
    b.ring("z", (0.0, -0.25, 2.62), 0.075, 0.05, 2.58, 2.76, 8, S(pt.metal, base="#2a2d32"), faces=("out", "a1"))
    # a pitot boom on the nose
    b.box((-0.012, 0.0, 2.25), (0.012, 0.024, 2.62), S(pt.metal), "fblrud")
    m.auto_center()
    return m


def wing_model(name, side, sheet):
    """One swept wing (side=+1 left): upper and lower skin lofted over span and chord, rounded leading edge, a weapon pylon with a small missile."""
    m = Model(name)
    b = Bld(m, sheet, side, density=DENS)
    xr, xt = 0.40, 1.62
    lead = lambda u: 0.60 - 0.50 * u
    trail = lambda u: -0.95 + 0.36 * u
    thick = lambda u: 0.15 - 0.07 * u
    us = np.linspace(0.0, 1.0, 9)
    vs = np.linspace(0.0, 1.0, 6)

    def top(u, v):
        x = xr + u * (xt - xr)
        z = lead(u) + v * (trail(u) - lead(u))
        t = thick(u)
        return (x, 0.04 + t * 0.5 * (0.45 + 0.55 * math.sin(math.pi * min(v * 1.0, 1.0)) ** 0.8) - 0.02 * u, z)

    def bot(u, v):
        x, y, z = top(u, v)
        return (x, 0.04 - thick(u) * 0.5 * (0.45 + 0.55 * math.sin(math.pi * v) ** 0.8) - 0.02 * u, z)

    b.loft(top, list(us), list(vs), 0.03, SKIN, hint=(0, 1, 0))
    b.loft(bot, list(us), list(vs), 0.03, SKIN, hint=(0, -1, 0))
    # leading and trailing edges and the tip cap
    for k in range(len(us) - 1):
        u0, u1 = us[k], us[k + 1]
        for v, h in ((0.0, (0, 0, 1)), (1.0, (0, 0, -1))):
            A, B_ = top(u0, v), top(u1, v)
            C, D = bot(u0, v), bot(u1, v)
            b.strip(A, B_, C, D, 0.03, SKIN, "u", h, grow=0.1)
    A, B_, C, D = top(1.0, 0.0), top(1.0, 1.0), bot(1.0, 0.0), bot(1.0, 1.0)
    b.strip(A, B_, C, D, 0.03, SKIN, "u", (1, 0, 0), grow=0.1)
    # weapon pylon and missile under the wing
    b.box((0.98, -0.16, -0.30), (1.04, -0.02, 0.0), DARK, "fblr")
    b.ring("z", (1.01, -0.2, -0.2), 0.05, 0.0, -0.62, 0.38, 8, S(pt.painted, base="#c9ccd0", hard="", dirt=0.2), faces=("out", "a1"))
    b.ring("z", (1.01, -0.2, -0.2), 0.052, 0.04, 0.3, 0.38, 8, S(pt.painted, base="#a22b2b", hard="", dirt=0.1), faces=("out", "a1"))
    m.auto_center()
    return m


def nacelle_model(name, side, sheet):
    """A ducted fan on its pylon at the wing tip, tilted 35 degrees up and forward: duct ring, fan face, dark well, glowing exhaust lip underneath."""
    m = Model(name)
    b = Bld(m, sheet, side, density=DENS)
    c = np.array([2.18, 0.12, 0.05])
    R0 = rax("x", 35)
    ax_dir = R0 @ np.array([0.0, 1.0, 0.0])
    rout, rin = 0.56, 0.48
    a0, a1 = c[1] - 0.34, c[1] + 0.34
    # the duct: 14 slabs round the axis, skin outside, dark liner inside; the exhaust lip (bottom, a0) glows
    b.ring("y", tuple(c), rout, rin, a0, a1, 14, {"out": SKIN, "in": DARK, "a1": S(pt.metal, base="#8e949b"), "a0": S(glow)}, faces=("out", "in", "a1", "a0"), R0=R0, emit=0)
    # glow only on the lower lip: a thin ring of emissive slabs
    b.ring("y", tuple(c), rin + 0.005, rin - 0.04, a0 - 0.0, a0 + 0.035, 14, S(glow), faces=("a0", "in"), R0=R0, emit=15)
    # glowing exhaust plate under the duct (reads from the street as the old orange lift glows did)
    b.ob(tuple(c + R0 @ np.array([0.0, -0.36, 0.0])), (0.62, 0.03, 0.62), R0, S(glow), "d", emit=15)
    # fan, hub, stator vanes
    fc = tuple(c + ax_dir * 0.0)
    b.disc("y", tuple(c), rin - 0.01, c[1] + 0.04, c[1] + 0.06, 14, {"a1": S(fan_face, centre=tuple(c + R0 @ np.array([0, 0.05, 0])), axis=tuple(ax_dir), r=rin - 0.01), "a0": DARK}, faces=("a1", "a0"), R0=R0)
    # the wing tip carries a pylon to the duct: a box that bridges, and a small pod behind the duct
    b.box((1.55, 0.04, -0.15), (2.0, 0.2, 0.25), DARK if False else SKIN, "fbudl")
    b.ob(tuple(c + np.array([0.0, -0.18, -0.3])), (0.5, 0.2, 0.6), rax("x", 20), SKIN, "fbudl")
    m.auto_center()
    return m


def tail_model(sheet):
    m = Model("vtol_tail")
    b = Bld(m, sheet, density=DENS)
    # V-tail: two canted fins
    for sx in (1, -1):
        c = np.array([0.30 * sx, 0.55, -1.75])
        R = rax("z", -sx * 26)
        # a tapered fin = two slabs: a root slab and a tip slab swept back
        b.ob(tuple(c), (0.06, 0.8, 0.85), R, SKIN, "fblrud")
        cc = np.array([0.30 * sx, 0.0, -1.75]) + R @ np.array([0.0, 0.42, -0.1])
        b.ob(tuple(cc), (0.05, 0.14, 0.6), R, S(air_skin, nose_band=False), "fblrud")
    b.box((-0.2, 0.24, -2.0), (0.2, 0.34, -1.45), SKIN, "fulr")
    m.auto_center()
    return m


# ---------------------------------------------------------------------------------------------------- the wreck
def _broken(b, secs, tear_z, seed, end="back"):
    """The skin as built plus a ragged torn end: ribs, plates and singed insulation sticking out."""
    rnd = np.random.RandomState(seed)
    z, pts = secs[0] if end == "back" else secs[-1]
    for j in range(len(pts)):
        if rnd.rand() < 0.8:
            p = pts[j]
            L = 0.07 + 0.16 * rnd.rand()
            ang = rnd.uniform(-35, 35)
            c = np.array([p[0] * 0.93, p[1] * 0.93, tear_z + (-L / 2 if end == "back" else L / 2)])
            b.ob(tuple(c), (0.07 + 0.08 * rnd.rand(), 0.20 + 0.25 * rnd.rand(), L), rax("x", ang) @ rax("z", rnd.uniform(-35, 35)), S(scorch), "fblrud")
    for k in range(4):
        c = np.array([rnd.uniform(-0.3, 0.3), rnd.uniform(-0.22, 0.28), tear_z + (-0.05 if end == "back" else 0.05)])
        b.ob(tuple(c), (0.05, 0.38, 0.05), rax("z", rnd.uniform(0, 180)), S(exposed), "fblrud")
    # smouldering scraps in the tear: a few small glowing slabs
    for k in range(6):
        c = np.array([rnd.uniform(-0.35, 0.35), rnd.uniform(-0.25, 0.3), tear_z + rnd.uniform(-0.06, 0.06)])
        b.ob(tuple(c), (0.05 + 0.06 * rnd.rand(), 0.04 + 0.05 * rnd.rand(), 0.05), rax("z", rnd.uniform(0, 180)), S(glow), "fblrud", emit=8)


def wreck_models(sheet, sheet_g):
    out = []
    scorch_s = S(scorch)
    # 1. the nose section: front fuselage with the cannon, a bent canopy frame, torn at the back
    m = Model("vtol_wreck_nose")
    b = Bld(m, sheet, density=DENS)
    secs = fuselage_secs(0.9, 2.3)
    tube(b, secs, scorch_s)
    b.ring("z", (0.0, -0.25, 2.2), 0.055, 0.03, 1.9, 2.75, 8, S(pt.metal, base="#2a2c30"), faces=("out", "a1"))
    _broken(b, secs, 0.9, 1, "back")
    for k in range(4):
        b.ob((0.0, 0.40, 1.0 + 0.2 * k), (0.6, 0.03, 0.03), rax("z", 4 * k - 6), S(exposed), "ufblrd")
    m.auto_center()
    out.append(m)
    # 2. the middle: a fuselage stub with one wing root and a bent nacelle
    m = Model("vtol_wreck_mid")
    b = Bld(m, sheet, density=DENS)
    secs = fuselage_secs(-1.3, 0.45)
    tube(b, secs, scorch_s)
    _broken(b, secs, 0.45, 2, "front")
    _broken(b, secs, -1.3, 3, "back")
    # a wing stub: a tilted slab
    b.ob((1.0, 0.0, -0.2), (1.2, 0.1, 1.2), rax("z", 8) @ rax("y", -12), scorch_s, "fblrud")
    b.ob((1.62, 0.1, -0.1), (0.5, 0.08, 0.8), rax("z", 20) @ rax("y", -25), scorch_s, "fblrud")
    m.auto_center()
    out.append(m)
    # 3. the tail: the rear fuselage with one fin snapped over and the nozzle
    m = Model("vtol_wreck_tail")
    b = Bld(m, sheet, density=DENS)
    secs = fuselage_secs(-2.25, -1.2)
    tube(b, secs, scorch_s)
    _broken(b, secs, -1.2, 4, "front")
    b.ring("z", (0.0, 0.02, -2.28), 0.15, 0.11, -2.42, -2.2, 12, S(pt.metal, base="#2a2c30"), faces=("out", "in"))
    b.ob((0.35, 0.5, -1.8), (0.06, 0.8, 0.85), rax("z", -30), scorch_s, "fblrud")
    b.ob((-0.62, 0.1, -1.9), (0.06, 0.8, 0.8), rax("z", 80), scorch_s, "fblrud")
    m.auto_center()
    out.append(m)
    # 4. a fan duct torn off its pylon, lying on its side
    m = Model("vtol_wreck_nacelle")
    b = Bld(m, sheet, density=DENS)
    c = (0.0, 0.0, 0.0)
    b.ring("y", c, 0.64, 0.55, -0.34, 0.34, 14, {"out": scorch_s, "in": S(exposed), "a0": scorch_s, "a1": scorch_s}, faces=("out", "in", "a0", "a1"))
    b.disc("y", c, 0.54, 0.0, 0.02, 14, S(fan_face, centre=(0, 0, 0), axis=(0, 1, 0), r=0.53), faces=("a1", "a0"))
    b.ob((0.0, 0.0, 0.6), (0.5, 0.2, 0.6), rax("x", 20), scorch_s, "fblrud")
    m.auto_center()
    out.append(m)
    return out


def build_vtol():
    v = Vehicle("vtol")
    main = Sheet("vtol_main", density=DENS, pad=3, max_size=2048)
    glass = Sheet("vtol_glass", density=DENS, pad=2, min_size=64, translucent=True)
    v.sheets = [main, glass]
    P = v.parts
    fus = v.add_model(fuselage_model(main, glass))
    nose = v.add_model(nose_model(main, glass))
    wl = v.add_model(wing_model("vtol_wing_l", 1, main))
    wr = v.add_model(wing_model("vtol_wing_r", -1, main))
    nl = v.add_model(nacelle_model("vtol_nac_l", 1, main))
    nr = v.add_model(nacelle_model("vtol_nac_r", -1, main))
    tl = v.add_model(tail_model(main))
    for nm, mm in (("fuselage", fus), ("nose", nose), ("wingL", wl), ("wingR", wr), ("nacL", nl), ("nacR", nr), ("tail", tl)):
        P.append(PartSpec(nm, mm, group="vtol"))
    v.wreck = [v.add_model(m) for m in wreck_models(main, glass)]
    return v
