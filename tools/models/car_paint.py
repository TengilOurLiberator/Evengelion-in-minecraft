"""Painters specific to the roadster (and shared by the wagon and aircraft where the material is the same)."""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from . import paint as pt
from .paint import edge_fx, fbm, grain, mix, rgb, smooth, vnoise, white_noise

FONT_BOLD = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "story", "fonts", "KaTeX_Main-Bold.ttf"))
FONT_REG = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "story", "fonts", "KaTeX_Main-Regular.ttf"))

BLUE = rgb("#2152c4")
WHITE = rgb("#ecedf0")


def _font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


def blue(ctx, hard="", stripe=True, tone=1.0, seed=11, shut="", ao_arch=None, wear=1.0, **kw):
    """The body paint: deep blue, lighter high up and on upward faces, a shoulder highlight, grime and dust near the ground, racing stripes
    on the bonnet and rear deck.  Everything is a function of position so that neighbouring panels match; `hard` edges (t,b,l,r) get panel-edge
    ambient occlusion and a bevel highlight, `shut` edges a dark shut-line."""
    P, N = ctx.P, ctx.N
    y, x, z = P[..., 1], P[..., 0], P[..., 2]
    c = np.broadcast_to(BLUE * tone, (ctx.h, ctx.w, 3)).copy()
    lt = 0.78 + 0.34 * smooth(0.10, 0.95, y) + 0.10 * max(N[1], 0.0)
    c = c * lt[..., None]
    side = 1 - abs(N[1])
    c = c + (side * 0.13 * np.exp(-((y - 0.60) / 0.05) ** 2))[..., None] * np.array([0.55, 0.72, 1.0], np.float32)
    c = c + (0.08 * np.exp(-((y - 0.38) / 0.04) ** 2) * side)[..., None] * np.array([0.3, 0.45, 0.8], np.float32)
    n = fbm(P, 7.0, seed, 3)
    dirt = smooth(0.46, 0.06, y) * (0.5 + 0.9 * n) * wear
    c = c * (1 - 0.34 * dirt)[..., None]
    c = mix(c, c * np.array([0.85, 0.78, 0.66], np.float32), 0.55 * smooth(0.28, 0.08, y) * n * wear)
    if ao_arch:
        for (zc, yc, ra) in ao_arch:
            d = np.sqrt((z - zc) ** 2 + (y - yc) ** 2)
            c = c * (1 - 0.35 * (1 - smooth(ra, ra + 0.30, d)))[..., None]
    if N[1] > 0.5:
        # bonnet details, as a pattern of position: louvres either side of the centre, the shut lines round the bonnet panel
        ax = np.abs(x)
        louv = (z > 1.5) & (z < 2.25) & (ax > 0.46) & (ax < 0.84) & (np.mod((z - 1.5) / 0.075, 1.0) < 0.38)
        c = np.where(louv[..., None], c * 0.18, c)
        seam = ((np.abs(ax - 1.03) < 0.008) & (z > 1.07) & (z < 3.25)) | ((np.abs(z - 1.07) < 0.008) & (ax < 1.03))
        c = np.where(seam[..., None], c * 0.22, c)
    if stripe:
        ax = np.abs(x)
        up = (N[1] > 0.2) | (N[2] > 0.55) | (N[2] < -0.55)
        zone = ((z > 1.05) | (z < -1.3)) & (y > 0.3)
        if up:
            m = ((ax > 0.07) & (ax < 0.33) & zone)
            wh = WHITE * lt[..., None] * (0.97 + 0.03 * n[..., None])
            c = np.where(m[..., None], wh * (1 - 0.15 * dirt[..., None]), c)
            # a hairline of lighter blue at the edges of the stripes
            e = (np.abs(ax - 0.07) < 0.012) | (np.abs(ax - 0.33) < 0.012)
            c = np.where((e & zone)[..., None], c * 0.82, c)
    c = c + ((white_noise(ctx, seed + 3) > 0.9985) * 0.08)[..., None]
    c = grain(ctx, c, 0.015, 140, seed)
    if shut:
        d = np.full_like(ctx.dl, 9.0)
        for ch, arr in (("t", ctx.dt), ("b", ctx.db), ("l", ctx.dl), ("r", ctx.dr)):
            if ch in shut:
                d = np.minimum(d, arr)
        w = max(0.014, 1.4 * ctx.px)
        c = np.where((d < w)[..., None], c * 0.12, c)
        c = np.where(((d >= w) & (d < w * 2.2))[..., None], np.minimum(c * 1.18 + 0.03, 1), c)
    if hard:
        c = edge_fx(ctx, c, hard, ao=0.22, ao_w=0.05, hl=0.16)
    return c


