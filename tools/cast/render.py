"""A small software renderer for Minecraft player skins: draws the model (both skin layers) from any angle.

Used only to make the preview sheets (tools\\cast\\preview). It follows the game's own box layout, so what it
shows is what the skin looks like on the model, minus the game's lighting and the pose.

    render_view(img, slim, yaw, pitch) -> RGBA image of one view of the standing figure
    sheet(skins)                        -> one big image: front, 3/4, side, back of every skin, plus tiny "far" views
"""
import math

import numpy as np
from PIL import Image, ImageDraw

# (name, base uv, overlay uv, (x0, x1), (y0, y1), (z0, z1), overlay inflate); units are texels (1/16 block)
# the figure faces +Z; the character's left arm is at +X (the viewer's right in the front view)


def boxes(slim):
    aw = 3 if slim else 4
    return [
        ("head", (0, 0), (32, 0), (-4, 4), (24, 32), (-4, 4), 0.5),
        ("body", (16, 16), (16, 32), (-4, 4), (12, 24), (-2, 2), 0.25),
        ("rarm", (40, 16), (40, 32), (-4 - aw, -4), (12, 24), (-2, 2), 0.25),
        ("larm", (32, 48), (48, 48), (4, 4 + aw), (12, 24), (-2, 2), 0.25),
        ("rleg", (0, 16), (0, 32), (-4, 0), (0, 12), (-2, 2), 0.25),
        ("lleg", (16, 48), (0, 48), (0, 4), (0, 12), (-2, 2), 0.25),
    ]


def _face_points(face, x0, x1, y0, y1, z0, z1, tw, th, S):
    """Sample points (N, 3) of a face plus texel (col, row) for each, in model space."""
    nu, nv = tw * S, th * S
    s = (np.arange(nu) + 0.5) / nu
    t = (np.arange(nv) + 0.5) / nv
    ss, tt = np.meshgrid(s, t)                       # (nv, nu)
    ss, tt = ss.ravel(), tt.ravel()
    w, h, d = x1 - x0, y1 - y0, z1 - z0
    if face == "front":
        p = np.stack([x0 + ss * w, y1 - tt * h, np.full_like(ss, z1)], 1)
        n = (0, 0, 1)
    elif face == "back":
        p = np.stack([x1 - ss * w, y1 - tt * h, np.full_like(ss, z0)], 1)
        n = (0, 0, -1)
    elif face == "right":
        p = np.stack([np.full_like(ss, x0), y1 - tt * h, z0 + ss * d], 1)
        n = (-1, 0, 0)
    elif face == "left":
        p = np.stack([np.full_like(ss, x1), y1 - tt * h, z1 - ss * d], 1)
        n = (1, 0, 0)
    elif face == "top":
        p = np.stack([x0 + ss * w, np.full_like(ss, y1), z0 + tt * d], 1)
        n = (0, 1, 0)
    else:                                            # bottom
        p = np.stack([x0 + ss * w, np.full_like(ss, y0), z1 - tt * d], 1)
        n = (0, -1, 0)
    col = np.minimum((ss * tw).astype(int), tw - 1)
    row = np.minimum((tt * th).astype(int), th - 1)
    return p, n, col, row


