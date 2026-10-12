"""Model authoring: cuboid elements in rig space, texture sheets painted per face, item model JSON and item definitions.

Rig space: +x LEFT, +y up, +z FORWARD (blocks).  Face names are rig names: front (+z), back (-z), left (+x), right (-x), up, down.
A model is authored in rig coordinates (or in "raw" coordinates if the part is displayed with a scale); `Model.center` is the point that
the item display puts at the entity's origin, so a part with scale 1 needs a translation equal to the centre, nothing else.

Conversion to the item model frame (26.3: an item display turns its model 180 degrees about y after centring it at the origin):
    model_x = 8 - 16 (x - cx),  model_y = 8 + 16 (y - cy),  model_z = 8 - 16 (z - cz)
so rig front becomes the model's NORTH face, rig left its WEST, rig right EAST, rig back SOUTH.  UV orientation follows from vanilla's
vertex tables (see FACE_GEOM): u runs to the viewer's right, v downward, seen from outside the face.
"""
import json
import math
import os

import numpy as np

from .vmath import I3, euler_zyx, mirror_x_mat

FACES = ("front", "back", "left", "right", "up", "down")
LETTER = {"f": "front", "b": "back", "l": "left", "r": "right", "u": "up", "d": "down"}
VANILLA = {"front": "north", "back": "south", "left": "west", "right": "east", "up": "up", "down": "down"}
NORMAL = {"front": (0, 0, 1), "back": (0, 0, -1), "left": (1, 0, 0), "right": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
MIRROR_FACE = {"front": "front", "back": "back", "left": "right", "right": "left", "up": "up", "down": "down"}
MIN_EXT, MAX_EXT = -16.0, 32.0

PACK_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "pack", "angel-resources"))
NS = "angel"


def face_geom(lo, hi, face):
    """(corner, u_vec, v_vec) of a face of the unrotated box: the texture's top-left corner and the full-length vectors of its u and v axes.

    Taken from vanilla's FaceInfo vertex order (vertex 0 = (minU, minV), 1 = (minU, maxV), 2 = (maxU, maxV), 3 = (maxU, minV)) mapped through the
    180 degree turn about y that an item display applies (verified in the 26.3 jar: DisplayRenderer$ItemDisplayRenderer.submitInner rotates by pi about +y)."""
    lx, ly, lz = lo
    hx, hy, hz = hi
    if face == "front":
        return (lx, hy, hz), (hx - lx, 0, 0), (0, ly - hy, 0)
    if face == "back":
        return (hx, hy, lz), (lx - hx, 0, 0), (0, ly - hy, 0)
    if face == "left":
        return (hx, hy, hz), (0, 0, lz - hz), (0, ly - hy, 0)
    if face == "right":
        return (lx, hy, lz), (0, 0, hz - lz), (0, ly - hy, 0)
    if face == "up":
        return (hx, hy, hz), (lx - hx, 0, 0), (0, 0, lz - hz)
    if face == "down":
        return (hx, ly, lz), (lx - hx, 0, 0), (0, 0, hz - lz)
    raise ValueError(face)


class Region:
    """A rectangle of a sheet (inner size w x h; `pad` pixels of replicated edge around it)."""

    def __init__(self, sheet, w, h):
        self.sheet, self.w, self.h = sheet, int(w), int(h)
        self.x = self.y = None
        self.painter = None

    def uv(self):
        s = self.sheet
        return [round(self.x / s.W * 16, 5), round(self.y / s.H * 16, 5), round((self.x + self.w) / s.W * 16, 5), round((self.y + self.h) / s.H * 16, 5)]


