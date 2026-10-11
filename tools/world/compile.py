"""Turn a finished World into datapack files that place it.

Two ways to place a block canvas are built here, and `template` is the default:

  template  The canvas is cut into 48x48x48 tiles (the largest a structure file is meant to hold). Each tile that
            has anything in it becomes a structure file (gzip NBT, DataVersion of the game) cropped to the box that
            holds its blocks, and one `place template` command puts it back. Cells nobody touched (0) are left out
            of the file, so they never overwrite anything. Block states are exact, and the game itself re-connects
            fences, panes, walls and stairs and updates edges between tiles.
  fill      The same tiles, but each is cut into boxes of one block (greedy meshing) and placed with `fill` and
            `setblock`. Much more text, much slower on the server; kept as a fallback and for the comparison.

Air the author set on purpose (1) is, by default, not written (`air="drop"`): the world is void, so placing air over it
changes nothing, and in a real set most of the volume is air. After a set is changed, run the generated
`clear_<set>` (or `rebuild_<set>`) first so that old blocks do not survive. `air="keep"` writes every air cell.

Placement is a chain of small functions run a tick apart, so the server never stalls: for each group of tiles
(a 2x2 block of tile columns) it forceloads the chunks, waits until they are loaded, then places the tiles a few at a
time. The set's own commands run at the end, with everything still loaded, and then the forceload is released.
"""
import math
import re

import numpy as np

import mcdata
import nbt

NS = "angel"
TILE = 48                 # the largest structure a structure block can save and load
STAGE_TILES = 2           # tile columns per side that are forceloaded together
MARGIN = 16               # blocks of extra forceload round a stage: placement updates the blocks next to the edge
WAIT_TICKS = 2            # how often the chain looks again at chunks that have not loaded yet

# Cost model, in milliseconds of server time. Measured on a real 26.3 server (warm JVM, nobody online): a 48-block cube of
# one block costs 1.1-1.3 us per block whichever way it is placed; mixed detailed content 3-12 us per block by template
# (it is the state changes the neighbours cause that cost, not the block count); a setblock 2.2 us, a fill 1 us + 1.2 us per
# block; loading a stage of 81 chunks 100-160 ms. These are the middle of those ranges, so the estimates are only a guide.
TEMPLATE_MS_PER_BLOCK = 0.003       # place template, per block record
TEMPLATE_MS_FIXED = 4.0             # reading the file, per command
FILL_MS_PER_BLOCK = 0.0012          # fill, per block of volume
FILL_MS_FIXED = 0.004               # per fill/setblock command
STAGE_MS = 150.0                    # forceloading and generating one stage of chunks
STEP_MS = 120.0                     # target work per tick (a tick is 50 ms; some overrun is fine with nobody playing)
MAX_COMMANDS_PER_STEP = 2000        # keeps single function files small


# ---------------------------------------------------------------- block names

def canon(block):
    """'minecraft:oak_stairs[half=top,facing=east]' -> properties sorted, so equal states compare equal."""
    name, props = mcdata.parse_block(block)
    if not props:
        return name
    return name + "[" + ",".join(f"{k}={props[k]}" for k in sorted(props)) + "]"


def canon_table(w):
    """(names, lut): canonical block names by compact id (0 untouched, 1 air), and a lookup array from the
    canvas's palette ids to those ids."""
    names, ix = [None, "minecraft:air"], {"minecraft:air": 1}
    lut = np.zeros(max(2, len(w.palette)), dtype=np.uint16)
    lut[1] = 1
    for gid in range(2, len(w.palette)):
        c = canon(w.palette[gid])
        if c not in ix:
            ix[c] = len(names)
            names.append(c)
        lut[gid] = ix[c]
    return names, lut


# ---------------------------------------------------------------- structure files

_STATE = np.frombuffer(b"state", dtype=np.uint8)
_POS = np.frombuffer(b"pos", dtype=np.uint8)


def _be32(a):
    return np.ascontiguousarray(a.astype(">i4")).view(np.uint8).reshape(len(a), 4)


def _palette_entry(canon_name):
    # 26.x writes a block state as {id, properties}; the older {Name, Properties} is read as an empty block, silently
    name, props = mcdata.parse_block(canon_name)
    e = {"id": name}
    if props:
        e["properties"] = dict(props)
    return e


