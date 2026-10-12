"""Builder helpers on top of mdl.Model: mirrored (left/right) building, oriented boxes, lofted surfaces made of thin tilted slabs, rings and discs
(round things made of rotated slabs), Catmull-Rom profiles."""
import math

import numpy as np

from .mdl import LETTER, MIRROR_FACE
from .vmath import I3, mirror_x_mat, rax

SW = {"f": "f", "b": "b", "l": "r", "r": "l", "u": "u", "d": "d"}


def catmull(pts, n=8):
    """Smooth curve through points [(x, y), ...] (centripetal-ish Catmull-Rom, uniform), returns an interpolating function f(x) for monotone x."""
    pts = sorted(tuple(map(float, p)) for p in pts)
    xs = np.array([p[0] for p in pts])
    ys = np.array([p[1] for p in pts])
    # monotone cubic (PCHIP) interpolation
    h = np.diff(xs)
    d = np.diff(ys) / h
    m = np.zeros(len(xs))
    m[0], m[-1] = d[0], d[-1]
    for i in range(1, len(xs) - 1):
        if d[i - 1] * d[i] > 0:
            w1, w2 = 2 * h[i] + h[i - 1], h[i] + 2 * h[i - 1]
            m[i] = (w1 + w2) / (w1 / d[i - 1] + w2 / d[i])
    def f(x):
        x = np.asarray(x, float)
        i = np.clip(np.searchsorted(xs, x) - 1, 0, len(xs) - 2)
        t = (x - xs[i]) / h[i]
        h00, h10, h01, h11 = 2 * t ** 3 - 3 * t ** 2 + 1, t ** 3 - 2 * t ** 2 + t, -2 * t ** 3 + 3 * t ** 2, t ** 3 - t ** 2
        return h00 * ys[i] + h10 * h[i] * m[i] + h01 * ys[i + 1] + h11 * h[i] * m[i + 1]
    return f


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