def underbody(ctx, seed=12, **kw):
    P = ctx.P
    c = np.broadcast_to(rgb("#34353a"), (ctx.h, ctx.w, 3)).copy()
    n = fbm(P, 5.0, seed, 3)
    c = c * (0.7 + 0.6 * n)[..., None]
    rust = smooth(0.62, 0.8, fbm(P, 9.0, seed + 1, 3))
    c = mix(c, rgb("#5b3a24"), rust * 0.5)
    return grain(ctx, c, 0.05, 80, seed)


def carpet(ctx, base="#2a2d38", seed=13, **kw):
    c = np.broadcast_to(rgb(base), (ctx.h, ctx.w, 3)).copy()
    n = white_noise(ctx, seed) - 0.5
    n2 = fbm(ctx.P, 70.0, seed, 2) - 0.5
    c = c * (1 + 0.18 * n + 0.18 * n2)[..., None]
    c = c * (0.85 + 0.2 * fbm(ctx.P, 3.0, seed + 4, 2))[..., None]
    return edge_fx(ctx, c, "tblr", ao=0.3, ao_w=0.06, hl=0.0)


def pleats(ctx, base="#c4915a", seed=14, across="u", pitch=0.17, hard="tblr", piping=None, **kw):
    """Leather with stitched pleats: channels every `pitch` blocks across the face's u (or v) direction."""
    c = pt.leather(ctx, base=base, hard=hard, piping=piping, seed=seed, pipe=0.35)
    t = (ctx.dl if across == "u" else ctx.dt) / pitch
    f = np.mod(t, 1.0)
    groove = np.exp(-((f - 0.0) / 0.05) ** 2) + np.exp(-((f - 1.0) / 0.05) ** 2)
    crown = 0.12 * np.sin(f * math.pi)
    c = c * (1 - 0.22 * groove + crown)[..., None]
    return np.clip(c, 0, 1)


def mesh(ctx, pitch=0.045, bg="#0b0b0d", fg="#9ea3ab", **kw):
    a = ctx.dl / pitch
    b = ctx.dt / pitch
    line = (np.abs(np.mod(a + b, 1.0) - 0.5) < 0.14) | (np.abs(np.mod(a - b, 1.0) - 0.5) < 0.14)
    c = np.where(line[..., None], rgb(fg), rgb(bg)).astype(np.float32)
    return edge_fx(ctx, c, "tblr", ao=0.35, ao_w=0.05, hl=0.0)


def slats(ctx, n=6, bg="#0d0d10", fg="#aab0b8", horizontal=True, **kw):
    t = ctx.V if horizontal else ctx.U
    f = np.mod(t * n, 1.0)
    bar = (f > 0.25) & (f < 0.8)
    c = np.where(bar[..., None], rgb(fg) * (0.7 + 0.5 * (1 - f))[..., None], rgb(bg)).astype(np.float32)
    return edge_fx(ctx, c, "tblr", ao=0.3, ao_w=0.04, hl=0.15)


# ---------------------------------------------------------------------------------------------------- instruments
_dial_cache = {}


