"""Software previewer: renders item models (read back from the JSON files the pack really contains) with their textures.

Follows vanilla's rules for what the game does with such a model on an item_display: element rotation about its origin (x, y, z Euler angles,
R = Rz Ry Rx), vertex order and UV corners of FaceInfo, the centring translate(-0.5), the half turn about +y, then the display's own
transformation (scale, rotation, translation).  Back faces are culled (an item model is one-sided, like a block display), cutout texels with
alpha below 0.5 are dropped, quads whose texture region holds partial alpha are blended back to front.  Lighting is the entity shader's
two-light model (approximated), `light_emission` shows as full brightness.  Z-buffered, perspective-correct, optional supersampling.
"""
import json
import math
import os

import numpy as np

from .mdl import NS, PACK_ROOT
from .vmath import euler_zyx, from_euler_zyx, look_matrix, rax

F_FLIP = np.diag([-1.0, 1.0, -1.0])
# vanilla FaceInfo vertex order per face (model space min/max picks): (x, y, z) with 0 = min, 1 = max
FACE_VERTS = {
    "down": [(0, 0, 1), (0, 0, 0), (1, 0, 0), (1, 0, 1)],
    "up": [(0, 1, 0), (0, 1, 1), (1, 1, 1), (1, 1, 0)],
    "north": [(1, 1, 0), (1, 0, 0), (0, 0, 0), (0, 1, 0)],
    "south": [(0, 1, 1), (0, 0, 1), (1, 0, 1), (1, 1, 1)],
    "west": [(0, 1, 0), (0, 0, 0), (0, 0, 1), (0, 1, 1)],
    "east": [(1, 1, 1), (1, 0, 1), (1, 0, 0), (1, 1, 0)],
}
FACE_DIR = {"down": (0, -1, 0), "up": (0, 1, 0), "north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0), "east": (1, 0, 0)}
UV_CORNER = [(0, 0), (0, 1), (1, 1), (1, 0)]       # (u pick, v pick): vertex 0 = (minU, minV) ...

_tex_cache = {}
_model_cache = {}


def load_texture(ref, pack_root=PACK_ROOT):
    if ref in _tex_cache:
        return _tex_cache[ref]
    from PIL import Image
    ns, _, rest = ref.partition(":")
    path = os.path.join(pack_root, "assets", ns, "textures", rest + ".png")
    arr = np.asarray(Image.open(path).convert("RGBA"), np.float32) / 255.0
    _tex_cache[ref] = arr
    return arr


def load_model(name, pack_root=PACK_ROOT):
    """-> dict(V (n,4,3) item-frame verts after element rotation (model units / 16, before centring), N (n,3), UV (n,4,2), TEX (n,) refs, EMIT (n,), TR (n,) translucent)"""
    key = (name, pack_root)
    if key in _model_cache:
        return _model_cache[key]
    path = os.path.join(pack_root, "assets", NS, "models", "item", name + ".json")
    d = json.load(open(path))
    tex = d["textures"]
    V, N, UV, TEX, EMIT, TR = [], [], [], [], [], []
    for e in d["elements"]:
        lo, hi = np.array(e["from"], float), np.array(e["to"], float)
        R = np.eye(3)
        org = np.zeros(3)
        rot = e.get("rotation")
        if rot:
            org = np.array(rot["origin"], float)
            if "axis" in rot:
                R = rax(rot["axis"], rot["angle"])
            else:
                R = from_euler_zyx(rot["x"], rot["y"], rot["z"])
        for fname, f in e["faces"].items():
            sel = FACE_VERTS[fname]
            vs = np.array([[(lo, hi)[a][0], (lo, hi)[b][1], (lo, hi)[c][2]] for a, b, c in sel], float)
            vs = org + (vs - org) @ R.T
            n = R @ np.array(FACE_DIR[fname], float)
            u0, v0, u1, v1 = f["uv"]
            uvs = np.array([[(u0, u1)[a] / 16, (v0, v1)[b] / 16] for a, b in UV_CORNER], float)
            ref = tex[f["texture"][1:]]
            t = load_texture(ref, pack_root)
            H, W = t.shape[:2]
            x0, x1 = int(round(u0 / 16 * W)), int(round(u1 / 16 * W))
            y0, y1 = int(round(v0 / 16 * H)), int(round(v1 / 16 * H))
            al = t[y0:y1, x0:x1, 3]
            tr = bool(((al > 0.02) & (al < 0.98)).any())
            V.append(vs / 16.0)
            N.append(n)
            UV.append(uvs)
            TEX.append(ref)
            EMIT.append(e.get("light_emission", 0))
            TR.append(tr)
    out = dict(V=np.array(V), N=np.array(N), UV=np.array(UV), TEX=TEX, EMIT=np.array(EMIT), TR=np.array(TR))
    _model_cache[key] = out
    return out


class Instance:
    """A model placed in rig space: the display's transformation (t, R, s) and an optional extra rigid motion (R_g about c_g, then t_g)."""

    def __init__(self, model, t=(0, 0, 0), R=None, s=1.0, motion=None, name=""):
        self.model, self.t, self.s = model, np.array(t, float), s
        self.R = np.eye(3) if R is None else np.asarray(R, float)
        self.motion = motion
        self.name = name

    def world(self, md):
        V = md["V"] - 0.5
        V = V @ F_FLIP.T
        N = md["N"] @ F_FLIP.T
        V = self.t + (V * self.s) @ self.R.T
        N = N @ self.R.T
        if self.motion:
            Rg, cg, tg = self.motion
            V = cg + (V - cg) @ np.asarray(Rg).T + tg
            N = N @ np.asarray(Rg).T
        return V, N


def dir_yaw_pitch(yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    return np.array([math.sin(y) * math.cos(p), math.sin(p), math.cos(y) * math.cos(p)])


LIGHT0 = np.array([0.2, 1.0, -0.7]) / np.linalg.norm([0.2, 1.0, -0.7])
LIGHT1 = np.array([-0.2, 1.0, 0.7]) / np.linalg.norm([-0.2, 1.0, 0.7])


def shade_of(n, ambient=0.42):
    a = np.maximum(0.0, n @ LIGHT0) + np.maximum(0.0, n @ LIGHT1)
    return np.minimum(1.0, ambient + 0.5 * a)


class Camera:
    def __init__(self, eye, target=None, yaw_pitch=None, fov=60.0, aspect=1.0, up=(0, 1, 0), fov_is_horizontal=False):
        self.eye = np.array(eye, float)
        if target is None:
            target = self.eye + dir_yaw_pitch(*yaw_pitch)
        self.M = look_matrix(self.eye, target, up)
        self.fov = fov
        self.aspect = aspect
        if fov_is_horizontal:
            self.tx = math.tan(math.radians(fov) / 2)
            self.ty = self.tx / aspect
        else:
            self.ty = math.tan(math.radians(fov) / 2)
            self.tx = self.ty * aspect


def render(instances, cam, size=(480, 360), ss=2, pack_root=PACK_ROOT, sky=((120, 160, 215), (205, 222, 240)), ground=True, gy=0.0,
           ambient=0.42, shadow=None, extra_quads=None, bg=None, brightness=1.0, cull=True, fog=None):
    """-> uint8 image (h, w, 3).  `shadow`: (x0, x1, z0, z1) rectangle that darkens the ground softly."""
    W, H = size[0] * ss, size[1] * ss
    img = np.zeros((H, W, 3), np.float32)
    zbuf = np.full((H, W), np.inf, np.float32)
    # background: sky gradient and ground plane by ray casting
    ys, xs = np.mgrid[0:H, 0:W]
    sx = ((xs + 0.5) / W * 2 - 1) * cam.tx
    sy = (1 - (ys + 0.5) / H * 2) * cam.ty
    rd = cam.M[2][None, None, :] + sx[..., None] * cam.M[0][None, None, :] + sy[..., None] * cam.M[1][None, None, :]
    rd = rd / np.linalg.norm(rd, axis=-1, keepdims=True)
    t_ = np.clip(rd[..., 1] * 0.5 + 0.5, 0, 1)
    top, hor = np.array(sky[0], np.float32) / 255, np.array(sky[1], np.float32) / 255
    img[:] = hor + (top - hor) * np.clip(rd[..., 1] * 1.6, 0, 1)[..., None]
    if bg is not None:
        img[:] = np.array(bg, np.float32) / 255
    if ground:
        with np.errstate(divide="ignore", invalid="ignore"):
            tg = (gy - cam.eye[1]) / rd[..., 1]
        m = (rd[..., 1] < -1e-4) & (tg > 0)
        gp = cam.eye[None, None, :] + rd * tg[..., None]
        gx, gz = gp[..., 0], gp[..., 2]
        chk = ((np.floor(gx / 2) + np.floor(gz / 2)) % 2) * 0.05
        gcol = np.stack([0.34 + chk, 0.35 + chk, 0.37 + chk], axis=-1)
        gcol = gcol * (0.6 + 0.4 * np.clip(1 - tg / 120, 0, 1))[..., None]
        if shadow is not None:
            x0, x1, z0, z1 = shadow
            dx = np.maximum(np.maximum(x0 - gx, gx - x1), 0)
            dz = np.maximum(np.maximum(z0 - gz, gz - z1), 0)
            sd = np.sqrt(dx * dx + dz * dz)
            gcol = gcol * (1 - 0.65 * (1 - np.clip(sd / 1.2, 0, 1)))[..., None]
        img = np.where(m[..., None], gcol, img)
        zbuf = np.where(m, tg.astype(np.float32), zbuf)
        zbuf = np.where(m, np.float32(np.inf), zbuf)   # the ground never hides geometry above it; keep depth open
    # geometry
    opaque, trans = [], []
    for inst in instances:
        md = load_model(inst.model, pack_root)
        V, N = inst.world(md)
        for i in range(len(V)):
            q = (V[i], N[i], md["UV"][i], md["TEX"][i], md["EMIT"][i])
            (trans if md["TR"][i] else opaque).append(q)
    if extra_quads:
        opaque += extra_quads
    near = 0.04
    M, eye = cam.M, cam.eye

    def project(P):
        c = (P - eye) @ M.T
        return c

    def draw(q, blend):
        v, n, uv, tref, emit = q
        c = project(v)
        # backface cull (item models are one-sided)
        if cull and np.dot(n, eye - v.mean(axis=0)) <= 0:
            return
        sh = shade_of(n, ambient) * brightness
        sh = max(sh, emit / 15.0 * brightness) if emit else sh
        tex = load_texture(tref, pack_root)
        th, tw = tex.shape[:2]
        # clip against the near plane
        poly = [(c[i], uv[i]) for i in range(4)]
        out = []
        for i in range(4):
            a, b = poly[i], poly[(i + 1) % 4]
            ina, inb = a[0][2] > near, b[0][2] > near
            if ina:
                out.append(a)
            if ina != inb:
                t = (near - a[0][2]) / (b[0][2] - a[0][2])
                out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
        if len(out) < 3:
            return
        P3 = np.array([o[0] for o in out])
        UVs = np.array([o[1] for o in out])
        px = (P3[:, 0] / P3[:, 2] / cam.tx * 0.5 + 0.5) * W
        py = (0.5 - P3[:, 1] / P3[:, 2] / cam.ty * 0.5) * H
        iz = 1.0 / P3[:, 2]
        for k in range(1, len(out) - 1):
            idx = (0, k, k + 1)
            _tri(px[list(idx)], py[list(idx)], iz[list(idx)], UVs[list(idx)], tex, th, tw, sh, blend)

    def _tri(px, py, iz, uv, tex, th, tw, sh, blend):
        x0 = max(int(math.floor(px.min())), 0)
        x1 = min(int(math.ceil(px.max())), W - 1)
        y0 = max(int(math.floor(py.min())), 0)
        y1 = min(int(math.ceil(py.max())), H - 1)
        if x1 < x0 or y1 < y0:
            return
        den = (py[1] - py[2]) * (px[0] - px[2]) + (px[2] - px[1]) * (py[0] - py[2])
        if abs(den) < 1e-12:
            return
        gx, gy_ = np.meshgrid(np.arange(x0, x1 + 1) + 0.5, np.arange(y0, y1 + 1) + 0.5)
        w0 = ((py[1] - py[2]) * (gx - px[2]) + (px[2] - px[1]) * (gy_ - py[2])) / den
        w1 = ((py[2] - py[0]) * (gx - px[2]) + (px[0] - px[2]) * (gy_ - py[2])) / den
        w2 = 1 - w0 - w1
        inside = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        if not inside.any():
            return
        izz = w0 * iz[0] + w1 * iz[1] + w2 * iz[2]
        z = 1.0 / np.maximum(izz, 1e-9)
        zb = zbuf[y0:y1 + 1, x0:x1 + 1]
        ok = inside & (z < zb)
        if not ok.any():
            return
        u = (w0 * uv[0, 0] * iz[0] + w1 * uv[1, 0] * iz[1] + w2 * uv[2, 0] * iz[2]) * z
        v = (w0 * uv[0, 1] * iz[0] + w1 * uv[1, 1] * iz[1] + w2 * uv[2, 1] * iz[2]) * z
        u = np.nan_to_num(u, nan=0.0, posinf=0.0, neginf=0.0)
        v = np.nan_to_num(v, nan=0.0, posinf=0.0, neginf=0.0)
        ti = np.clip(u * tw, 0, tw - 1).astype(int)
        tj = np.clip(v * th, 0, th - 1).astype(int)
        px_ = tex[tj, ti]
        a = px_[..., 3]
        if blend:
            ok = ok & (a > 0.02)
            if not ok.any():
                return
            sub = img[y0:y1 + 1, x0:x1 + 1]
            col = px_[..., :3] * sh
            sub[:] = np.where(ok[..., None], sub * (1 - a[..., None]) + col * a[..., None], sub)
        else:
            ok = ok & (a >= 0.5)
            if not ok.any():
                return
            sub = img[y0:y1 + 1, x0:x1 + 1]
            sub[:] = np.where(ok[..., None], px_[..., :3] * sh, sub)
            zb[:] = np.where(ok, z, zb)

    for q in opaque:
        draw(q, False)
    trans.sort(key=lambda q: -float(((q[0].mean(axis=0) - eye) @ M[2])))
    for q in trans:
        draw(q, True)
    img = np.clip(img, 0, 1)
    if ss > 1:
        img = img.reshape(size[1], ss, size[0], ss, 3).mean(axis=(1, 3))
    return (img * 255 + 0.5).astype(np.uint8)


def save(img, path, label=None, scale=1):
    from PIL import Image, ImageDraw
    im = Image.fromarray(img)
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.LANCZOS)
    if label:
        d = ImageDraw.Draw(im)
        d.rectangle((0, 0, im.width, 14), fill=(0, 0, 0))
        d.text((4, 2), label, fill=(255, 255, 255))
    im.save(path)


def contact_sheet(images, cols, path, pad=4, bg=(30, 30, 34)):
    from PIL import Image
    ims = [Image.fromarray(i) if not hasattr(i, "save") else i for i in images]
    w, h = ims[0].size
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (w + pad) + pad, rows * (h + pad) + pad), bg)
    for k, im in enumerate(ims):
        sheet.paste(im, (pad + (k % cols) * (w + pad), pad + (k // cols) * (h + pad)))
    sheet.save(path)
