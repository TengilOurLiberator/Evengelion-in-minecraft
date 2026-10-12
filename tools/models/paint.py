"""Procedural painters for face textures (numpy).  A painter is `f(ctx, **kw) -> (h, w, 3 or 4)` float array in 0..1; `ctx` is a mdl.PaintCtx whose
P gives the rig-space position of every texel, so paint can depend on where the surface is (height above ground, distance from a wheel, the
bonnet stripe...) and neighbouring panels line up without seams."""
import math
import os

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))


def rgb(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


def smooth(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0 + 1e-12), 0, 1)
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    t = np.asarray(t, np.float32)
    if t.ndim == 2:
        t = t[..., None]
    return a * (1 - t) + b * t


def _hash(ix, iy, iz, seed):
    n = (ix.astype(np.uint32) * np.uint32(374761393)) + (iy.astype(np.uint32) * np.uint32(668265263)) + \
        (iz.astype(np.uint32) * np.uint32(2246822519)) + np.uint32(seed * 3266489917 % (1 << 32))
    n = (n ^ (n >> np.uint32(13))) * np.uint32(1274126177)
    n = n ^ (n >> np.uint32(16))
    return (n & np.uint32(0xFFFFFF)).astype(np.float32) / np.float32(0xFFFFFF)


def vnoise(P, f, seed=0):
    """3D value noise in 0..1 at frequency f (cells per block)."""
    Q = P * f
    I = np.floor(Q)
    F = Q - I
    F = F * F * (3 - 2 * F)
    ix, iy, iz = I[..., 0].astype(np.int64), I[..., 1].astype(np.int64), I[..., 2].astype(np.int64)
    fx, fy, fz = F[..., 0], F[..., 1], F[..., 2]
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                h = _hash(ix + dx, iy + dy, iz + dz, seed)
                w = (fx if dx else 1 - fx) * (fy if dy else 1 - fy) * (fz if dz else 1 - fz)
                out = out + h * w
    return out.astype(np.float32)


def fbm(P, f, seed=0, octaves=3):
    tot, amp, norm = 0.0, 1.0, 0.0
    for o in range(octaves):
        tot = tot + amp * vnoise(P, f * (2 ** o), seed + o * 17)
        norm += amp
        amp *= 0.5
    return tot / norm


def white_noise(ctx, seed=0):
    """Per-texel noise that is the same for coplanar overlapping panels (hash of the texel's position, 1 mm quantised)."""
    q = np.floor(ctx.P * 256).astype(np.int64)
    return _hash(q[..., 0], q[..., 1], q[..., 2], seed)


def edge_fx(ctx, col, hard="tblr", ao=0.28, ao_w=0.06, hl=0.20, hl_w=1.3, dark_line=0.0, dark_w=0.0):
    """Edge treatment of a panel: ambient-occlusion darkening towards the edges that meet another panel, a bright 1-2 texel bevel highlight on
    the upper/left edges and a darker one on the lower/right edges.  `hard` = the edges that get it: t(op) b(ottom) l(eft) r(ight)."""
    big = np.float32(9.0)
    dt = ctx.dt if "t" in hard else np.full_like(ctx.dt, big)
    db = ctx.db if "b" in hard else np.full_like(ctx.db, big)
    dl = ctx.dl if "l" in hard else np.full_like(ctx.dl, big)
    dr = ctx.dr if "r" in hard else np.full_like(ctx.dr, big)
    d = np.minimum(np.minimum(dt, db), np.minimum(dl, dr))
    if ao:
        col = col * (1 - ao * (1 - smooth(0.0, ao_w, d)))[..., None]
    px = ctx.px
    if hl:
        w = max(hl_w * px, 1e-4)
        up = np.minimum(dt, dl) < w
        low = np.minimum(db, dr) < w
        col = np.where(up[..., None], np.minimum(col * (1 + hl) + hl * 0.35, 1.0), col)
        col = np.where(low[..., None] & ~up[..., None], col * (1 - hl * 0.9), col)
    if dark_line:
        m = d < max(dark_w, 1e-4)
        col = np.where(m[..., None], col * (1 - dark_line), col)
    return col