def dial_image(kind, size=256):
    key = (kind, size)
    if key in _dial_cache:
        return _dial_cache[key]
    S = size * 2
    im = Image.new("RGBA", (S, S), (14, 14, 16, 255))
    d = ImageDraw.Draw(im)
    cx = cy = S / 2
    R = S / 2

    def pol(r, ang):          # ang in degrees from 12 o'clock, clockwise
        a = math.radians(ang)
        return cx + r * R * math.sin(a), cy - r * R * math.cos(a)

    f_big = _font(FONT_BOLD, int(S * 0.115))
    f_small = _font(FONT_BOLD, int(S * 0.075))
    white = (238, 236, 226, 255)
    if kind in ("speedo", "rev"):
        if kind == "speedo":
            vmax, major, minor, a0, a1, labels, needle_v, red_from = 200, 20, 10, -135, 135, range(0, 201, 40), 70, None
            title = "km/h"
        else:
            vmax, major, minor, a0, a1, labels, needle_v, red_from = 8, 1, 0.5, -135, 135, range(0, 9), 2.6, 6.5
            title = "x1000 rpm"
        if red_from is not None:
            for k in range(int((vmax - red_from) * 20)):
                v = red_from + k / 20
                ang = a0 + (a1 - a0) * v / vmax
                d.line([pol(0.84, ang), pol(0.95, ang)], fill=(200, 30, 30, 255), width=int(S * 0.012))
        v = 0.0
        while v <= vmax + 1e-6:
            ang = a0 + (a1 - a0) * v / vmax
            ismaj = abs(v / major - round(v / major)) < 1e-6
            d.line([pol(0.78 if ismaj else 0.84, ang), pol(0.93, ang)], fill=white, width=int(S * (0.014 if ismaj else 0.007)))
            v += minor
        for v in labels:
            ang = a0 + (a1 - a0) * v / vmax
            tx, ty = pol(0.62, ang)
            s = str(int(v))
            w = d.textlength(s, font=f_big)
            d.text((tx - w / 2, ty - S * 0.06), s, fill=white, font=f_big)
        w = d.textlength(title, font=f_small)
        d.text((cx - w / 2, cy + R * 0.42), title, fill=(190, 190, 180, 255), font=f_small)
        w = d.textlength("TENSHI", font=f_small)
        d.text((cx - w / 2, cy - R * 0.30), "TENSHI", fill=(160, 160, 155, 255), font=f_small)
        ang = a0 + (a1 - a0) * needle_v / vmax
        d.line([pol(-0.18, ang), pol(0.88, ang)], fill=(255, 120, 30, 255), width=int(S * 0.018))
        d.ellipse((cx - S * 0.045, cy - S * 0.045, cx + S * 0.045, cy + S * 0.045), fill=(40, 40, 44, 255), outline=(200, 200, 200, 255), width=3)
    else:
        # small gauge: a 180-degree sweep, labels at the ends
        kinds = {"fuel": ("E", "F", "FUEL", 0.7), "temp": ("C", "H", "TEMP", 0.45), "oil": ("L", "H", "OIL", 0.6), "amp": ("-", "+", "AMP", 0.55)}
        l0, l1, title, nv = kinds[kind]
        a0, a1 = -70, 70
        for k in range(0, 11):
            ang = a0 + (a1 - a0) * k / 10
            d.line([pol(0.74 if k % 5 else 0.66, ang), pol(0.9, ang)], fill=white, width=int(S * (0.014 if k % 5 == 0 else 0.008)))
        d.text(pol(0.52, a0), l0, fill=white, font=f_big, anchor="mm")
        d.text(pol(0.52, a1), l1, fill=white, font=f_big, anchor="mm")
        w = d.textlength(title, font=f_small)
        d.text((cx - w / 2, cy + R * 0.28), title, fill=(190, 190, 180, 255), font=f_small)
        ang = a0 + (a1 - a0) * nv
        d.line([pol(-0.12, ang), pol(0.84, ang)], fill=(255, 120, 30, 255), width=int(S * 0.02))
        d.ellipse((cx - S * 0.04, cy - S * 0.04, cx + S * 0.04, cy + S * 0.04), fill=(40, 40, 44, 255))
    im = im.resize((size, size), Image.LANCZOS)
    arr = np.asarray(im, np.float32) / 255.0
    _dial_cache[key] = arr
    return arr


