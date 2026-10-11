"""Read access to the built voxel worlds (tools/world/sets/*.py build in a second or two): the ground height under a point, what stands in
a box, whether a route is on road with room above it.  Used by the generator to give routes their heights and by the checker to prove
that every frame of every route is on a surface with headroom.  Nothing here writes to tools/world."""
import importlib
import math
import os
import sys

import numpy as np

from core import TOOLS

WORLD_DIR = os.path.join(TOOLS, "world")
for p in (TOOLS, WORLD_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

# block names that do not stop a car or a person (matched on the whole name, never on a fragment: "stairs" contains "air")
PASS_EXACT = {"air", "cave_air", "void_air", "light", "short_grass", "tall_grass", "fern", "large_fern", "vine", "cobweb", "tripwire", "string",
              "lever", "poppy", "dandelion", "cornflower", "azure_bluet", "allium", "lily_of_the_valley", "wildflowers", "leaf_litter",
              "pink_petals", "sweet_berry_bush", "dead_bush", "ladder", "rail", "powered_rail", "detector_rail", "activator_rail", "bush"}
PASS_SUFFIX = ("_carpet", "_sign", "_wall_sign", "_hanging_sign", "_banner", "_wall_banner", "_torch", "_wall_torch", "_button",
               "_pressure_plate", "_sapling", "_tulip", "_orchid", "_flower")


def is_passable(name):
    if name is None:
        return True
    n = name.replace("minecraft:", "")
    base = n.split("[")[0]
    if base in PASS_EXACT or base.endswith(PASS_SUFFIX):
        return True
    if base == "snow" and "layers=1" in n:
        return True
    return False


def top_of(name):
    n = name.replace("minecraft:", "")
    if "_slab" in n and "type=bottom" in n:
        return 0.5
    if "carpet" in n:
        return 0.0625
    return 1.0


class Probe:
    def __init__(self, set_name):
        import voxel
        import layout
        mod = importlib.import_module(f"sets.{set_name}")
        self.set_name = set_name
        self.w = voxel.World(set_name, *layout.SETS[set_name])
        self.built = mod.build(self.w)
        self.o = self.w.origin
        self.pal = self.w.palette
        self.passable = np.array([is_passable(n) for n in self.pal], dtype=bool)
        self.passable[0] = True
        self.passable[1] = True

    # block at ABSOLUTE integer coordinates
    def gid(self, x, y, z):
        lx, ly, lz = int(math.floor(x)) - self.o[0], int(math.floor(y)) - self.o[1], int(math.floor(z)) - self.o[2]
        if not self.w.inside(lx, ly, lz):
            return 0
        return int(self.w.a[lx, ly, lz])

    def name(self, x, y, z):
        return self.pal[self.gid(x, y, z)]

    def solid(self, x, y, z):
        return not self.passable[self.gid(x, y, z)]

    def surface(self, x, z, ref_y, up=1.6, down=8):
        """Height of the standing surface under (x, z): the top of the highest solid cell whose cell above is free, searching from
        ref_y + up downwards.  None if nothing."""
        y0 = int(math.floor(ref_y + up))
        for y in range(y0, y0 - down - 2, -1):
            if self.solid(x, y, z) and not self.solid(x, y + 1, z):
                return y + top_of(self.name(x, y, z))
        return None

    def surface_name(self, x, z, ref_y):
        y0 = int(math.floor(ref_y + 1.6))
        for y in range(y0, y0 - 10, -1):
            if self.solid(x, y, z) and not self.solid(x, y + 1, z):
                return self.name(x, y, z)
        return None

    def box_hits(self, cx, cy, cz, yaw, hw=2.0, hl=3.5, h=2.2, y_from=0.65, step=0.5, pitch=0.0):
        """Solid blocks inside the car-sized box (width 2*hw, length 2*hl, floor tilted by `pitch` degrees, nose down positive) standing on
        y = cy, from y_from above the floor to h.  Returns {name: count} of the cells met by a sample grid."""
        fx, fz = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        lx, lz = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        tp = math.tan(math.radians(pitch))
        hits = {}
        a = -hl
        while a <= hl + 1e-6:
            b = -hw
            base = cy - a * tp
            while b <= hw + 1e-6:
                px, pz = cx + fx * a + lx * b, cz + fz * a + lz * b
                y = base + y_from
                while y <= base + h:
                    if self.solid(px, y, pz):
                        nm = self.name(px, y, pz)
                        if "_slab[type=bottom]" not in nm:           # a low slab is ground, not an obstacle
                            hits[nm] = hits.get(nm, 0) + 1
                    y += 0.5
                b += step
            a += step
        return hits

    def ground_under(self, cx, cz, yaw, hw=1.8, hl=3.0, ref_y=None):
        """The four wheel contact heights of a car at (cx, cz) heading yaw."""
        fx, fz = -math.sin(math.radians(yaw)), math.cos(math.radians(yaw))
        lx, lz = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        out = []
        for a in (-hl, hl):
            for b in (-hw, hw):
                out.append(self.surface(cx + fx * a + lx * b, cz + fz * a + lz * b, ref_y if ref_y is not None else 0))
        return out