def render_view(img, slim, yaw=0.0, pitch=12.0, K=8, S=14, pad=6, bg=(0, 0, 0, 0)):
    tex = np.asarray(img.convert("RGBA"))
    th_, ph_ = math.radians(yaw), math.radians(pitch)
    cy_, sy_ = math.cos(th_), math.sin(th_)
    cp_, sp_ = math.cos(ph_), math.sin(ph_)

    def xf(p):
        x = p[:, 0] * cy_ + p[:, 2] * sy_
        z = -p[:, 0] * sy_ + p[:, 2] * cy_
        y = p[:, 1] * cp_ - z * sp_
        z2 = p[:, 1] * sp_ + z * cp_
        return x, y, z2

    def xn(n):
        x = n[0] * cy_ + n[2] * sy_
        z = -n[0] * sy_ + n[2] * cy_
        y = n[1] * cp_ - z * sp_
        z2 = n[1] * sp_ + z * cp_
        return np.array([x, y, z2])

    light = np.array([-0.35, 0.65, 0.7])
    light /= np.linalg.norm(light)
    pts, cols, deps, sxs, sys_ = [], [], [], [], []
    W = int((26 + 2 * pad) * K)
    H = int((34 + 2 * pad) * K)
    cx, cy = W / 2, H - pad * K
    for name, buv, ouv, (x0, x1), (y0, y1), (z0, z1), infl in boxes(slim):
        w, h, d = x1 - x0, y1 - y0, z1 - z0
        for layer in (0, 1):
            u0, v0 = ouv if layer else buv
            g = infl if layer else 0.0
            bx0, bx1, by0, by1, bz0, bz1 = x0 - g, x1 + g, y0 - g, y1 + g, z0 - g, z1 + g
            rects = {"top": (u0 + d, v0, w, d), "bottom": (u0 + d + w, v0, w, d),
                     "right": (u0, v0 + d, d, h), "front": (u0 + d, v0 + d, w, h),
                     "left": (u0 + d + w, v0 + d, d, h), "back": (u0 + d + w + d, v0 + d, w, h)}
            for face, (ru, rv, rw, rh) in rects.items():
                p, n, c, r = _face_points(face, bx0, bx1, by0, by1, bz0, bz1, rw, rh, S)
                x, y, z = xf(p)
                nn = xn(n)
                if nn[2] < -0.05 and False:
                    continue
                px = tex[rv + r, ru + c]
                keep = px[:, 3] > 128
                if not keep.any():
                    continue
                shade = 0.52 + 0.55 * max(0.0, float(nn @ light))
                rgb = np.clip(px[:, :3].astype(float) * shade, 0, 255).astype(np.uint8)
                sxs.append((cx + x[keep] * K).astype(int))
                sys_.append((cy - y[keep] * K).astype(int))
                deps.append(z[keep])
                cols.append(rgb[keep])
    sx, sy, dp, col = np.concatenate(sxs), np.concatenate(sys_), np.concatenate(deps), np.concatenate(cols)
    ok = (sx >= 0) & (sx < W) & (sy >= 0) & (sy < H)
    sx, sy, dp, col = sx[ok], sy[ok], dp[ok], col[ok]
    order = np.lexsort((-dp, sy * W + sx))           # per pixel: nearest (largest z) first
    key = (sy * W + sx)[order]
    first = np.concatenate([[True], key[1:] != key[:-1]])
    pick = order[first]
    out = np.zeros((H, W, 4), np.uint8)
    out[:] = bg
    out[sy[pick], sx[pick], :3] = col[pick]
    out[sy[pick], sx[pick], 3] = 255
    return Image.fromarray(out, "RGBA")