def encode_structure(ids, xs, ys, zs, names, size, data_version):
    """Raw (uncompressed) NBT of a structure: `ids` are compact block ids, xs/ys/zs positions inside `size`."""
    uniq, inv = np.unique(ids, return_inverse=True)
    n = len(ids)
    rec = np.empty((n, 36), dtype=np.uint8)       # one block = { state: int, pos: [int, int, int] }
    rec[:, 0] = nbt.INT
    rec[:, 1:3] = (0, 5)
    rec[:, 3:8] = _STATE
    rec[:, 8:12] = _be32(inv)
    rec[:, 12] = nbt.LIST
    rec[:, 13:15] = (0, 3)
    rec[:, 15:18] = _POS
    rec[:, 18] = nbt.INT
    rec[:, 19:23] = (0, 0, 0, 3)
    rec[:, 23:27] = _be32(xs)
    rec[:, 27:31] = _be32(ys)
    rec[:, 31:35] = _be32(zs)
    rec[:, 35] = nbt.END
    head = b"".join([
        bytes([nbt.COMPOUND, 0, 0]),
        nbt.named("DataVersion", nbt.Int(data_version)),
        nbt.named("size", nbt.List(nbt.INT, [nbt.Int(v) for v in size])),
        nbt.named("palette", nbt.List(nbt.COMPOUND, [_palette_entry(names[u]) for u in uniq.tolist()])),
        bytes([nbt.LIST]), b"\x00\x06blocks", bytes([nbt.COMPOUND]), n.to_bytes(4, "big"),     # the blocks list: n compounds follow
    ])
    tail = nbt.named("entities", nbt.List(nbt.COMPOUND, [])) + b"\x00"
    return head + rec.tobytes() + tail


def structure_to_blocks(raw_or_root, names_unused=None):
    """Read a structure (parsed root compound) back as [(x, y, z, 'canonical block')]."""
    root = raw_or_root
    palette = []
    for e in root["palette"]:
        props = e.get("properties")
        palette.append(e["id"] + ("[" + ",".join(f"{k}={props[k]}" for k in sorted(props)) + "]" if props else ""))
    out = []
    for b in root["blocks"]:
        x, y, z = (int(v) for v in b["pos"])
        out.append((x, y, z, palette[int(b["state"])]))
    return out


# ---------------------------------------------------------------- the fill alternative: greedy boxes

def _rects2d(layer):
    """Merge a 2D array layer[x, z] (0 = nothing) into rectangles (x1, z1, x2, z2, key)."""
    kt = np.ascontiguousarray(layer.T)       # rows are z
    nz, nx = kt.shape
    out, open_ = [], {}
    for z in range(nz + 1):
        cur = set()
        if z < nz:
            row = kt[z]
            d = np.flatnonzero(row[1:] != row[:-1]) + 1
            for a, b in zip([0] + d.tolist(), d.tolist() + [nx]):
                k = int(row[a])
                if k:
                    cur.add((a, b - 1, k))
        for key in list(open_):
            if key not in cur:
                out.append((key[0], open_.pop(key), key[1], z - 1, key[2]))
        for key in cur:
            open_.setdefault(key, z)
    return out


def mesh_boxes(cid, threshold):
    """Cut cid[x, y, z] (cells with id <= threshold are not drawn) into boxes of one block: (x1, y1, z1, x2, y2, z2, id)."""
    sx, sy, sz = cid.shape
    boxes, open_ = [], {}
    for y in range(sy + 1):
        cur = set()
        if y < sy:
            layer = np.where(cid[:, y, :] > threshold, cid[:, y, :], 0)
            if layer.any():
                cur = {(x1, z1, x2, z2, k) for x1, z1, x2, z2, k in _rects2d(layer)}
        for key in list(open_):
            if key not in cur:
                x1, z1, x2, z2, k = key
                boxes.append((x1, open_.pop(key), z1, x2, y - 1, z2, k))
        for key in cur:
            open_.setdefault(key, y)
    return boxes


def paint_boxes(boxes, shape):
    """Replay boxes onto an empty array (used to check the mesher)."""
    a = np.zeros(shape, dtype=np.uint32)
    for x1, y1, z1, x2, y2, z2, k in boxes:
        a[x1:x2 + 1, y1:y2 + 1, z1:z2 + 1] = k
    return a