class Sheet:
    """One texture (a PNG in textures/item/): faces ask for regions, `pack` places them, `render` paints them."""

    def __init__(self, name, density=56, pad=2, min_size=64, max_size=4096, translucent=False):
        self.name, self.density, self.pad = name, density, pad
        self.min_size, self.max_size = min_size, max_size
        self.regions = []
        self.cache = {}
        self.W = self.H = None
        self.translucent = translucent

    @property
    def ref(self):
        return f"{NS}:item/{self.name}"

    def alloc(self, w, h, key=None):
        if key is not None and key in self.cache:
            return self.cache[key]
        w = max(2, min(int(w), 1024))
        h = max(2, min(int(h), 1024))
        r = Region(self, w, h)
        self.regions.append(r)
        if key is not None:
            self.cache[key] = r
        return r

    def pack(self):
        p = self.pad
        area = sum((r.w + 2 * p) * (r.h + 2 * p) for r in self.regions)
        size = self.min_size
        while True:
            if size > self.max_size:
                raise RuntimeError(f"sheet {self.name}: does not fit in {self.max_size}px (area {area})")
            if area * 1.25 <= size * size and self._shelf(size):
                break
            size *= 2
        # shrink the height to the used rows (power of two)
        used = max((r.y + r.h + p) for r in self.regions) if self.regions else 1
        H = self.min_size
        while H < used:
            H *= 2
        self.W, self.H = size, min(size, H)
        return self

    def _shelf(self, W):
        p = self.pad
        order = sorted(self.regions, key=lambda r: (-r.h, -r.w))
        x = y = rowh = 0
        for r in order:
            rw, rh = r.w + 2 * p, r.h + 2 * p
            if rw > W:
                return False
            if x + rw > W:
                x, y, rowh = 0, y + rowh, 0
            r.x, r.y = x + p, y + p
            x += rw
            rowh = max(rowh, rh)
        return (y + rowh) <= W

    def render(self):
        arr = np.zeros((self.H, self.W, 4), np.float32)
        p = self.pad
        for r in self.regions:
            if r.painter is None:
                tile = np.zeros((r.h, r.w, 4), np.float32)
                tile[..., :3] = 0.5
                tile[..., 3] = 1.0
            else:
                tile = r.painter(r)
            arr[r.y:r.y + r.h, r.x:r.x + r.w] = tile
            # replicate the edge into the padding ring (mip levels and neighbours never bleed a foreign colour in)
            if p:
                arr[r.y - p:r.y, r.x:r.x + r.w] = tile[:1]
                arr[r.y + r.h:r.y + r.h + p, r.x:r.x + r.w] = tile[-1:]
                arr[r.y - p:r.y + r.h + p, r.x - p:r.x] = arr[r.y - p:r.y + r.h + p, r.x:r.x + 1]
                arr[r.y - p:r.y + r.h + p, r.x + r.w:r.x + r.w + p] = arr[r.y - p:r.y + r.h + p, r.x + r.w - 1:r.x + r.w]
        return arr

    def save(self, path):
        from PIL import Image
        arr = np.clip(self.render(), 0, 1)
        Image.fromarray((arr * 255 + 0.5).astype(np.uint8), "RGBA").save(path)


class Elem:
    """One cuboid.  lo/hi in rig space before rotation; `R` (3x3, rig space) rotates it about `pivot`."""

    def __init__(self, lo, hi, R=None, pivot=None, emit=0, faces=None, kind="car", tag=""):
        self.lo = np.array(lo, float)
        self.hi = np.array(hi, float)
        self.R = I3 if R is None else np.asarray(R, float)
        self.pivot = (self.lo + self.hi) / 2 if pivot is None else np.array(pivot, float)
        self.emit = int(emit)
        self.faces = faces or {}            # rig face name -> dict(region, sheet)
        self.kind = kind                    # "car" (opaque) or "glass" (see-through) for the sight-line measurement
        self.tag = tag

    def rotated(self):
        return not np.allclose(self.R, I3, atol=1e-9)

    def corners_world(self):
        out = []
        for ix in (0, 1):
            for iy in (0, 1):
                for iz in (0, 1):
                    p = np.array([(self.lo, self.hi)[ix][0], (self.lo, self.hi)[iy][1], (self.lo, self.hi)[iz][2]])
                    out.append(self.pivot + self.R @ (p - self.pivot))
        return np.array(out)

    def box(self):
        """(t, R, size): the oriented box's lower corner, rotation and size in rig space, for ray casting."""
        t = self.pivot + self.R @ (self.lo - self.pivot)
        return t, self.R, self.hi - self.lo

    def mirrored(self, sheet_faces_map=None):
        lo = np.array([-self.hi[0], self.lo[1], self.lo[2]])
        hi = np.array([-self.lo[0], self.hi[1], self.hi[2]])
        piv = np.array([-self.pivot[0], self.pivot[1], self.pivot[2]])
        return Elem(lo, hi, mirror_x_mat(self.R), piv, self.emit, None, self.kind, self.tag)