def grain(ctx, col, amt=0.025, f=90.0, seed=1):
    n = vnoise(ctx.P, f, seed) - 0.5
    n2 = white_noise(ctx, seed + 5) - 0.5
    return col * (1 + amt * (n * 1.4 + n2 * 0.9))[..., None]


def solid(ctx, color="#808080", **kw):
    return np.broadcast_to(rgb(color), (ctx.h, ctx.w, 3)).copy()


# ---------------------------------------------------------------------------------------------------- generic materials
def metal(ctx, base="#c9ccd2", hard="tblr", bands=True, tint=None, dark=0.0, seed=2, **kw):
    """Chrome / polished steel: brightness follows the facet's normal (so ring segments and tilted slabs read as a curved reflector), plus a
    horizon band and a hot streak along the face."""
    c = np.broadcast_to(rgb(base), (ctx.h, ctx.w, 3)).copy()
    N = ctx.N
    if bands:
        refl = 0.5 + 0.55 * N[1] + 0.25 * math.sin(N[0] * 3.1 + N[2] * 2.3)
        s = 0.58 + 0.40 * min(max(refl, 0.0), 1.0)
        t = ctx.V if abs(ctx.vh[1]) > 0.5 else ctx.U
        s = s + 0.14 * np.exp(-((t - 0.3) / 0.16) ** 2) - 0.10 * np.exp(-((t - 0.78) / 0.12) ** 2)
        c = c * s[..., None]
    if tint is not None:
        c = c * rgb(tint)
    c = c * (1 - dark)
    c = edge_fx(ctx, c, hard, ao=0.12, ao_w=0.03, hl=0.25)
    return grain(ctx, c, 0.02, 120, seed)

def rubber(ctx, base="#1b1b1e", hard="", seed=3, **kw):
    c = np.broadcast_to(rgb(base), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.85 + 0.3 * vnoise(ctx.P, 40.0, seed))[..., None]
    if hard:
        c = edge_fx(ctx, c, hard, ao=0.3, ao_w=0.04, hl=0.1)
    return c


def leather(ctx, base="#c4915a", hard="tblr", piping=None, stitch=True, seed=4, ao=0.30, pipe=0.5, **kw):
    """Tan leather: grain, soft shading, a slightly darker piping line a little in from the edge and a row of stitches beside it."""
    b = rgb(base)
    c = np.broadcast_to(b, (ctx.h, ctx.w, 3)).copy()
    g = fbm(ctx.P, 60.0, seed, 3)
    c = c * (0.90 + 0.20 * g)[..., None]
    c = c * (0.92 + 0.10 * fbm(ctx.P, 6.0, seed + 9, 2))[..., None]
    d = np.full_like(ctx.dl, 9.0)
    for ch, arr in (("t", ctx.dt), ("b", ctx.db), ("l", ctx.dl), ("r", ctx.dr)):
        if ch in hard:
            d = np.minimum(d, arr)
    pw = 0.011
    pl = np.exp(-((d - 0.045) / pw) ** 2)
    pc = rgb(piping) if piping else b * 0.62
    c = mix(c, pc, pipe * pl)
    if stitch:
        along = np.where(np.abs(ctx.dt - d) < 1e-6, ctx.dl, np.where(np.abs(ctx.db - d) < 1e-6, ctx.dl, ctx.dt))
        dash = (np.floor(along * 45) % 2 == 0)
        st = (np.abs(d - 0.075) < 0.005) & dash
        c = np.where(st[..., None], c * 0.72, c)
    return edge_fx(ctx, c, hard, ao=ao, ao_w=0.07, hl=0.10)