# ---------------------------------------------------------------- blocks that need their neighbours

# `place template` puts down a tile's blocks and then asks each one to check its surroundings. A torch, lantern, door,
# plant, rail, pane... whose support stands in a tile that is placed later is therefore removed as unsupported, and
# nothing puts it back. So the cells on a tile edge that are not plain cubes and have something across the edge are
# placed again with setblock/fill once every tile is down. Cubes cannot be lost this way, so they are not repeated.
_CUBE = re.compile(
    r"^(stone|cobblestone|mossy_cobblestone|dirt|coarse_dirt|rooted_dirt|grass_block|podzol|mycelium|sand|red_sand|gravel|clay|"
    r"bedrock|obsidian|crying_obsidian|netherrack|end_stone|glowstone|sea_lantern|bricks|quartz_block|bone_block|"
    r"water|lava|light|barrier|structure_void|andesite|diorite|granite|calcite|tuff|basalt|smooth_basalt|blackstone|deepslate|"
    r"terracotta|glass|tinted_glass|ice|packed_ice|blue_ice|snow_block|magma_block|soul_sand|soul_soil|"
    r".+_(planks|log|wood|concrete|wool|terracotta|bricks|tiles|block|ore|stone|andesite|diorite|granite|basalt|blackstone|"
    r"deepslate|sandstone|glass|nylium|quartz|copper|lamp|brick|leaves))$")
_SHAPED = re.compile(r"(stairs|slab|wall|button|pressure_plate|fence|gate|door|trapdoor|pane|bars|carpet|torch|lantern|sign|banner|"
                     r"bed|head|skull|rail|ladder|vine|wire|chain|candle|fan|coral|sapling|flower|mushroom)")


def needs_neighbours(canon_name):
    name = canon_name.split("[", 1)[0].split(":", 1)[1]
    return not (_CUBE.match(name) and not _SHAPED.search(name))


def border_fixups(cid, dependent, tile=TILE):
    """cid: canvas of compact ids; dependent: bool per id. Returns an array like cid holding the id of every cell to place
    again (0 elsewhere): dependent blocks on a tile edge with a block on the other side of that edge."""
    solid = cid > 1
    cells = dependent[cid] & solid
    fx = np.zeros_like(cid)
    for axis in range(3):
        n = cid.shape[axis]
        for c in range(tile, n, tile):                 # the edge lies between layer c - 1 and layer c
            lo = [slice(None)] * 3
            hi = [slice(None)] * 3
            lo[axis], hi[axis] = c - 1, c
            lo, hi = tuple(lo), tuple(hi)
            for a, b in ((lo, hi), (hi, lo)):
                m = cells[a] & solid[b]
                fx[a] = np.where(m, cid[a], fx[a])
    return fx


# ---------------------------------------------------------------- tiles and the compiled set

class Tile:
    """A piece of the canvas: ix/iy/iz its place in the tile grid, `lo`/`hi` its absolute world corners (inclusive)
    after cropping to what is in it, `cmds` the commands that place it, `blocks` how many blocks it holds."""
    __slots__ = ("ix", "iy", "iz", "lo", "hi", "cmds", "blocks", "ms", "file", "data", "boxes")

    def __init__(self, ix, iy, iz):
        self.ix, self.iy, self.iz = ix, iy, iz
        self.cmds, self.blocks, self.ms, self.file, self.data, self.boxes = [], 0, 0.0, None, None, None


class CompiledSet:
    def __init__(self, name, origin, size, method, air):
        self.name, self.origin, self.size, self.method, self.air = name, tuple(origin), tuple(size), method, air
        self.tiles = []             # tiles with something in them
        self.tile_grid = (0, 0, 0)
        self.functions = {}         # "world/<set>/p0" -> [lines]
        self.structures = {}        # "<set>/t0_0_0" -> gzip bytes
        self.names = []
        self.post = []
        self.fix_cmds = []          # blocks on tile edges that are placed again once every tile is down
        self.rects = []
        self.steps = 0
        self.ms_place = 0.0
        self.ticks_place = 0
        self.ticks_clear = 0

    @property
    def blocks(self):
        return sum(t.blocks for t in self.tiles)

    @property
    def structure_bytes(self):
        return sum(len(v) for v in self.structures.values())

    def abs_box(self):
        o, s = self.origin, self.size
        return o[0], o[1], o[2], o[0] + s[0] - 1, o[1] + s[1] - 1, o[2] + s[2] - 1


