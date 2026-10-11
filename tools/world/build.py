"""Build the Angel Attack world: run every set's builder, check it, and write the datapack that places it.

    python build.py                    build everything (sets with a module in sets\\; a small demo set if there are none)
    python build.py --preview          also write pictures to tools\\world\\preview\\ (top view and two middle slices per set)
    python build.py --sets city,hq     only these sets (the others' files are removed; for quick tries)
    python build.py --demo             add the built-in demo set to the real sets
    python build.py --demo-only        only the demo set (ignores sets\\ entirely; for trying the compiler)
    python build.py --method fill      place with fill commands instead of structure files (slower, much bigger)
    python build.py --air keep         write every air cell too (default: air is not written; see compile.py)
    python build.py --out DIR          write the pack to DIR instead (a test copy)
    python build.py --selftest         compile the demo set into a temporary folder and check everything, writing nothing

Use the Python of the D:\\voice-assistant environment (numpy, pillow).

Writes (all under D:\\angel-attack\\datapack\\angel, and a list of what it wrote in tools\\world\\build_manifest.json
so that a later build can remove what is no longer made):
    data/angel/function/world/   init, place_all, abort, and per set: place_<set>, clear_<set>, rebuild_<set>, enter_<set>,
                                 and the chain <set>/p0.. and <set>/c0.. that those start
    data/angel/structure/<set>/  the tiles
    data/angel/worldgen/biome/void.json, world_clock/day.json, timeline/sky.json, data/minecraft/dimension_type/overworld.json
    pack.mcmeta                  only if there is none
and tools\\world\\anchors.json.
"""
import argparse
import importlib
import json
import os
import shutil
import sys
import tempfile
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
for p in (TOOLS, HERE):                      # set modules may import `voxel` or `world.voxel`, `..voxel` alike
    if p not in sys.path:
        sys.path.insert(0, p)

import compile as comp                      # noqa: E402
import cmdcheck                             # noqa: E402
import demo                                 # noqa: E402
import layout                               # noqa: E402
import mcdata                               # noqa: E402
import verify                               # noqa: E402
import voxel                                # noqa: E402
import worldgen                             # noqa: E402

PACK = os.path.join(ROOT, "datapack", "angel")
SETS_DIR = os.path.join(HERE, "sets")
PREVIEW_DIR = os.path.join(HERE, "preview")
ANCHORS = os.path.join(HERE, "anchors.json")
MANIFEST = os.path.join(HERE, "build_manifest.json")
NS = "angel"
BUILD_MIN_Y, BUILD_MAX_Y = -64, 320          # the overworld dimension type: min_y -64, height 384
FALLING = ("sand", "red_sand", "gravel", "anvil", "dragon_egg", "suspicious_sand", "suspicious_gravel")      # and *_concrete_powder


def say(msg=""):
    print(msg, flush=True)


# ---------------------------------------------------------------- finding and running the sets

def load_builder(name):
    """The build function of sets/<name>.py, or None if there is no such module. Raises if the module is broken."""
    if not os.path.isfile(os.path.join(SETS_DIR, name + ".py")):
        return None
    for modname in (f"world.sets.{name}", f"sets.{name}"):
        try:
            mod = importlib.import_module(modname)
            break
        except ImportError as e:
            # a relative import in the module can fail under one of the two names but work under the other
            if modname == f"sets.{name}":
                raise
            last = e
    if not hasattr(mod, "build"):
        raise AttributeError(f"sets/{name}.py has no build(w)")
    return mod.build


def make_sets(only, add_demo):
    """[(World, how)] for every set to be built. Missing modules are skipped with a warning."""
    sets, errors = [], []
    for name, (origin, size) in layout.SETS.items():
        if only and name not in only:
            continue
        try:
            fn = load_builder(name)
        except Exception as e:
            errors.append(f"set {name}: cannot import sets/{name}.py: {type(e).__name__}: {e}")
            continue
        if fn is None:
            say(f"warning: no module for set '{name}' (sets/{name}.py); skipped")
            continue
        w = voxel.World(name, origin, size)
        t0 = time.time()
        try:
            fn(w)
        except Exception as e:
            import traceback
            errors.append(f"set {name}: build(w) raised {type(e).__name__}: {e}\n" + traceback.format_exc())
            continue
        say(f"  built {name} in {time.time() - t0:.1f}s")
        sets.append(w)
    if add_demo or not sets and not errors:
        if not sets:
            say("warning: no set modules found; using the built-in demo set so there is something to compile")
        w = voxel.World(demo.NAME, demo.ORIGIN, demo.SIZE)
        demo.build(w)
        sets.append(w)
    return sets, errors


