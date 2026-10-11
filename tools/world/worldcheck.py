"""Compare a world on disk (after `save-all flush`, or with the server stopped) with the canvases it was built from.

    python worldcheck.py D:\\angel-attack\\server\\angel-world            all sets from layout.py (needs the set modules)
    python worldcheck.py WORLD --demo                                 only the built-in demo set

Reads the overworld's region files (region/r.X.Z.mca, deflate or no compression) and compares every cell of each set's box:
what the canvas says (air where nothing was drawn) with what the chunk holds. A block matches if its name is the same and
every property the author gave is the same (properties the game fills in or changes itself, such as the connections of a
fence, are not compared). Chunks and sections that were never saved are air.
"""
import os
import struct
import sys
import zlib

import numpy as np

import compile as comp
import mcdata
import nbt

_DEF = {}


def DEFAULTS():
    if not _DEF:
        _DEF.update(mcdata.block_defaults())
    return _DEF


AIRS = {"minecraft:air", "minecraft:cave_air", "minecraft:void_air"}


def read_chunk(region_path_cache, world_dir, cx, cz):
    """The parsed chunk at chunk coordinates (cx, cz), or None if it was never saved."""
    rx, rz = cx >> 5, cz >> 5
    path = os.path.join(world_dir, "dimensions", "minecraft", "overworld", "region", f"r.{rx}.{rz}.mca")   # 26.x layout\n    if not os.path.isdir(os.path.dirname(path)):\n        path = os.path.join(world_dir, "region", f"r.{rx}.{rz}.mca")                                      # older layout
    if path not in region_path_cache:
        region_path_cache[path] = open(path, "rb").read() if os.path.isfile(path) else None
    data = region_path_cache[path]
    if data is None:
        return None
    entry = struct.unpack(">I", data[4 * ((cx & 31) + (cz & 31) * 32):][:4])[0]
    if entry == 0:
        return None
    offset, count = entry >> 8, entry & 0xFF
    length, comp_type = struct.unpack(">IB", data[offset * 4096:offset * 4096 + 5])
    body = data[offset * 4096 + 5:offset * 4096 + 4 + length]
    if comp_type == 2:
        body = zlib.decompress(body)
    elif comp_type == 1:
        import gzip
        body = gzip.decompress(body)
    elif comp_type != 3:
        raise ValueError(f"region file uses compression type {comp_type} (set region-file-compression=deflate)")
    return nbt.loads(body)