def dial(ctx, kind="speedo", centre=(0, 0, 0), right=(-1.0, 0.0, 0.0), up=(0.0, 1.0, 0.0), radius=0.2, glow=0.0, **kw):
    """A dial face painted on any element lying in the plane spanned by `right` and `up` through `centre` (face radius `radius` blocks): works for
    the rotated rectangles of a disc too, since the lookup is by position."""
    img = dial_image(kind)
    S = img.shape[0]
    d = ctx.P - np.array(centre, np.float32)
    a = d @ np.array(right, np.float32) / radius
    b = d @ np.array(up, np.float32) / radius
    ix = np.clip(((a * 0.5 + 0.5) * S).astype(int), 0, S - 1)
    iy = np.clip(((0.5 - b * 0.5) * S).astype(int), 0, S - 1)
    c = img[iy, ix, :3].copy()
    r = np.sqrt(a * a + b * b)
    c = np.where((r > 1.0)[..., None], rgb("#0e0e10"), c)
    # a glass sheen across the face
    sheen = np.exp(-((a * 0.7 + b * 0.7 - 0.45) / 0.18) ** 2) * 0.10
    c = c + sheen[..., None]
    return np.clip(c, 0, 1)


def switch_panel(ctx, **kw):
    """A small panel with a row of labelled rocker switches and a key slot (a few bright marks)."""
    c = np.broadcast_to(rgb("#9aa0a8"), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.8 + 0.4 * smooth(0, 1, ctx.V))[..., None]
    n = 5
    t = ctx.U * n
    cell = np.mod(t, 1.0)
    sw = (np.abs(cell - 0.5) < 0.18) & (np.abs(ctx.V - 0.5) < 0.28)
    c = np.where(sw[..., None], rgb("#18181a"), c)
    c = np.where((sw & (ctx.V < 0.5))[..., None], rgb("#3a3a40"), c)
    return edge_fx(ctx, grain(ctx, c, 0.03, 100, 3), "tblr", ao=0.2, ao_w=0.03, hl=0.2)


# ---------------------------------------------------------------------------------------------------- lamps and plates
def head_lens(ctx, **kw):
    return pt.lamp(ctx, color="#fff6d0", rim="#b6bac2", glow=1.2)


def tail_lens(ctx, **kw):
    """Tail lamp: red upper lens with a lamp texture, amber indicator below, white reversing lamp in the middle."""
    c = np.broadcast_to(rgb("#e0201a"), (ctx.h, ctx.w, 3)).copy()
    v = ctx.V
    c = np.where((v > 0.62)[..., None], rgb("#f09a20"), c)
    c = np.where(((v > 0.40) & (v <= 0.62))[..., None], rgb("#f1efe6"), c)
    c = c * (0.85 + 0.2 * np.sin(ctx.U * 40.0) * 0.2 + 0.15 * np.exp(-((ctx.U - 0.5) / 0.4) ** 2))[..., None]
    return edge_fx(ctx, c, "tblr", ao=0.3, ao_w=0.03, hl=0.1)


_plate_cache = {}