# ---------------------------------------------------------------- checking a canvas

_FACE = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0)}


def attachment_warnings(w):
    """Blocks that the game will remove at once because what they hang on is missing: ladders, wall torches, wall signs
    and banners with nothing behind them, doors with nothing under them or a half missing."""
    out = []
    defaults = mcdata.block_defaults()
    for gid in range(2, len(w.palette)):
        name, props = mcdata.parse_block(w.palette[gid])
        short = name.split(":")[1]
        at = np.argwhere(w.a == gid)
        if not len(at):
            continue
        if short == "ladder" or short.endswith("wall_torch") or short.endswith("_wall_sign") or short.endswith("_wall_banner"):
            face = props.get("facing", defaults.get(name, {}).get("facing", "north"))
            dx, _, dz = _FACE[face]
            sx, sy, sz = at[:, 0] - dx, at[:, 1], at[:, 2] - dz
            inside = (sx >= 0) & (sx < w.size[0]) & (sz >= 0) & (sz < w.size[2])
            bad = inside & (w.a[np.clip(sx, 0, w.size[0] - 1), sy, np.clip(sz, 0, w.size[2] - 1)] <= 1)
            if bad.any():
                i = int(np.argmax(bad))
                out.append(f"{w.name}: {int(bad.sum())} of {len(at)} {w.palette[gid]} have no block behind them and will vanish (first at local {tuple(int(v) for v in at[i])})")
        elif short.endswith("_door"):
            half = props.get("half", "lower")
            if half == "lower":
                below = np.where(at[:, 1] > 0, w.a[at[:, 0], np.maximum(at[:, 1] - 1, 0), at[:, 2]], 0)
                above = w.a[at[:, 0], np.minimum(at[:, 1] + 1, w.size[1] - 1), at[:, 2]]
                bad = (below <= 1) | (above <= 1)
                what = "nothing under them or no upper half"
            else:
                below = w.a[at[:, 0], np.maximum(at[:, 1] - 1, 0), at[:, 2]]
                bad = below <= 1
                what = "no lower half"
            if bad.any():
                i = int(np.argmax(bad))
                out.append(f"{w.name}: {int(bad.sum())} of {len(at)} {w.palette[gid]} have {what} and will vanish (first at local {tuple(int(v) for v in at[i])})")
        elif short == "redstone_lamp" and props.get("lit") == "true":
            out.append(f"{w.name}: {len(at)} redstone_lamp[lit=true] turn themselves off within a second unless powered (use light blocks, sea_lantern, glowstone or shroomlight)")
    return out


def fluid_warnings(w):
    """Water and lava sources with air (or nothing) beside or under them flow away as soon as the chunk ticks."""
    out = []
    for fluid in ("water", "lava"):
        ids = [g for g in range(2, len(w.palette)) if w.palette[g].split("[")[0] == "minecraft:" + fluid
               and "level=" not in w.palette[g] or w.palette[g] == f"minecraft:{fluid}[level=0]"]
        if not ids:
            continue
        src = np.isin(w.a, ids)
        if not src.any():
            continue
        open_ = np.zeros(w.size, dtype=bool)
        free = w.a <= 1
        for axis, sl in ((0, 1), (0, -1), (2, 1), (2, -1), (1, -1)):
            shifted = np.zeros_like(free)
            idx_dst = [slice(None)] * 3
            idx_src = [slice(None)] * 3
            idx_dst[axis] = slice(0, -1) if sl == 1 else slice(1, None)
            idx_src[axis] = slice(1, None) if sl == 1 else slice(0, -1)
            shifted[tuple(idx_dst)] = free[tuple(idx_src)]
            open_ |= shifted
        leaks = src & open_
        if leaks.any():
            first = tuple(int(v) for v in np.argwhere(leaks)[0])
            out.append(f"{w.name}: {int(leaks.sum())} of {int(src.sum())} {fluid} source cells have air beside or under them and will flow away (first at local {first}); "
                       f"close the sides and the bottom or the fluid spreads over everything in reach")
    return out