class Model:
    """A block-style item model: elements in rig space with a centre.  `sheets` are the textures its faces refer to."""

    def __init__(self, name, center=None, scale=1.0):
        self.name = name
        self.center = None if center is None else np.array(center, float)
        self.scale = scale
        self.elems = []
        self.sheets = []
        self.specs = []                      # per element: dict(face letters, styles) so that a mirror can repaint

    # ------------------------------------------------------------------------------------------------ building
    def add(self, lo, hi, sheet, style, faces="fblrud", R=None, pivot=None, density=None, emit=0, kind=None, tag="", shared=None, **kw):
        """Add a cuboid.  `style` is a painter (callable(ctx, **kw) -> RGBA float array) or a dict {face letter: (painter, kwargs)} with
        key "*" for the rest.  Only the faces named in `faces` exist (hidden faces cost nothing).  Returns the element."""
        lo = np.array(lo, float)
        hi = np.array(hi, float)
        if np.any(hi - lo < -1e-9):
            lo, hi = np.minimum(lo, hi), np.maximum(lo, hi)
        e = Elem(lo, hi, R, pivot, emit, None, kind or ("glass" if sheet.translucent else "car"), tag)
        if sheet not in self.sheets:
            self.sheets.append(sheet)
        dens = density or sheet.density
        for ch in faces:
            f = LETTER[ch]
            corner, uv_, vv_ = face_geom(e.lo, e.hi, f)
            ul, vl = float(np.linalg.norm(uv_)), float(np.linalg.norm(vv_))
            if ul < 1e-6 or vl < 1e-6:
                continue
            if isinstance(style, dict):
                st = style.get(ch) or style.get("*")
                if st is None:
                    continue
                painter, kws = (st if isinstance(st, tuple) else (st, {}))
            else:
                painter, kws = style, kw
            w, h = int(math.ceil(ul * dens)), int(math.ceil(vl * dens))
            key = None
            if shared is not None:
                key = (shared, f, round(ul, 3), round(vl, 3))
            reg = sheet.alloc(w, h, key)
            if reg.painter is None:
                reg.painter = _make_painter(painter, kws, e, f, corner, uv_, vv_, ul, vl, sheet.density if density is None else density)
            e.faces[f] = dict(region=reg, sheet=sheet)
        self.elems.append(e)
        return e

    def extent(self):
        pts = np.concatenate([e.corners_world() for e in self.elems])
        return pts.min(axis=0), pts.max(axis=0)

    def auto_center(self):
        lo, hi = self.extent()
        self.center = np.round((lo + hi) / 2, 3)
        return self.center

    # ------------------------------------------------------------------------------------------------ output
    def to_json(self):
        c = self.center
        if c is None:
            c = self.auto_center()
        F = np.diag([-1.0, 1.0, -1.0])
        tex_keys = {s.name: str(i) for i, s in enumerate(self.sheets)}
        textures = {tex_keys[s.name]: s.ref for s in self.sheets}
        elements = []
        for e in self.elems:
            mlo = [8 - 16 * (e.hi[0] - c[0]), 8 + 16 * (e.lo[1] - c[1]), 8 - 16 * (e.hi[2] - c[2])]
            mhi = [8 - 16 * (e.lo[0] - c[0]), 8 + 16 * (e.hi[1] - c[1]), 8 - 16 * (e.lo[2] - c[2])]
            d = {"from": [round(v, 4) for v in mlo], "to": [round(v, 4) for v in mhi]}
            if e.rotated():
                Rm = F @ e.R @ F
                ax, ay, az = euler_zyx(Rm)
                org = [8 - 16 * (e.pivot[0] - c[0]), 8 + 16 * (e.pivot[1] - c[1]), 8 - 16 * (e.pivot[2] - c[2])]
                d["rotation"] = {"origin": [round(v, 4) for v in org], "x": round(ax, 4), "y": round(ay, 4), "z": round(az, 4)}
            if e.emit:
                d["light_emission"] = e.emit
            faces = {}
            for f, fi in e.faces.items():
                faces[VANILLA[f]] = {"uv": fi["region"].uv(), "texture": "#" + tex_keys[fi["sheet"].name]}
            d["faces"] = faces
            elements.append(d)
        return {"textures": textures, "elements": elements}

    def item_definition(self):
        return {"model": {"type": "minecraft:model", "model": f"{NS}:item/{self.name}"}}

    def write(self, pack_root=PACK_ROOT):
        mdir = os.path.join(pack_root, "assets", NS, "models", "item")
        idir = os.path.join(pack_root, "assets", NS, "items")
        os.makedirs(mdir, exist_ok=True)
        os.makedirs(idir, exist_ok=True)
        with open(os.path.join(mdir, self.name + ".json"), "w", newline="\n") as fh:
            json.dump(self.to_json(), fh, separators=(",", ":"))
        with open(os.path.join(idir, self.name + ".json"), "w", newline="\n") as fh:
            json.dump(self.item_definition(), fh, separators=(",", ":"))