def plate(ctx, text="TK3 015", rear=True, **kw):
    key = (text, rear, ctx.w, ctx.h)
    if key not in _plate_cache:
        W, H = ctx.w * 2, ctx.h * 2
        bg = (238, 190, 40) if rear else (236, 236, 232)
        im = Image.new("RGBA", (W, H), bg + (255,))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, W - 1, H - 1), outline=(20, 20, 20, 255), width=max(2, H // 16))
        d.rectangle((H // 10, H // 10, W - 1 - H // 10, H - 1 - H // 10), outline=(30, 30, 30, 255), width=max(1, H // 40))
        f = _font(FONT_BOLD, int(H * 0.62))
        w = d.textlength(text, font=f)
        d.text(((W - w) / 2, H * 0.12), text, fill=(18, 18, 20, 255), font=f)
        for sx in (H * 0.18, W - H * 0.18):
            d.ellipse((sx - H * 0.04, H * 0.5 - H * 0.04, sx + H * 0.04, H * 0.5 + H * 0.04), fill=(120, 120, 124, 255))
        _plate_cache[key] = np.asarray(im.resize((ctx.w, ctx.h), Image.LANCZOS), np.float32)[..., :3] / 255.0
    c = _plate_cache[key].copy()
    c = c * (0.92 + 0.12 * fbm(ctx.P, 20.0, 5, 2))[..., None]
    return c


def emblem(ctx, **kw):
    """An invented badge: a swept-wing mark on deep blue in a silver ring."""
    S = 128
    im = Image.new("RGBA", (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((2, 2, S - 3, S - 3), fill=(200, 204, 212, 255))
    d.ellipse((12, 12, S - 13, S - 13), fill=(16, 38, 110, 255))
    wing = [(64, 30), (100, 84), (84, 80), (64, 52), (44, 80), (28, 84)]
    d.polygon(wing, fill=(230, 232, 240, 255))
    d.polygon([(64, 58), (72, 92), (64, 86), (56, 92)], fill=(255, 140, 40, 255))
    arr = np.asarray(im.resize((ctx.w, ctx.h), Image.LANCZOS), np.float32) / 255.0
    base = np.broadcast_to(rgb("#9aa0aa"), (ctx.h, ctx.w, 3)).copy()
    a = arr[..., 3:4]
    return base * (1 - a) + arr[..., :3] * a


# ---------------------------------------------------------------------------------------------------- wheels
def tyre_tread(ctx, centre=(0, 0, 0), **kw):
    d = ctx.P - np.array(centre, np.float32)
    th = np.arctan2(d[..., 2], d[..., 1])
    ax = d[..., 0]
    c = np.broadcast_to(rgb("#17171a"), (ctx.h, ctx.w, 3)).copy()
    blocks = np.mod(th / (2 * math.pi) * 32 + 0.5 * (np.abs(ax) > 0.0), 1.0)
    groove = (np.abs(blocks - 0.5) < 0.12) | (np.abs(ax) < 0.012) | (np.abs(np.abs(ax) - 0.085) < 0.01)
    c = np.where(groove[..., None], c * 0.45, c * (0.9 + 0.5 * vnoise(ctx.P, 90.0, 4)[..., None]))
    return np.clip(c + 0.02, 0, 1)


def tyre_wall(ctx, centre=(0, 0, 0), r_out=0.4, **kw):
    d = ctx.P - np.array(centre, np.float32)
    r = np.sqrt(d[..., 1] ** 2 + d[..., 2] ** 2)
    th = np.arctan2(d[..., 2], d[..., 1])
    c = np.broadcast_to(rgb("#202023"), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.9 + 0.25 * vnoise(ctx.P, 60.0, 5)[..., None])
    white = (np.abs(r - (r_out - 0.055)) < 0.011)
    c = np.where(white[..., None], rgb("#d8d8d0") * (0.85 + 0.15 * vnoise(ctx.P, 50, 3))[..., None], c)
    # raised lettering: short dashes on an arc
    txt = (np.abs(r - (r_out - 0.095)) < 0.013) & (np.mod(th / (2 * math.pi) * 90, 1.0) < 0.55) & (np.abs(np.sin(th * 3.0)) < 0.7)
    c = np.where(txt[..., None], c * 1.7 + 0.04, c)
    c = c * (0.7 + 0.5 * smooth(r_out - 0.13, r_out, r))[..., None]
    return np.clip(c, 0, 1)


def rim_face(ctx, centre=(0, 0, 0), r_rim=0.29, side=1.0, spokes=10, **kw):
    """Alloy wheel face seen along the axle: bright lip, spokes with dark gaps (brake disc behind), a centre boss."""
    d = ctx.P - np.array(centre, np.float32)
    r = np.sqrt(d[..., 1] ** 2 + d[..., 2] ** 2)
    th = np.arctan2(d[..., 2], d[..., 1]) * side
    metal = rgb("#c4c8d0")
    gap = rgb("#33302e")
    # brake disc and caliper behind the spokes
    c = np.broadcast_to(gap, (ctx.h, ctx.w, 3)).copy()
    c = c * (0.8 + 0.5 * vnoise(ctx.P, 50.0, 6)[..., None])
    c = np.where(((r > 0.12) & (r < 0.24))[..., None], rgb("#6b625a") * (0.8 + 0.3 * np.cos(r * 90.0))[..., None], c)
    cal = (np.abs(np.mod(th + 0.6, 2 * math.pi) - math.pi) < 0.5) & (r > 0.1) & (r < 0.26)
    c = np.where(cal[..., None], rgb("#a02820"), c)
    spoke_ang = np.mod(th / (2 * math.pi) * spokes + 0.3 * (r / r_rim), 1.0)
    width = 0.20 + 0.10 * (1 - r / r_rim)
    sp = (np.abs(spoke_ang - 0.5) < width) & (r > 0.06) & (r < r_rim - 0.02)
    shade = 0.75 + 0.35 * np.cos(th * spokes + 1.0 * r / r_rim * 6) * 0.5 + 0.2 * (0.5 - np.abs(spoke_ang - 0.5))
    c = np.where(sp[..., None], metal * shade[..., None], c)
    lip = (r >= r_rim - 0.025) & (r < r_rim + 0.03)
    c = np.where(lip[..., None], metal * (0.95 + 0.1 * np.cos(th * 2)[..., None]), c)
    c = np.where((r >= r_rim + 0.03)[..., None], rgb("#202023"), c)
    boss = r < 0.075
    c = np.where(boss[..., None], rgb("#d9dce2") * (0.8 + 0.3 * np.cos(th * 3 + 0.2))[..., None], c)
    return np.clip(c, 0, 1)


def hub_cap(ctx, centre=(0, 0, 0), **kw):
    d = ctx.P - np.array(centre, np.float32)
    r = np.sqrt(d[..., 1] ** 2 + d[..., 2] ** 2)
    th = np.arctan2(d[..., 2], d[..., 1])
    c = np.broadcast_to(rgb("#d3d6dc"), (ctx.h, ctx.w, 3)).copy()
    ears = (np.cos(th * 3) > 0.55) & (r > 0.05)
    c = c * (0.7 + 0.4 * (np.cos(th * 3) * 0.5 + 0.5))[..., None]
    c = np.where(ears[..., None], rgb("#eef0f4"), c)
    c = np.where((r < 0.03)[..., None], rgb("#2a2a2e"), c)
    emb = (r > 0.06) & (r < 0.075)
    c = np.where(emb[..., None], rgb("#a02820"), c)
    return np.clip(c, 0, 1)


def arch_liner(ctx, **kw):
    c = np.broadcast_to(rgb("#0e0e10"), (ctx.h, ctx.w, 3)).copy()
    n = fbm(ctx.P, 14.0, 7, 3)
    c = c * (0.7 + 1.0 * n)[..., None]
    return np.clip(c + 0.02, 0, 1)


def glass_clear(ctx, tint="#a4d4ea", alpha=0.26, **kw):
    return pt.glass(ctx, tint=tint, alpha=alpha, hard="tblr")


def mirror_glass(ctx, **kw):
    c = np.broadcast_to(rgb("#aab9cc"), (ctx.h, ctx.w, 3)).copy()
    c = c * (0.7 + 0.5 * ctx.V)[..., None]
    s = np.exp(-((ctx.U * 0.7 + ctx.V * 0.4 - 0.5) / 0.1) ** 2) * 0.35
    return np.clip(c + s[..., None], 0, 1)