def validate(w):
    """(errors, warnings) for one built set: block ids and states against the game's report, bounds, anchors."""
    errors, warnings = [], []
    table = mcdata.blocks()
    counts = np.bincount(w.a.ravel(), minlength=len(w.palette))
    for gid in range(2, len(w.palette)):
        msg = mcdata.check_block(w.palette[gid], table)
        if msg is None:
            name, props = mcdata.parse_block(w.palette[gid])
            name = name.split(":")[1]
            if counts[gid] and (name in FALLING or name.endswith("_concrete_powder") or name.endswith("anvil")):
                at = np.argwhere(w.a == gid)
                below = np.where(at[:, 1] > 0, w.a[at[:, 0], np.maximum(at[:, 1] - 1, 0), at[:, 2]], 0)
                loose = int((below <= 1).sum())                      # nothing (or air) underneath
                if loose:
                    warnings.append(f"{w.name}: {loose} of {int(counts[gid])} {w.palette[gid]} cells have nothing under them and will fall")
            if counts[gid] and name.endswith("_leaves") and props.get("persistent") != "true":
                warnings.append(f"{w.name}: {w.palette[gid]} ({int(counts[gid])} cells) will rot away: leaves need [persistent=true] unless a log is within 6 blocks")
            if counts[gid] and name in ("grass_block", "mycelium", "podzol"):
                at = np.argwhere(w.a == gid)
                above = w.a[at[:, 0], np.minimum(at[:, 1] + 1, w.size[1] - 1), at[:, 2]]
                covered = sum(int((above == g).sum()) for g in set(above.tolist())
                              if g > 1 and not comp.needs_neighbours(comp.canon(w.palette[g]))
                              and not any(k in w.palette[g] for k in ("glass", "ice")))
                if covered:
                    warnings.append(f"{w.name}: {covered} {name} cells have a solid block on top and will turn to dirt (use dirt under buildings)")
            continue
        if counts[gid]:
            at = np.argwhere(w.a == gid)[0]
            errors.append(f"set {w.name}: {w.palette[gid]!r}: {msg} ({int(counts[gid])} cells, first at local "
                          f"{tuple(int(v) for v in at)})")
        else:
            warnings.append(f"{w.name}: palette entry {w.palette[gid]!r} is invalid ({msg}) but no cell uses it")
    warnings += attachment_warnings(w)
    warnings += fluid_warnings(w)
    oy, sy = w.origin[1], w.size[1]
    if oy < BUILD_MIN_Y or oy + sy > BUILD_MAX_Y:
        errors.append(f"set {w.name}: y {oy}..{oy + sy - 1} is outside the build height {BUILD_MIN_Y}..{BUILD_MAX_Y - 1}")
    if not (w.a > 1).any():
        warnings.append(f"{w.name}: nothing was drawn")
    x0, y0, z0 = w.origin
    for name, a in w.anchors.items():
        if not (x0 <= a["x"] < x0 + w.size[0] and y0 <= a["y"] < y0 + w.size[1] and z0 <= a["z"] < z0 + w.size[2]):
            warnings.append(f"{w.name}: anchor '{name}' ({a['x']}, {a['y']}, {a['z']}) lies outside the set")
    for c in w.commands:
        if not isinstance(c, str) or not c.strip():
            errors.append(f"set {w.name}: a post-placement command is empty or not text: {c!r}")
    return errors, warnings


# ---------------------------------------------------------------- writing