def section_states(sec):
    """(palette, indices[4096]) of a chunk section; index order is y, z, x."""
    bs = sec["block_states"]
    # 26.x: a block with only default properties is written as a plain string (which comes back as {"": name}, because\n    # lists may hold mixed types now and non-compound items are wrapped); one with properties as {id, properties}
    palette = [mcdata.parse_block(e) if isinstance(e, str) else (e.get("id") or e.get("") or e.get("Name"), dict(e.get("properties", e.get("Properties", {})))) for e in bs["palette"]]
    if len(palette) == 1 or "data" not in bs:
        return palette, np.zeros(4096, dtype=np.int64)
    bits = max(4, (len(palette) - 1).bit_length())
    per = 64 // bits
    longs = np.array(bs["data"], dtype=np.int64).astype(np.uint64)
    i = np.arange(4096)
    return palette, ((longs[i // per] >> ((i % per) * bits).astype(np.uint64)) & np.uint64((1 << bits) - 1)).astype(np.int64)


def check_world(world_dir, worlds, limit=8):
    """Compare each World with the region files. Returns a list of problem strings (empty when everything matches)."""
    problems = []
    cache = {}
    for w in worlds:
        names, lut = comp.canon_table(w)
        exp = lut[w.a].astype(np.int64)                               # compact ids
        parsed = [mcdata.parse_block(n) if n else None for n in names]
        skip = np.zeros(w.size, dtype=bool)                              # cells the set own commands change
        for c in w.commands:
            p = c.split()
            if len(p) > 4 and p[0] == "setblock":
                lx, ly, lz = (int(p[i]) - w.origin[i - 1] for i in (1, 2, 3))
                if w.inside(lx, ly, lz):
                    skip[lx, ly, lz] = True
        exp = np.where(skip, -1, exp)
        x0, y0, z0 = w.origin
        sx, sy, sz = w.size
        bad_total, shown, cells = 0, 0, 0
        kinds = {}                                                       # (expected, found) -> cells
        for cx in range(x0 >> 4, ((x0 + sx - 1) >> 4) + 1):
            for cz in range(z0 >> 4, ((z0 + sz - 1) >> 4) + 1):
                chunk = read_chunk(cache, world_dir, cx, cz)
                secs = {int(s["Y"]): s for s in chunk["sections"]} if chunk else {}
                # the window of this chunk inside the set, in canvas coordinates
                lx0, lx1 = max(x0, cx * 16) - x0, min(x0 + sx, cx * 16 + 16) - x0
                lz0, lz1 = max(z0, cz * 16) - z0, min(z0 + sz, cz * 16 + 16) - z0
                for sy_ in range((y0 >> 4), ((y0 + sy - 1) >> 4) + 1):
                    ly0, ly1 = max(y0, sy_ * 16) - y0, min(y0 + sy, sy_ * 16 + 16) - y0
                    sec = secs.get(sy_)
                    if sec is not None:
                        palette, idx = section_states(sec)
                        idx = idx.reshape(16, 16, 16)                    # y, z, x
                    else:
                        palette, idx = [("minecraft:air", {})], np.zeros((16, 16, 16), dtype=np.int64)
                    # actual cells of the window, as [x, y, z] of palette indices
                    gx0, gy0, gz0 = x0 + lx0 - cx * 16, y0 + ly0 - sy_ * 16, z0 + lz0 - cz * 16
                    act = idx[gy0:gy0 + (ly1 - ly0), gz0:gz0 + (lz1 - lz0), gx0:gx0 + (lx1 - lx0)].transpose(2, 0, 1)
                    want = exp[lx0:lx1, ly0:ly1, lz0:lz1]
                    cells += want.size
                    pairs = want * 100000 + act
                    for pair in np.unique(pairs):
                        e, a = divmod(int(pair), 100000)
                        ok = e == -1 or _match(parsed[e], palette[a])
                        if ok:
                            continue
                        where = np.argwhere(pairs == pair)
                        bad_total += len(where)
                        key = ((names[e] or "air").split("[")[0], palette[a][0])
                        kinds[key] = kinds.get(key, 0) + len(where)
                        if shown < limit:
                            lx, ly, lz = where[0]
                            problems.append(f"{w.name}: local ({lx0 + lx}, {ly0 + ly}, {lz0 + lz}) expected {names[e] or 'air (untouched)'}, "
                                            f"the world has {palette[a][0]}{_props(palette[a][1])} ({len(where)} cells like this in this section)")
                            shown += 1
        if bad_total:
            problems.append(f"{w.name}: {bad_total:,} of {cells:,} cells differ; by kind: "
                            + ", ".join(f"{e} -> {a} x{n:,}" for (e, a), n in sorted(kinds.items(), key=lambda kv: -kv[1])[:8]))
    return problems, cells


def _props(p):
    return "[" + ",".join(f"{k}={v}" for k, v in sorted(p.items())) + "]" if p else ""


def _match(expected, actual):
    """expected: (name, props) or None for untouched/air; actual: (name, props) from the chunk."""
    aname, aprops = actual
    aprops = {**DEFAULTS().get(aname, {}), **aprops}
    if expected is None or expected[0] == "minecraft:air":
        return aname in AIRS
    ename, eprops = expected
    return aname == ename and all(aprops.get(k) == v for k, v in eprops.items())


if __name__ == "__main__":
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import demo
    import voxel
    world_dir = sys.argv[1]
    ws = []
    if "--demo" in sys.argv:
        w = voxel.World(demo.NAME, demo.ORIGIN, demo.SIZE)
        demo.build(w)
        ws.append(w)
    else:
        import build
        ws, errs = build.make_sets(None, False)
        if errs:
            sys.exit("\n".join(errs))
    probs, n = check_world(world_dir, ws)
    print("\n".join(probs) if probs else f"all {n:,} cells match")
    sys.exit(1 if probs else 0)
