"""Glass around the head: the dark capsule, the rising amber fluid, the amber cockpit, the white-out.

Why six slabs and not one cube: the faces of a block display are drawn from outside only (back faces are culled, see models.py), so the
camera inside a single big display would see nothing.  A box of six thin slabs, each seen from the side that faces the middle, is drawn
correctly from inside; every ray from a camera in the middle crosses exactly one slab, so the tint is even and no edges show.

Everything made here carries angel.story (halt kills it) and angel.launch (the restore function kills it) and a tag of its own, and
is changed afterwards with `data merge entity` (block_state is a plain string in 26.x).

Coordinates may be numbers (world) or strings such as "~-6.5" (relative to where the command runs).
"""
from core import TAG, fnum, num

THIN = 0.03


def _c(v):
    return v if isinstance(v, str) else num(v)


def _rel(base, off):
    """a coordinate `off` from `base`; base None means 'relative to the command position'"""
    if base is None:
        return f"~{num(off)}"
    return base + off


def _tf(sx, sy, sz, tx=0.0, ty=0.0, tz=0.0):
    return (f"transformation:{{translation:[{fnum(tx)},{fnum(ty)},{fnum(tz)}],left_rotation:[0f,0f,0f,1f],"
            f"scale:[{fnum(sx)},{fnum(sy)},{fnum(sz)}],right_rotation:[0f,0f,0f,1f]}}")


def slab(tags, block, x, y, z, sx, sy, sz, bright=None, view_range=1.0, ty=0.0):
    """summon one block_display spanning (x, y, z) .. (x+sx, y+sy, z+sz); `ty` lifts it inside its own transformation (the fluid's lid)"""
    br = f",brightness:{{sky:{bright},block:{bright}}}" if bright is not None else ""
    tg = ",".join(f'"{t}"' for t in [TAG, "angel.launch"] + list(tags))
    return (f'summon minecraft:block_display {_c(x)} {_c(y)} {_c(z)} {{Tags:[{tg}],block_state:"minecraft:{block}",'
            f'teleport_duration:0,interpolation_duration:0,view_range:{fnum(view_range)}{br},{_tf(sx, sy, sz, 0.0, ty, 0.0)}}}')


def box_shell(tag, block, centre, half, t=THIN, bright=None, view_range=1.0, layers=1, gap=0.05):
    """Six slabs just inside the box with half sizes `half` = (hx, hy, hz) about `centre` = (cx, cy, cz), all carrying `tag`.
    centre None: relative to the position the command runs at (use it with `execute positioned ...`).
    layers: that many boxes, each `gap` smaller than the one outside it (stained glass is only 46 % opaque: three layers of black
    glass dim the view to about 16 %, two of orange make it mostly amber)."""
    if layers > 1:
        out = []
        for k in range(layers):
            out += box_shell(tag, block, centre, (half[0] - k * gap, half[1] - k * gap, half[2] - k * gap), t, bright, view_range)
        return out
    hx, hy, hz = half
    cx, cy, cz = centre if centre else (None, None, None)
    X = lambda off: _rel(cx, off)
    Y = lambda off: _rel(cy, off)
    Z = lambda off: _rel(cz, off)
    return [
        slab([tag, tag + "_w"], block, X(-hx), Y(-hy), Z(-hz), t, 2 * hy, 2 * hz, bright, view_range),
        slab([tag, tag + "_e"], block, X(hx - t), Y(-hy), Z(-hz), t, 2 * hy, 2 * hz, bright, view_range),
        slab([tag, tag + "_n"], block, X(-hx), Y(-hy), Z(-hz), 2 * hx, 2 * hy, t, bright, view_range),
        slab([tag, tag + "_s"], block, X(-hx), Y(-hy), Z(hz - t), 2 * hx, 2 * hy, t, bright, view_range),
        slab([tag, tag + "_d"], block, X(-hx), Y(-hy), Z(-hz), 2 * hx, t, 2 * hz, bright, view_range),
        slab([tag, tag + "_u"], block, X(-hx), Y(hy - t), Z(-hz), 2 * hx, t, 2 * hz, bright, view_range),
    ]


def set_block(tag, block):
    """Change the block of every slab with `tag`."""
    return f'execute as @e[tag={tag}] run data merge entity @s {{block_state:"minecraft:{block}"}}'


def kill(tag):
    return f"kill @e[tag={tag}]"


# ------------------------------------------------------------------------------------------------ the rising fluid
class Fluid:
    """Amber glass that fills a box from the floor up: four walls that grow and a lid that rises with them (the lid is seen from above
    while the level is below the eyes and from below once it has passed them).  Walls and lid are inset from the capsule's own walls."""

    def __init__(self, tag, block, x0, x1, y0, y1, z0, z1, bright=None, layers=1, gap=0.05):
        self.tag, self.block, self.bright = tag, block, bright
        self.x0, self.x1, self.y0, self.y1, self.z0, self.z1 = x0, x1, y0, y1, z0, z1
        self.layers, self.gap = layers, gap

    def _parts(self, h, k=0):
        """(tag suffix, x, y, z, sx, sy, sz, lift) for a column of height h, layer k (each layer `gap` further in)"""
        t = THIN
        d = k * self.gap
        x0, x1, z0, z1 = self.x0 + d, self.x1 - d, self.z0 + d, self.z1 - d
        xl, zl = x1 - x0, z1 - z0
        return [(f"w{k}", x0, self.y0, z0, t, h, zl, 0.0),
                (f"e{k}", x1 - t, self.y0, z0, t, h, zl, 0.0),
                (f"n{k}", x0, self.y0, z0, xl, h, t, 0.0),
                (f"s{k}", x0, self.y0, z1 - t, xl, h, t, 0.0),
                (f"u{k}", x0, self.y0, z0, xl, t, zl, h - t)]

    def spawn(self, h0=0.06):
        return [slab([self.tag, f"{self.tag}_{suf}"], self.block, x, y, z, sx, sy, sz, self.bright, ty=lift)
                for k in range(self.layers) for suf, x, y, z, sx, sy, sz, lift in self._parts(h0, k)]

    def rise_to(self, h, ticks):
        """data merge commands that take the level to height h over `ticks` ticks (linear: one smooth rise)."""
        return [f"execute as @e[tag={self.tag}_{suf},limit=1] run data merge entity @s {{start_interpolation:0,"
                f"interpolation_duration:{int(ticks)},{_tf(sx, sy, sz, 0.0, lift, 0.0)}}}"
                for k in range(self.layers) for suf, x, y, z, sx, sy, sz, lift in self._parts(h, k)]

    @property
    def full_height(self):
        return self.y1 - self.y0