class Out:
    """Writes files under the pack, remembers what it wrote, and leaves identical files alone."""

    def __init__(self, base):
        self.base, self.written = base, {}

    def put(self, rel, data):
        path = os.path.join(self.base, *rel.split("/"))
        if isinstance(data, str):
            data = data.encode("utf-8")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        same = False
        if os.path.isfile(path) and os.path.getsize(path) == len(data):
            with open(path, "rb") as f:
                same = f.read() == data
        if not same:
            with open(path, "wb") as f:
                f.write(data)
        self.written[rel] = len(data)

    def put_json(self, rel, value):
        self.put(rel, json.dumps(value, indent=1) + "\n")

    def put_function(self, path, lines):
        self.put(f"data/{NS}/function/{path}.mcfunction", "\n".join(lines) + "\n")

    def clean_old(self, manifest_path):
        """Remove files an earlier build wrote that this one did not."""
        if not os.path.isfile(manifest_path):
            return 0
        with open(manifest_path, encoding="utf-8") as f:
            old = json.load(f).get("files", [])
        n = 0
        for rel in old:
            if rel not in self.written:
                path = os.path.join(self.base, *rel.split("/"))
                if os.path.isfile(path):
                    os.remove(path)
                    n += 1
                d = os.path.dirname(path)
                while d != self.base and os.path.isdir(d) and not os.listdir(d):
                    os.rmdir(d)
                    d = os.path.dirname(d)
        return n


def shared_functions(compiled, anchors):
    """init, place_all, abort and enter_<set>, as {path: lines}."""
    fns = {"world/init": worldgen.init_lines()}
    names = [cs.name for cs in compiled]
    if names:
        fns["world/place_all"] = ["scoreboard objectives add angel_world dummy", "scoreboard players set #all angel_world 1",
                                  f"execute in minecraft:overworld run function {NS}:world/{names[0]}/p0"]
    else:
        fns["world/place_all"] = ["say [angel] there are no sets to place"]
    pending = []
    for cs in compiled:
        pending += [f"world/{cs.name}/p{i}" for i in range(cs.steps)]
        pending += [f"world/{cs.name}/c{i}" for i in range(sum(1 for k in cs.functions if k.startswith(f"world/{cs.name}/c")))]
    fns["world/abort"] = (["scoreboard players set #all angel_world 0", "scoreboard players set #rebuild angel_world 0"]
                          + [f"schedule clear {NS}:{p}" for p in pending]
                          + [f"forceload remove {r[0]} {r[1]} {r[2]} {r[3]}" for cs in compiled for r in cs.rects]
                          + ["say [angel] placement stopped (forceload released)"])
    for cs in compiled:
        fns[f"world/enter_{cs.name}"] = worldgen.enter_lines(cs.name, anchors.get(f"{cs.name}.start"))
    return fns


def write_all(compiled, worlds, out, anchors):
    shared = comp.finish_sets(compiled, anchors)
    shared.update(shared_functions(compiled, anchors))
    for cs in compiled:
        shared.update(cs.functions)
    for path, lines in shared.items():
        out.put_function(path, lines)
    for cs in compiled:
        for name, data in cs.structures.items():
            out.put(f"data/{NS}/structure/{name}.nbt", data)
    for rel, value in worldgen.files().items():
        out.put_json(rel, value)
    return shared


def pack_mcmeta(out):
    path = os.path.join(out.base, "pack.mcmeta")
    if not os.path.isfile(path):                  # not recorded in the manifest: it belongs to the whole pack, not to this tool
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"pack": {"description": "Angel Attack: the giant-robot story", "min_format": 121, "max_format": 121}}, f, indent=2)
            f.write("\n")
        say("  wrote pack.mcmeta (there was none)")


def write_previews(worlds):
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    for w in worlds:
        for axis, tag in (("y", "top"), ("x", "slice_x"), ("z", "slice_z")):
            voxel.preview(w, os.path.join(PREVIEW_DIR, f"{w.name}_{tag}.png"), axis=axis)
    say(f"  previews in {PREVIEW_DIR}")


# ---------------------------------------------------------------- main

def human(n):
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{int(n)} B"
        n /= 1024.0