def compile_set(w, method="template", air="drop", level=6, fixups=True):
    """Build every tile of a finished World. Returns a CompiledSet with structures/functions filled in."""
    if method not in ("template", "fill") or air not in ("drop", "keep"):
        raise ValueError("method is 'template' or 'fill'; air is 'drop' or 'keep'")
    names, lut = canon_table(w)
    threshold = 0 if air == "keep" else 1
    dv = mcdata.data_version()
    cs = CompiledSet(w.name, w.origin, w.size, method, air)
    cs.names = names
    sx, sy, sz = w.size
    cs.tile_grid = (math.ceil(sx / TILE), math.ceil(sy / TILE), math.ceil(sz / TILE))
    for ix in range(cs.tile_grid[0]):
        for iy in range(cs.tile_grid[1]):
            for iz in range(cs.tile_grid[2]):
                x0, y0, z0 = ix * TILE, iy * TILE, iz * TILE
                cid = lut[w.a[x0:x0 + TILE, y0:y0 + TILE, z0:z0 + TILE]]
                mask = cid > threshold
                if not mask.any():
                    continue
                bb = []
                for ax, other in ((0, (1, 2)), (1, (0, 2)), (2, (0, 1))):
                    nz = np.flatnonzero(mask.any(axis=other))
                    bb.append((int(nz[0]), int(nz[-1])))
                (a0, a1), (b0, b1), (c0, c1) = bb
                cid = cid[a0:a1 + 1, b0:b1 + 1, c0:c1 + 1]
                t = Tile(ix, iy, iz)
                t.lo = (w.origin[0] + x0 + a0, w.origin[1] + y0 + b0, w.origin[2] + z0 + c0)
                t.hi = (t.lo[0] + a1 - a0, t.lo[1] + b1 - b0, t.lo[2] + c1 - c0)
                if method == "template":
                    tr = np.ascontiguousarray(cid.transpose(1, 2, 0))          # y, z, x: runs along x are the densest
                    yy, zz, xx = np.nonzero(tr > threshold)
                    ids = tr[yy, zz, xx]
                    t.blocks = len(ids)
                    size = (a1 - a0 + 1, b1 - b0 + 1, c1 - c0 + 1)
                    raw = encode_structure(ids, xx, yy, zz, names, size, dv)
                    t.file = f"{w.name}/t{ix}_{iy}_{iz}"
                    cs.structures[t.file] = nbt.compress(raw, level)
                    t.cmds = [f"place template {NS}:{t.file} {t.lo[0]} {t.lo[1]} {t.lo[2]}"]
                    t.ms = TEMPLATE_MS_FIXED + TEMPLATE_MS_PER_BLOCK * t.blocks
                else:
                    boxes = mesh_boxes(cid, threshold)
                    t.boxes = boxes
                    cmds, vol = [], 0
                    for bx1, by1, bz1, bx2, by2, bz2, k in boxes:
                        p1 = (t.lo[0] + bx1, t.lo[1] + by1, t.lo[2] + bz1)
                        p2 = (t.lo[0] + bx2, t.lo[1] + by2, t.lo[2] + bz2)
                        v = (bx2 - bx1 + 1) * (by2 - by1 + 1) * (bz2 - bz1 + 1)
                        vol += v
                        if v == 1:
                            cmds.append(f"setblock {p1[0]} {p1[1]} {p1[2]} {names[k]}")
                        else:
                            cmds.append(f"fill {p1[0]} {p1[1]} {p1[2]} {p2[0]} {p2[1]} {p2[2]} {names[k]}")
                    t.cmds, t.blocks = cmds, vol
                    t.ms = FILL_MS_FIXED * len(cmds) + FILL_MS_PER_BLOCK * vol
                cs.tiles.append(t)
    full = lut[w.a]
    dependent = np.array([False, False] + [needs_neighbours(n) for n in names[2:]])
    for bx1, by1, bz1, bx2, by2, bz2, k in (mesh_boxes(border_fixups(full, dependent), 0) if fixups else []):
        p1, p2 = w.abs(bx1, by1, bz1), w.abs(bx2, by2, bz2)
        if p1 == p2:
            cs.fix_cmds.append(f"setblock {p1[0]} {p1[1]} {p1[2]} {names[k]}")
        else:
            cs.fix_cmds.append(f"fill {p1[0]} {p1[1]} {p1[2]} {p2[0]} {p2[1]} {p2[2]} {names[k]}")
    return cs


