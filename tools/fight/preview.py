"""A small software renderer for the Angel's boxes (z-buffer, flat shading, outlines), used to look at the model.

    python preview.py [pose ...]     writes preview\\<pose>_{front,side,q3}.png and preview\\sheet_<pose>.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402

OUT = os.path.join(HERE, "preview")
LIGHT = np.array([-0.45, 0.8, 0.55])
LIGHT = LIGHT / np.linalg.norm(LIGHT)
# unit-cube faces: (normal, 4 corners in (sx,sy,sz) in -1/1)
FACES = []
for ax in range(3):
    for sg in (-1, 1):
        n = np.zeros(3)
        n[ax] = sg
        u = [(ax + 1) % 3, (ax + 2) % 3]
        quad = []
        for a, b in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
            c = np.zeros(3)
            c[ax] = sg
            c[u[0]] = a
            c[u[1]] = b
            quad.append(c)
        FACES.append((n, np.array(quad)))


def _hash(a, b, seed):
    return ((a * 73856093) ^ (b * 19349663) ^ (seed * 83492791)) & 255


def render(boxes, yaw=0.0, pitch=8.0, size=(520, 760), dist=210.0, target=(0, 50, 0), fov=34.0, extra=None,
           unit=0.3, reflines=True):
    """yaw: camera azimuth in degrees, 0 = looking at the monster's front (camera on +z looking toward -z)."""
    W, H = size
    yaw_r, pit_r = math.radians(yaw), math.radians(pitch)
    cam_dir = np.array([math.sin(yaw_r) * math.cos(pit_r), math.sin(pit_r), math.cos(yaw_r) * math.cos(pit_r)])
    tgt = np.array(target, float)
    eye = tgt + cam_dir * dist
    fwd = tgt - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0, 1, 0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    f = 0.5 * H / math.tan(math.radians(fov) / 2)

    def proj(p):
        d = p - eye
        z = d @ fwd
        return np.array([W / 2 + f * (d @ right) / z, H / 2 - f * (d @ up) / z, z])

    img = np.zeros((H, W, 3), float)
    # night background: vertical gradient
    t = np.linspace(0, 1, H)[:, None]
    img[:] = (np.array([6, 9, 22]) * (1 - t) + np.array([22, 30, 52]) * t)[:, None, :].reshape(H, 1, 3)
    zbuf = np.full((H, W), 1e9)
    ids = np.full((H, W), -1, int)
    # ground plane (z-buffered as a big quad at y = 0)
    def tri(p0, p1, p2, color, ident, attrs=None, shade=1.0, emissive=0.0, tex=None):
        xs = [p0[0], p1[0], p2[0]]
        ys = [p0[1], p1[1], p2[1]]
        x0, x1 = int(max(0, math.floor(min(xs)))), int(min(W - 1, math.ceil(max(xs))))
        y0, y1 = int(max(0, math.floor(min(ys)))), int(min(H - 1, math.ceil(max(ys))))
        if x1 < x0 or y1 < y0:
            return
        gx, gy = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        den = (p1[1] - p2[1]) * (p0[0] - p2[0]) + (p2[0] - p1[0]) * (p0[1] - p2[1])
        if abs(den) < 1e-9:
            return
        l0 = ((p1[1] - p2[1]) * (gx - p2[0]) + (p2[0] - p1[0]) * (gy - p2[1])) / den
        l1 = ((p2[1] - p0[1]) * (gx - p2[0]) + (p0[0] - p2[0]) * (gy - p2[1])) / den
        l2 = 1 - l0 - l1
        m = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not m.any():
            return
        inv = l0 / p0[2] + l1 / p1[2] + l2 / p2[2]
        z = 1.0 / np.maximum(inv, 1e-9)
        sub = zbuf[y0:y1 + 1, x0:x1 + 1]
        upd = m & (z < sub)
        if not upd.any():
            return
        sub[upd] = z[upd]
        ids[y0:y1 + 1, x0:x1 + 1][upd] = ident
        col = np.array(color, float) * shade
        if tex is not None:
            u = (l0 * attrs[0][0] / p0[2] + l1 * attrs[1][0] / p1[2] + l2 * attrs[2][0] / p2[2]) * z
            v = (l0 * attrs[0][1] / p0[2] + l1 * attrs[1][1] / p1[2] + l2 * attrs[2][1] / p2[2]) * z
            ui = np.floor(np.nan_to_num(u) * tex[0]).astype(int)
            vi = np.floor(np.nan_to_num(v) * tex[0]).astype(int)
            h = _hash(ui, vi, tex[1]) / 255.0
            k = (0.86 + 0.28 * h)[..., None]
            c = col[None, None, :] * k
        else:
            c = np.broadcast_to(col, (y1 - y0 + 1, x1 - x0 + 1, 3))
        reg = img[y0:y1 + 1, x0:x1 + 1]
        cc = c if emissive == 0 else c * (1 - emissive) + np.array(color, float) * emissive
        reg[upd] = np.asarray(cc)[upd]

    ident = 0
    # ground
    gp = [proj(np.array(p, float)) for p in ((-400, 0, -400), (400, 0, -400), (400, 0, 400), (-400, 0, 400))]
    if all(q[2] > 1 for q in gp):
        tri(gp[0], gp[1], gp[2], (26, 30, 38), -2)
        tri(gp[0], gp[2], gp[3], (26, 30, 38), -2)
    for e in list(boxes) + list(extra or []):
        col = model.COLORS.get(e["block"], (128, 128, 128))
        h = e["half"]
        glow = (e.get("light") or 0) >= 15
        for (n, quad) in FACES:
            nw = e["R"] @ n
            if nw @ (eye - e["centre"]) <= 0 and e["block"] != "minecraft:red_stained_glass":
                continue
            lam = max(0.0, float(nw @ LIGHT))
            shade = 0.50 + 0.50 * lam
            if e["block"] in (model.DARK,):
                shade = 0.55 + 0.9 * lam
            pts = [e["centre"] + e["R"] @ (q * h) for q in quad]
            pp = [proj(p) for p in pts]
            if any(q[2] < 1 for q in pp):
                continue
            uv = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
            tex = (8, ident % 7) if not glow else None
            emi = 0.0
            if glow:
                shade, emi = 1.0, 0.0
            if e["block"] == "minecraft:red_stained_glass":
                continue
            tri(pp[0], pp[1], pp[2], col, ident, [uv[0], uv[1], uv[2]], shade, emi, tex)
            tri(pp[0], pp[2], pp[3], col, ident, [uv[0], uv[2], uv[3]], shade, emi, tex)
        ident += 1
    # outlines where the id changes between two solid parts
    edge = np.zeros((H, W), bool)
    edge[:, 1:] |= ids[:, 1:] != ids[:, :-1]
    edge[1:, :] |= ids[1:, :] != ids[:-1, :]
    solid = ids >= 0
    edge &= solid
    img[edge] *= 0.55
    # outline against the background
    bgedge = np.zeros((H, W), bool)
    bgedge[:, 1:] |= solid[:, 1:] ^ solid[:, :-1]
    bgedge[1:, :] |= solid[1:, :] ^ solid[:-1, :]
    img[bgedge & solid] *= 0.4
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    # a bloom for the glowing parts
    glow = np.zeros((H, W), float)
    for e in boxes:
        if (e.get("light") or 0) >= 15 and e["block"] != "minecraft:black_concrete":
            p = proj(e["centre"])
            glow_pts = p
            gx, gy = int(glow_pts[0]), int(glow_pts[1])
            r = max(6, int(f * (e["half"].max() * 2.4) / glow_pts[2]))
            yy, xx = np.ogrid[:H, :W]
            glow += np.exp(-((xx - gx) ** 2 + (yy - gy) ** 2) / (2 * (r * 0.55) ** 2)) * (0.5 if e["tag"] == "core" else 0.3)
    if glow.max() > 0:
        g = np.clip(glow, 0, 1)[..., None]
        col = np.array([255, 70, 50]) if any(e["tag"] == "core" for e in boxes) else np.array([255, 200, 120])
        arr = np.asarray(im).astype(float)
        arr = arr + g * col * 0.55
        im = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
    if reflines:
        d = ImageDraw.Draw(im)
        # reference: the player giant's eye height (25.9 blocks) and total height (28.8)
        for yb, lab, colr in ((25.9, "player eye 25.9", (90, 160, 255)), (28.8, "player top 28.8", (60, 100, 160))):
            yu = yb / unit
            a = proj(np.array([-40.0, yu, 0.0]))
            b = proj(np.array([40.0, yu, 0.0]))
            d.line([(a[0], a[1]), (b[0], b[1])], fill=colr, width=1)
            d.text((6, a[1] - 11), lab, fill=colr)
    return im


def sheet(pose_name, pose, extra_label=""):
    boxes = model.pose_boxes(pose)
    views = [("front", 0, 6, {}), ("side", 90, 6, {}), ("q3", 38, 14, {}),
             ("close", 18, 6, dict(dist=84, target=(0, 70, 6), size=(520, 760)))]
    ims = [render(boxes, yaw=y, pitch=p, **kw) for (_, y, p, kw) in views]
    W = sum(i.width for i in ims)
    H = ims[0].height
    sh = Image.new("RGB", (W, H), (0, 0, 0))
    x = 0
    for (n, _, _, _), i in zip(views, ims):
        sh.paste(i, (x, 0))
        i.save(os.path.join(OUT, f"{pose_name}_{n}.png"))
        x += i.width
    d = ImageDraw.Draw(sh)
    d.text((8, 8), f"{pose_name} {extra_label}", fill=(255, 255, 255))
    sh.save(os.path.join(OUT, f"sheet_{pose_name}.png"))
    return sh


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    model.build()
    names = sys.argv[1:] or ["idle_a"]
    for n in names:
        sheet(n, model.poses()[n])
        print("wrote", n)