def run(args):
    t0 = time.time()
    only = set(args.sets.split(",")) if args.sets else None
    say("building sets")
    if args.selftest or args.demo_only:
        w = voxel.World(demo.NAME, demo.ORIGIN, demo.SIZE)
        demo.build(w)
        worlds, errors = [w], []
    else:
        worlds, errors = make_sets(only, args.demo)
    warnings = []
    for w in worlds:
        e, wn = validate(w)
        errors += e
        warnings += wn
    for wn in warnings:
        say("warning: " + wn)
    if errors:
        say("\nERRORS")
        for e in errors:
            say("  " + e)
        say("\nnothing written.")
        return 1

    say("compiling")
    compiled = []
    for w in worlds:
        t1 = time.time()
        cs = comp.compile_set(w, args.method, args.air)
        cs.post = [c.strip() for c in w.commands]
        compiled.append(cs)
        say(f"  {w.name}: {len(cs.tiles)}/{int(np.prod(cs.tile_grid))} tiles with blocks, {cs.blocks:,} blocks, "
            f"{human(cs.structure_bytes)} of structure files, {len(cs.fix_cmds)} edge fixes ({time.time() - t1:.1f}s)")

    anchors = {}
    for w in worlds:
        for name, a in w.anchors.items():
            anchors[f"{w.name}.{name}"] = {k: a[k] for k in ("x", "y", "z", "yaw", "pitch")}

    out_dir = tempfile.mkdtemp(prefix="angel-selftest-") if args.selftest else (os.path.abspath(args.out) if args.out else PACK)
    out = Out(out_dir)
    shared = write_all(compiled, worlds, out, anchors)

    say("checking")
    problems = []
    for w, cs in zip(worlds, compiled):
        p, cells = verify.check_set(w, cs)
        problems += p
        say(f"  {w.name}: {'the compiled set reads back identical' if not p else 'MISMATCH'} ({cells:,} cells)")
    bad = cmdcheck.check_functions(shared)
    nlines = sum(len(v) for v in shared.values())
    for path, n, line, msg in bad[:30]:
        problems.append(f"function {path} line {n}: {msg}: {line[:140]}")
    say(f"  {len(shared)} functions, {nlines:,} lines: {len(bad)} lines the command tree does not accept")
    if problems:
        say("\nPROBLEMS")
        for p in problems:
            say("  " + p)
        if not args.selftest:
            say("(the files were written anyway; fix the cause and build again)")
        return 1

    if not args.selftest:
        pack_mcmeta(out)
        manifest = MANIFEST if not args.out else os.path.join(out_dir, "..", "build_manifest.json")
        anchors_path = ANCHORS if not args.out else os.path.join(out_dir, "..", "anchors.json")
        removed = out.clean_old(manifest)
        with open(manifest, "w", encoding="utf-8") as f:
            json.dump({"files": sorted(out.written)}, f, indent=0)
        with open(anchors_path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(anchors, f, indent=1)
            f.write("\n")
        say(f"  wrote {len(out.written)} files to {out_dir} (removed {removed} stale), {len(anchors)} anchors to {anchors_path}")
    else:
        say(f"  (self-test output in {out_dir})")
        shutil.rmtree(out_dir, ignore_errors=True)

    say("placement estimate (rough: detailed content costs more per block than plain cubes; measured 1-12 us per block)")
    total = 0.0
    for cs in compiled:
        est = max(cs.ticks_place / 20.0, cs.ms_place / 1000.0)
        total += est
        say(f"  {cs.name}: place about {est:.0f}s ({cs.steps} steps, {cs.ms_place / 1000:.1f}s of server work); "
            f"clear about {cs.ticks_clear / 20:.0f}s")
    say(f"  place_all: about {total:.0f}s")
    if args.preview:
        write_previews(worlds)
    say(f"done in {time.time() - t0:.1f}s")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--sets")
    ap.add_argument("--demo", action="store_true")
    ap.add_argument("--demo-only", action="store_true", dest="demo_only")
    ap.add_argument("--method", choices=("template", "fill"), default="template")
    ap.add_argument("--air", choices=("drop", "keep"), default="drop")
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--out", help="write the pack here instead of datapack\\angel (for tests)")
    return run(ap.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
