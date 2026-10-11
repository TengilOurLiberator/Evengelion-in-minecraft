"""Make synthetic sets as big as the real ones and time/measure the compiler on them (not part of the build).

    python bench.py city      a 320 x 160 x 320 street grid of buildings with windows, stairs, lamps
    python bench.py solid     a 320 x 144 x 320 block of rock with a cavern carved out (the densest case)
    options: --method fill|template  --air drop|keep  --write DIR   (write the generated pack to DIR)
"""
import argparse
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import compile as comp      # noqa: E402
import voxel                # noqa: E402


def city(w, rng):
    sx, sy, sz = w.size
    w.fill(0, 0, 0, sx - 1, 3, sz - 1, "stone")
    w.fill(0, 4, 0, sx - 1, 4, sz - 1, "grass_block")
    # streets every 64 blocks
    for k in range(0, sx, 64):
        w.fill(k, 4, 0, k + 7, 4, sz - 1, "gray_concrete")
        w.fill(0, 4, k, sx - 1, 4, k + 7, "gray_concrete")
    for bx in range(10, sx - 50, 64):
        for bz in range(10, sz - 50, 64):
            for _ in range(3):
                x, z = bx + int(rng.integers(0, 24)), bz + int(rng.integers(0, 24))
                wx, wz, h = int(rng.integers(14, 30)), int(rng.integers(14, 30)), int(rng.integers(20, 130))
                w.fill(x, 5, z, x + wx, 5 + h, z + wz, "light_gray_concrete")
                w.fill(x + 1, 6, z + 1, x + wx - 1, 4 + h, z + wz - 1, "air")
                for y in range(8, 4 + h, 4):
                    w.fill(x, y, z, x + wx, y + 1, z, "glass")
                    w.fill(x, y, z + wz, x + wx, y + 1, z + wz, "glass")
                    w.fill(x, y, z, x, y + 1, z + wz, "glass_pane")
                    w.fill(x + wx, y, z, x + wx, y + 1, z + wz, "glass_pane")
                    w.fill(x + 1, y - 1, z + 1, x + wx - 1, y - 1, z + wz - 1, "smooth_stone")
                for i in range(wx + 3):
                    w.set(x - 1 + i, 5 + h + 1, z - 1, "stone_brick_stairs[facing=south,half=bottom]")
                w.set(x + 2, 6, z + 2, "lantern[hanging=false]")
    for x in range(3, sx, 16):
        for z in range(3, sz, 16):
            if w.a[x, 5, z] == 0:
                w.fill(x, 5, z, x, 8, z, "oak_fence")
                w.set(x, 9, z, "lantern[hanging=false]")


def solid(w, rng):
    sx, sy, sz = w.size
    w.fill(0, 0, 0, sx - 1, sy - 1, sz - 1, "stone")
    for _ in range(300):                               # ore and other blocks inside the rock
        x, y, z = (int(rng.integers(0, s)) for s in w.size)
        w.fill(x, y, z, x + 3, y + 3, z + 3, str(rng.choice(["deepslate", "andesite", "iron_ore", "tuff", "granite"])))
    # a big cavern, and tunnels
    xs, ys, zs = np.ogrid[:sx, :sy, :sz]
    cav = ((xs - sx / 2) / 130.0) ** 2 + ((ys - sy / 2) / 50.0) ** 2 + ((zs - sz / 2) / 130.0) ** 2 < 1
    w.a[cav] = 1
    for _ in range(30):
        x, y, z = (int(rng.integers(0, s - 10)) for s in w.size)
        w.fill(x, y, z, x + int(rng.integers(5, 120)), y + 5, z + 5, "air")


MAKERS = {"city": (city, (320, 160, 320)), "solid": (solid, (320, 144, 320))}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("kind", choices=MAKERS)
    ap.add_argument("--method", default="template")
    ap.add_argument("--air", default="drop")
    ap.add_argument("--write")
    a = ap.parse_args()
    maker, size = MAKERS[a.kind]
    w = voxel.World("bench" + a.kind, (5000, 0, 5000), size)
    t = time.time()
    maker(w, np.random.default_rng(1))
    solid_cells = int((w.a > 1).sum())
    print(f"drawn in {time.time() - t:.1f}s: {solid_cells:,} blocks of {w.a.size:,} cells ({100 * solid_cells / w.a.size:.0f}%), "
          f"{int((w.a == 1).sum()):,} air, {len(w.palette)} palette entries")
    t = time.time()
    cs = comp.compile_set(w, a.method, a.air)
    dt = time.time() - t
    print(f"compiled ({a.method}, air {a.air}) in {dt:.1f}s: {len(cs.tiles)} of {np.prod(cs.tile_grid)} tiles, {cs.blocks:,} block records, "
          f"{cs.structure_bytes / 1e6:.1f} MB gzip, {len(cs.fix_cmds)} edge fixes")
    cmds = sum(len(t.cmds) for t in cs.tiles)
    print(f"  commands for the tiles: {cmds:,}; estimated server work {sum(t.ms for t in cs.tiles) / 1000:.1f}s")
    raw = None
    if a.write:
        os.makedirs(a.write, exist_ok=True)
        import gzip
        t = next(t for t in cs.tiles if t.blocks == max(x.blocks for x in cs.tiles)) if a.method == "template" else None
        if t is not None:
            raw = len(gzip.decompress(cs.structures[t.file]))
            print(f"  fullest tile {t.file}: {t.blocks:,} blocks, {raw / 1e6:.1f} MB raw, {len(cs.structures[t.file]) / 1e6:.2f} MB gzip")
            for name, data in cs.structures.items():
                p = os.path.join(a.write, *name.split("/")) + ".nbt"
                os.makedirs(os.path.dirname(p), exist_ok=True)
                open(p, "wb").write(data)