def sheet(skins, path, names=None):
    """skins: {id: (PIL image, slim)}. Writes one sheet: each row a character, columns front / 3-4 / side / back / tiny far views."""
    names = names or list(skins)
    views = [(0, 12), (-38, 12), (90, 12), (180, 12)]
    K = 7
    cell_w, cell_h = int(38 * K), int(46 * K)
    far_w = 120
    W = cell_w * len(views) + far_w + 140
    H = cell_h * len(names) + 10
    bg = (58, 62, 70, 255)
    sheet_img = Image.new("RGBA", (W, H), bg)
    d = ImageDraw.Draw(sheet_img)
    for r, nm in enumerate(names):
        img, slim = skins[nm]
        y = 5 + r * cell_h
        d.text((6, y + 6), f"{nm}\n{'slim' if slim else 'wide'}", fill=(235, 235, 235, 255))
        for c, (yaw, pitch) in enumerate(views):
            v = render_view(img, slim, yaw, pitch, K=K, pad=6)
            sheet_img.alpha_composite(v, (140 + c * cell_w + (cell_w - v.width) // 2, y + (cell_h - v.height) // 2))
        # far views: the figure at about 1/6 size, as seen from some distance (nearest-neighbour, then enlarged x2)
        v = render_view(img, slim, -25, 8, K=3, S=8, pad=2)
        small = v.resize((max(1, v.width // 2), max(1, v.height // 2)), Image.BILINEAR)
        small = small.resize((small.width * 2, small.height * 2), Image.NEAREST)
        sheet_img.alpha_composite(small, (140 + len(views) * cell_w + 8, y + 10))
    sheet_img.convert("RGB").save(path)
    return path

COLORS = {"minecraft:white_wool": (238, 238, 240), "minecraft:light_gray_concrete": (140, 142, 148),
          "minecraft:white_concrete": (225, 227, 230), "minecraft:light_blue_wool": (110, 165, 218),
          "minecraft:black_concrete": (28, 28, 30), "minecraft:light_gray_stained_glass": (190, 195, 205),
          "minecraft:cyan_stained_glass": (70, 190, 205)}


def gurney_preview(parts, seat_y, seat_z, crew, path, K=140):
    """Side, front and top view of the gurney (boxes drawn as flat rectangles) with the lying patient and the crew as outlines."""
    W, H = int(5.0 * K), int(2.6 * K)
    img = Image.new("RGB", (W * 1, H * 3 // 1), (58, 62, 70))
    d = ImageDraw.Draw(img)
    # side view (forward = right): panel 0 ; front view (left = left) : panel 1 ; top view: panel 2
    def panel(i, ox, oy):
        return ox + i * 0, oy + i * H
    for (cx, cy, cz, sx, sy, sz, block, _root) in parts:
        col = COLORS.get(block, (255, 0, 255))
        # side: horizontal = z, vertical = y
        x0, x1 = 2.5 * K + (cz) * K, 2.5 * K + (cz + sz) * K
        y0, y1 = 2.2 * K - (cy + sy) * K, 2.2 * K - cy * K
        d.rectangle([x0, y0, x1, y1], fill=col, outline=(20, 20, 20))
        # front: horizontal = x (+ = left of the patient = viewer's right when looking at the foot end from the front: mirrored)
        fx0, fx1 = 2.5 * K - (cx + sx) * K, 2.5 * K - cx * K
        d.rectangle([fx0, H + y0, fx1, H + y1], fill=col, outline=(20, 20, 20))
        # top: horizontal = z, vertical = x
        ty0, ty1 = H * 2 + 1.3 * K - (cx + sx) * K, H * 2 + 1.3 * K - cx * K
        d.rectangle([x0, ty0, x1, ty1], fill=col, outline=(20, 20, 20))
    # the patient: 1.8 long, 0.25 thick, 0.5 wide, feet at seat_z, head toward -z; plus 1.0 wide at the shoulders
    px0, px1 = 2.5 * K + (seat_z - 1.8) * K, 2.5 * K + seat_z * K
    py1, py0 = 2.2 * K - (seat_y - 0.125) * K, 2.2 * K - (seat_y + 0.125) * K
    d.rectangle([px0, py0, px1, py1], outline=(255, 120, 120), width=3)
    d.rectangle([px0, H * 2 + 1.3 * K - 0.5 * K, px1, H * 2 + 1.3 * K + 0.5 * K], outline=(255, 120, 120), width=3)
    for name, (lat, fw) in crew.items():
        cxp = 2.5 * K + fw * K
        d.rectangle([cxp - 0.15 * K, H * 2 + 1.3 * K - (lat + 0.15) * K, cxp + 0.15 * K, H * 2 + 1.3 * K - (lat - 0.15) * K], outline=(120, 255, 140), width=3)
        d.text((cxp - 10, H * 2 + 1.3 * K - lat * K - 5), name[-1], fill=(120, 255, 140))
    d.text((8, 8), "side (foot end right)", fill=(235, 235, 235))
    d.text((8, H + 8), "front view", fill=(235, 235, 235))
    d.text((8, 2 * H + 8), "top (left of patient = up)", fill=(235, 235, 235))
    img.save(path)
    return path