# ---------------------------------------------------------------- the chain of functions

def _stage_rect(items):
    x1 = min(i["lo"][0] for i in items) - MARGIN
    z1 = min(i["lo"][2] for i in items) - MARGIN
    x2 = max(i["hi"][0] for i in items) + MARGIN
    z2 = max(i["hi"][2] for i in items) + MARGIN
    chunks = ((x2 >> 4) - (x1 >> 4) + 1) * ((z2 >> 4) - (z1 >> 4) + 1)
    if chunks > 256:
        raise ValueError(f"a stage of {chunks} chunks is more than forceload takes at once (256)")
    return x1, z1, x2, z2


def make_chain(set_name, prefix, items, y, before=(), fix=(), after=(), final_tail=()):
    """Functions that do `items` stage by stage, then the `fix` commands, then `after`, then release the forceload.
    items: dicts with ix, iy, iz, lo, hi (absolute), ms, cmds.
    Returns ({'world/<set>/<prefix><n>': lines}, rects, steps, ticks, ms). Step 0 is the entry."""
    stages = {}
    for it in items:
        stages.setdefault((it["ix"] // STAGE_TILES, it["iz"] // STAGE_TILES), []).append(it)
    steps, rects, ticks, ms = [], [], 0, 0.0
    ms += STAGE_MS * len(stages)
    for key in sorted(stages):
        grp = sorted(stages[key], key=lambda i: (i["iy"], i["ix"], i["iz"]))
        x1, z1, x2, z2 = _stage_rect(grp)
        rects.append((x1, z1, x2, z2))
        steps.append(("run", ([f"forceload add {x1} {z1} {x2} {z2}"], 1.0)))
        steps.append(("wait", (x1, z1, x2, z2)))
        cur, cur_ms = [], 0.0
        for it in grp:
            if cur and (cur_ms + it["ms"] > STEP_MS or len(cur) + len(it["cmds"]) > MAX_COMMANDS_PER_STEP):
                steps.append(("run", (cur, cur_ms)))
                cur, cur_ms = [], 0.0
            cur = cur + it["cmds"]
            cur_ms += it["ms"]
        if cur:
            steps.append(("run", (cur, cur_ms)))
    fix = list(fix)
    for i in range(0, len(fix), 300):                    # edge blocks placed again, 300 commands to a tick at most
        part = fix[i:i + 300]
        steps.append(("run", (part, max(1.0, FILL_MS_FIXED * len(part)))))
    fin = list(after) + [f"forceload remove {r[0]} {r[1]} {r[2]} {r[3]}" for r in rects] + list(final_tail)
    steps.append(("run", (fin, 1.0)))
    steps[0][1][0][:0] = list(before)

    def ref(n):
        return f"{NS}:world/{set_name}/{prefix}{n}"

    fns = {}
    for n, (kind, body) in enumerate(steps):
        last = n == len(steps) - 1
        if kind == "run":
            lines, step_ms = body
            lines = list(lines)
            if not last:
                lines.append(f"schedule function {ref(n + 1)} 1t")
            ticks += max(1, math.ceil(step_ms / 50.0)) if not last else 1
            ms += step_ms
        else:
            x1, z1, x2, z2 = body
            cx, cz = (x1 + x2) // 2, (z1 + z2) // 2
            probe = " ".join(f"if loaded {px} {y} {pz}" for px, pz in ((x1, z1), (x2, z1), (x1, z2), (x2, z2), (cx, cz)))
            lines = ["scoreboard players set #ok angel_world 0",
                     f"execute {probe} run scoreboard players set #ok angel_world 1",
                     f"execute if score #ok angel_world matches 1 run function {ref(n + 1)}",
                     f"execute unless score #ok angel_world matches 1 run schedule function {ref(n)} {WAIT_TICKS}t"]
            ticks += 3
        fns[f"world/{set_name}/{prefix}{n}"] = lines
    return fns, rects, len(steps), ticks, ms


def wrap(command, fallback_dimension="minecraft:overworld"):
    """A set's own command, made to run in the overworld whatever context the chain was started in."""
    c = command.strip()
    if c.startswith("/"):
        c = c[1:]
    return f"execute in {fallback_dimension} run {c}"


def finish_sets(compiled, anchors):
    """Add the function chains to every CompiledSet and return the shared functions as {path: lines}.
    `compiled` is a list in placement order; the sets' own post-placement commands must already be in cs.post."""
    shared = {}
    order = [cs.name for cs in compiled]
    for k, cs in enumerate(compiled):
        items = [{"ix": t.ix, "iy": t.iy, "iz": t.iz, "lo": t.lo, "hi": t.hi, "ms": t.ms, "cmds": t.cmds} for t in cs.tiles]
        nxt = order[k + 1] if k + 1 < len(order) else None
        if nxt:
            go_on = [f"execute if score #all angel_world matches 1 run function {NS}:world/{nxt}/p0"]
        else:
            go_on = ["scoreboard players set #all angel_world 0", "say [angel] every set is placed"]
        fns, rects, steps, ticks, ms = make_chain(
            cs.name, "p", items, cs.origin[1],
            before=["scoreboard objectives add angel_world dummy", "gamerule minecraft:max_block_modifications 10000000"],
            fix=cs.fix_cmds, after=[wrap(c) for c in cs.post],
            final_tail=[f"say [angel] placed {cs.name}: {len(cs.tiles)} tiles, {cs.blocks} blocks"] + go_on)
        cs.functions.update(fns)
        cs.rects, cs.steps, cs.ticks_place, cs.ms_place = rects, steps, ticks, ms

        # clear: fill the whole box with air (every tile of the grid, not only those with something in them)
        x0, y0, z0, x1, y1, z1 = cs.abs_box()
        clear_items = []
        for ix in range(cs.tile_grid[0]):
            for iy in range(cs.tile_grid[1]):
                for iz in range(cs.tile_grid[2]):
                    lo = (x0 + ix * TILE, y0 + iy * TILE, z0 + iz * TILE)
                    hi = (min(x1, lo[0] + TILE - 1), min(y1, lo[1] + TILE - 1), min(z1, lo[2] + TILE - 1))
                    vol = (hi[0] - lo[0] + 1) * (hi[1] - lo[1] + 1) * (hi[2] - lo[2] + 1)
                    clear_items.append({"ix": ix, "iy": iy, "iz": iz, "lo": lo, "hi": hi, "ms": FILL_MS_PER_BLOCK * vol + FILL_MS_FIXED,
                                        "cmds": [f"fill {lo[0]} {lo[1]} {lo[2]} {hi[0]} {hi[1]} {hi[2]} minecraft:air"]})
        cfns, _, _, cticks, _ = make_chain(
            cs.name, "c", clear_items, cs.origin[1],
            before=["scoreboard objectives add angel_world dummy", "gamerule minecraft:max_block_modifications 10000000"],
            final_tail=[f"say [angel] cleared {cs.name}",
                        "scoreboard players operation #go angel_world = #rebuild angel_world",
                        "scoreboard players set #rebuild angel_world 0",
                        f"execute if score #go angel_world matches 1 run function {NS}:world/{cs.name}/p0"])
        cs.functions.update(cfns)
        cs.ticks_clear = cticks

        shared[f"world/place_{cs.name}"] = ["scoreboard objectives add angel_world dummy", "scoreboard players set #all angel_world 0",
                                           f"execute in minecraft:overworld run function {NS}:world/{cs.name}/p0"]
        shared[f"world/clear_{cs.name}"] = ["scoreboard objectives add angel_world dummy", "scoreboard players set #rebuild angel_world 0",
                                            f"execute in minecraft:overworld run function {NS}:world/{cs.name}/c0"]
        shared[f"world/rebuild_{cs.name}"] = ["scoreboard objectives add angel_world dummy", "scoreboard players set #all angel_world 0",
                                              "scoreboard players set #rebuild angel_world 1",
                                              f"execute in minecraft:overworld run function {NS}:world/{cs.name}/c0"]
    return shared