def vinyl(ctx, base="#232326", hard="", seed=5, tex=0.06, **kw):
    """Dash and trim: dark, pebbled."""
    c = np.broadcast_to(rgb(base), (ctx.h, ctx.w, 3)).copy()
    n = white_noise(ctx, seed) - 0.5
    c = c * (1 + tex * n * 2 + 0.06 * (fbm(ctx.P, 30.0, seed, 2) - 0.5))[..., None]
    if hard:
        c = edge_fx(ctx, c, hard, ao=0.3, ao_w=0.05, hl=0.18)
    return c


def painted(ctx, base="#5a6068", hard="tblr", seed=6, dirt=0.15, ao=0.25, **kw):
    """Plain painted steel: any colour, soft gradient, grain, edge fx."""
    c = np.broadcast_to(rgb(base), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.92 + 0.16 * smooth(-0.2, 1.2, ctx.P[..., 1]))[..., None]
    c = c * (1 - dirt * (1 - smooth(0.0, 0.5, ctx.P[..., 1])) * (0.5 + fbm(ctx.P, 5.0, seed, 3)))[..., None]
    c = grain(ctx, c, 0.04, 70.0, seed)
    return edge_fx(ctx, c, hard, ao=ao, ao_w=0.06, hl=0.16)


def glass(ctx, tint="#9fd0e8", alpha=0.30, hard="tblr", streak=True, seed=7, **kw):
    """Translucent glass with a faint sky gradient and diagonal reflection streaks; the edge is a little more opaque."""
    t = rgb(tint)
    c = np.broadcast_to(t, (ctx.h, ctx.w, 3)).copy()
    c = c * (0.8 + 0.3 * ctx.V)[..., None]
    a = np.full((ctx.h, ctx.w), alpha, np.float32)
    if streak:
        s = ctx.U * 0.8 + ctx.V * 0.5
        st = np.exp(-((np.mod(s, 1.0) - 0.30) / 0.05) ** 2) * 0.9 + np.exp(-((np.mod(s, 1.0) - 0.62) / 0.025) ** 2) * 0.5
        c = np.minimum(c + st[..., None] * 0.35, 1.0)
        a = a + st * 0.15
    edge = 1 - smooth(0.0, 0.05, ctx.edge) if hard else 0.0
    a = a + 0.22 * edge
    c = c * (1 - 0.3 * edge)[..., None] if hard else c
    return np.concatenate([c, np.clip(a, 0, 0.95)[..., None]], axis=-1)


def lamp(ctx, color="#fff2c0", rim="#b0b4ba", hard="tblr", seed=8, glow=1.0, **kw):
    """A lens: bright centre, reflector rings, a metal rim."""
    c = np.broadcast_to(rgb(color), (ctx.h, ctx.w, 3)).copy()
    cx, cy = ctx.U - 0.5, ctx.V - 0.5
    r = np.sqrt((cx * ctx.ul) ** 2 + (cy * ctx.vl) ** 2) / (0.5 * min(ctx.ul, ctx.vl) + 1e-6)
    c = c * (0.7 + 0.5 * np.exp(-(r * 1.4) ** 2) * glow)[..., None]
    rings = 0.06 * np.sin(r * 28.0) * (r < 0.95)
    c = c * (1 + rings)[..., None]
    c = mix(c, rgb(rim), smooth(0.9, 1.0, r) * 0.9)
    return np.minimum(c, 1.0)


def hazard(ctx, a="#e8b81c", b="#1b1b1b", w=0.35, angle=45.0, seed=9, dirt=0.35, **kw):
    """Diagonal hazard stripes, worn and dirty."""
    ca = math.cos(math.radians(angle))
    s = (ctx.dl * ca + ctx.dt * math.sin(math.radians(angle))) / (2 * w)
    stripe = (np.mod(s, 1.0) < 0.5)
    c = np.where(stripe[..., None], rgb(a), rgb(b)).astype(np.float32)
    n = fbm(ctx.P, 9.0, seed, 3)
    c = c * (1 - dirt * (0.6 * n + 0.4 * white_noise(ctx, seed) * 0.4))[..., None]
    return edge_fx(ctx, c, "tblr", ao=0.2, ao_w=0.04, hl=0.1)