class Bld:
    """Adds elements to a Model through a sheet; side=-1 builds the x-mirror image of everything it is given (so a wing is written once)."""

    def __init__(self, model, sheet, side=1, density=None):
        self.m, self.sheet, self.side, self.density = model, sheet, side, density

    # ---------------------------------------------------------------------------------------------- primitives
    def box(self, lo, hi, style, faces="fblrud", R=None, pivot=None, sheet=None, **kw):
        lo, hi = np.array(lo, float), np.array(hi, float)
        R = None if R is None else np.asarray(R, float)
        pivot = None if pivot is None else np.array(pivot, float)
        if self.side < 0:
            lo, hi = np.array([-hi[0], lo[1], lo[2]]), np.array([-lo[0], hi[1], hi[2]])
            if R is not None:
                R = mirror_x_mat(R)
            if pivot is not None:
                pivot = np.array([-pivot[0], pivot[1], pivot[2]])
            faces = "".join(SW[c] for c in faces)
            if isinstance(style, dict):
                style = {SW.get(k, k): v for k, v in style.items()}
        if self.density and "density" not in kw:
            kw["density"] = self.density
        return self.m.add(lo, hi, sheet or self.sheet, style, faces, R=R, pivot=pivot, **kw)

    def ob(self, centre, size, R, style, faces="fblrud", **kw):
        """An oriented box: `size` (x, y, z extents in its own frame), rotated by R about `centre`."""
        c = np.array(centre, float)
        h = np.array(size, float) / 2
        return self.box(c - h, c + h, style, faces, R=R, pivot=c, **kw)

    def strip(self, p00, p10, p01, p11, t, style, faces="u", hint=(0, 1, 0), grow=0.12, **kw):
        """A thin slab following a (nearly planar) quad of the surface: p00 origin corner, p10 along the first edge, p01 along the second, p11 opposite.
        The slab lies below the surface by t; the texture face 'u' is the surface's outer side, chosen to agree with `hint`."""
        p00, p10, p01, p11 = (np.array(p, float) for p in (p00, p10, p01, p11))
        ex = (p10 - p00 + p11 - p01) / 2
        ez = (p01 - p00 + p11 - p10) / 2
        w, l = np.linalg.norm(ex), np.linalg.norm(ez)
        if w < 1e-6 or l < 1e-6:
            return None
        ex = ex / w
        ez = ez - ex * np.dot(ez, ex)
        ez = ez / np.linalg.norm(ez)
        ey = np.cross(ez, ex)
        if np.dot(ey, np.array(hint, float)) < 0:
            ex, ez = ez, ex
            w, l = l, w
            ey = np.cross(ez, ex)
        R = np.stack([ex, ey, ez], axis=1)
        cen = (p00 + p10 + p01 + p11) / 4 - ey * (t / 2)
        size = (w * (1 + grow) + 0.02, t, l * (1 + grow) + 0.02)
        return self.ob(cen, size, R, style, faces, **kw)

    def loft(self, fn, us, vs, t, style, faces="u", hint=(0, 1, 0), percell=False, **kw):
        """Cells over a grid: fn(u, v) -> point; one slab per cell.  percell=True: `style(i, j, ni, nj)` returns (painter, kwargs) for each cell
        (edge control: only the boundary cells get hard edges)."""
        pts = [[np.array(fn(u, v), float) for v in vs] for u in us]
        out = []
        for i in range(len(us) - 1):
            for j in range(len(vs) - 1):
                st = style(i, j, len(us) - 1, len(vs) - 1) if percell else style
                if isinstance(st, tuple):
                    painter, kws = st
                    e = self.strip(pts[i][j], pts[i + 1][j], pts[i][j + 1], pts[i + 1][j + 1], t, painter, faces, hint, **{**kw, **kws})
                else:
                    e = self.strip(pts[i][j], pts[i + 1][j], pts[i][j + 1], pts[i + 1][j + 1], t, st, faces, hint, **kw)
                out.append(e)
        return out

    # ---------------------------------------------------------------------------------------------- round things
    _AX = {  # axis -> (axial index, radial0 index, tangential0 index, rotation axis, faces: out, in, a0, a1)
        "x": (0, 1, 2, "x", ("u", "d", "r", "l")),
        "y": (1, 2, 0, "y", ("f", "b", "d", "u")),
        "z": (2, 0, 1, "z", ("l", "r", "b", "f")),
    }

    def ring(self, axis, c, r_out, r_in, a0, a1, n, style, start=0.0, sweep=360.0, faces=("out", "a0", "a1"), overlap=1.02, R0=None, **kw):
        """A ring (or arc) of n tangent slabs around axis through centre c: radial thickness r_out - r_in, axial range a0..a1 (rig coordinates along the axis).
        style: painter or dict {out, in, a0, a1: painter or (painter, kwargs)}.  Angles in degrees; angle 0 points along +y (axis x), +z (axis y), +x (axis z)."""
        ax, rad, tan, rotax, (fo, fi, fa0, fa1) = self._AX[axis]
        step = sweep / n if sweep < 359.9 else 360.0 / n
        L = 2 * r_out * math.tan(math.radians(step) / 2) * overlap
        letters = {"out": fo, "in": fi, "a0": fa0, "a1": fa1}
        out = []
        for k in range(n):
            phi = start + (k + 0.5) * step
            lo = np.zeros(3)
            hi = np.zeros(3)
            lo[ax], hi[ax] = a0, a1
            lo[rad], hi[rad] = c[rad] + r_in, c[rad] + r_out
            lo[tan], hi[tan] = c[tan] - L / 2, c[tan] + L / 2
            piv = np.array(c, float)
            piv[ax] = (a0 + a1) / 2
            R = rax(rotax, phi) if R0 is None else R0 @ rax(rotax, phi)
            fl = "".join(letters[f] for f in faces)
            st = style
            if isinstance(style, dict):
                st = {letters[sem]: v for sem, v in style.items() if sem in letters}
            out.append(self.box(lo, hi, st, fl, R=R, pivot=piv, **kw))
        return out

    def disc(self, axis, c, r, a0, a1, n, style, faces=("a0", "a1"), R0=None, **kw):
        """A flat polygonal disc of radius r (circumradius 1/cos(180/n) larger) made of n/2 rectangles through the centre; each has faces on both axial sides."""
        ax, rad, tan, rotax, (fo, fi, fa0, fa1) = self._AX[axis]
        h = r * math.tan(math.pi / n)
        letters = {"a0": fa0, "a1": fa1, "out": fo, "in": fi}
        out = []
        for k in range(n // 2):
            phi = k * 360.0 / n
            lo = np.zeros(3)
            hi = np.zeros(3)
            lo[ax], hi[ax] = a0, a1
            lo[rad], hi[rad] = c[rad] - r, c[rad] + r
            lo[tan], hi[tan] = c[tan] - h, c[tan] + h
            piv = np.array(c, float)
            piv[ax] = (a0 + a1) / 2
            R = rax(rotax, phi) if R0 is None else R0 @ rax(rotax, phi)
            fl = "".join(letters[f] for f in faces)
            st = style
            if isinstance(style, dict):
                st = {letters[sem]: v for sem, v in style.items() if sem in letters}
            out.append(self.box(lo, hi, st, fl, R=R, pivot=piv, **kw))
        return out

    def cyl(self, axis, c, r, a0, a1, n, style, caps=True, **kw):
        """A solid-looking cylinder: ring of tangent slabs (outer faces only) plus end discs."""
        e = self.ring(axis, c, r, r * 0.7, a0, a1, n, style if not isinstance(style, dict) else style, faces=("out",), **kw)
        return e