def _make_painter(painter, kws, e, face, corner, u_vec, v_vec, ul, vl, density):
    """Closure that paints a region: builds the PaintCtx (rig-space position of every texel) when the sheet is rendered."""
    corner = np.array(corner, float)
    u_vec = np.array(u_vec, float)
    v_vec = np.array(v_vec, float)
    R, piv = e.R, e.pivot

    def paint(region):
        w, h = region.w, region.h
        us = (np.arange(w) + 0.5) / w
        vs = (np.arange(h) + 0.5) / h
        U, V = np.meshgrid(us, vs)
        P = corner[None, None, :] + U[..., None] * u_vec[None, None, :] + V[..., None] * v_vec[None, None, :]
        N = np.array(NORMAL[face], float)
        if e.rotated():
            P = piv[None, None, :] + (P - piv[None, None, :]) @ R.T
            N = R @ N
            uh, vh = R @ (u_vec / ul), R @ (v_vec / vl)
        else:
            uh, vh = u_vec / ul, v_vec / vl
        ctx = PaintCtx(w, h, ul, vl, U, V, P, N, uh, vh, face, e)
        out = painter(ctx, **kws)
        if out.shape[-1] == 3:
            out = np.concatenate([out, np.ones((h, w, 1), np.float32)], axis=-1)
        return np.clip(out, 0, 1).astype(np.float32)

    return paint


class PaintCtx:
    """What a painter gets: texel grid of a face (w x h), the face's size in blocks, the rig-space point of every texel (P), the outward
    normal N, the directions of u and v (unit rig vectors), distances to the four edges in blocks."""

    def __init__(self, w, h, ul, vl, U, V, P, N, uh, vh, face, elem):
        self.w, self.h, self.ul, self.vl = w, h, ul, vl
        self.U, self.V, self.P, self.N, self.uh, self.vh, self.face, self.elem = U, V, P, N, uh, vh, face, elem
        self.dl = U * ul                      # distance to the left edge (blocks)
        self.dr = (1 - U) * ul
        self.dt = V * vl
        self.db = (1 - V) * vl

    @property
    def edge(self):
        return np.minimum(np.minimum(self.dl, self.dr), np.minimum(self.dt, self.db))

    @property
    def x(self):
        return self.P[..., 0]

    @property
    def y(self):
        return self.P[..., 1]

    @property
    def z(self):
        return self.P[..., 2]

    @property
    def px(self):
        """blocks per texel"""
        return self.ul / self.w


# ---------------------------------------------------------------------------------------------------- validation
def validate_pack(pack_root=PACK_ROOT, names=None, verbose=False):
    """Check every model JSON of the pack that this library wrote against what 26.3 accepts.  Returns (errors, warnings, stats)."""
    from PIL import Image
    errs, warns = [], []
    mdir = os.path.join(pack_root, "assets", NS, "models", "item")
    idir = os.path.join(pack_root, "assets", NS, "items")
    tdir = os.path.join(pack_root, "assets", NS, "textures", "item")
    stats = {"models": 0, "elements": 0, "faces": 0, "rotated": 0}
    files = sorted(f for f in os.listdir(mdir) if f.endswith(".json")) if os.path.isdir(mdir) else []
    if names:
        files = [f for f in files if f[:-5] in names]
    tex_cache = {}
    face_names = {"north", "south", "east", "west", "up", "down"}
    for fn in files:
        nm = fn[:-5]
        path = os.path.join(mdir, fn)
        try:
            d = json.load(open(path))
        except Exception as ex:
            errs.append(f"{fn}: not valid JSON ({ex})")
            continue
        stats["models"] += 1
        # the item model definition
        ip = os.path.join(idir, fn)
        if not os.path.isfile(ip):
            errs.append(f"{fn}: no item definition assets/angel/items/{fn}")
        else:
            idf = json.load(open(ip))
            if idf.get("model", {}).get("model") != f"{NS}:item/{nm}" or idf.get("model", {}).get("type") != "minecraft:model":
                errs.append(f"{fn}: item definition does not point at {NS}:item/{nm}")
        tex = d.get("textures", {})
        for k, ref in tex.items():
            ns, _, rest = ref.partition(":")
            if ns != NS:
                errs.append(f"{fn}: texture {ref} is not in namespace {NS}")
            tp = os.path.join(tdir, rest.replace("item/", "", 1) + ".png")
            if not os.path.isfile(tp):
                errs.append(f"{fn}: texture {ref} missing ({tp})")
            elif tp not in tex_cache:
                im = Image.open(tp)
                tex_cache[tp] = im.size
        els = d.get("elements", [])
        if not els:
            errs.append(f"{fn}: no elements")
        if len(els) > 2000:
            warns.append(f"{fn}: {len(els)} elements")
        for i, e in enumerate(els):
            stats["elements"] += 1
            where = f"{fn} element {i}"
            fr, to = e.get("from"), e.get("to")
            if not (isinstance(fr, list) and isinstance(to, list) and len(fr) == 3 and len(to) == 3):
                errs.append(f"{where}: from/to malformed")
                continue
            for a in fr + to:
                if not (MIN_EXT <= a <= MAX_EXT):
                    errs.append(f"{where}: coordinate {a} outside {MIN_EXT:g}..{MAX_EXT:g} (3 blocks around the model centre)")
                    break
            for a, b in zip(fr, to):
                if b < a:
                    errs.append(f"{where}: to < from")
                    break
            if "light_emission" in e and not (isinstance(e["light_emission"], int) and 0 <= e["light_emission"] <= 15):
                errs.append(f"{where}: light_emission must be an integer 0..15")
            rot = e.get("rotation")
            if rot is not None:
                stats["rotated"] += 1
                if "origin" not in rot:
                    errs.append(f"{where}: rotation without origin")
                if "axis" in rot:
                    if rot["axis"] not in ("x", "y", "z") or "angle" not in rot:
                        errs.append(f"{where}: bad single-axis rotation")
                elif not all(k in rot for k in ("x", "y", "z")):
                    errs.append(f"{where}: Euler rotation needs x, y and z")
                for k in ("x", "y", "z", "angle"):
                    if k in rot and not isinstance(rot[k], (int, float)):
                        errs.append(f"{where}: rotation {k} is not a number")
            faces = e.get("faces", {})
            if not (1 <= len(faces) <= 6):
                errs.append(f"{where}: needs 1..6 faces (has {len(faces)})")
            for fname, f in faces.items():
                stats["faces"] += 1
                if fname not in face_names:
                    errs.append(f"{where}: unknown face {fname}")
                    continue
                t = f.get("texture")
                if not (isinstance(t, str) and t.startswith("#") and t[1:] in tex):
                    errs.append(f"{where}/{fname}: texture reference {t} not defined in textures")
                uv = f.get("uv")
                if uv is None:
                    warns.append(f"{where}/{fname}: no uv (vanilla would derive one)")
                else:
                    if len(uv) != 4 or any(not (0.0 <= v <= 16.0) for v in uv) or uv[2] <= uv[0] or uv[3] <= uv[1]:
                        errs.append(f"{where}/{fname}: uv {uv} outside 0..16 or empty")
    return errs, warns, stats

