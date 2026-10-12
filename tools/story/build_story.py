"""Build the story datapack: the sequencer engine, every line as a function, and the scenes found in tools/story/scenes/.

    python build_story.py                 write data/angel/function/story/** and say/** into datapack/angel
    python build_story.py --check         build in memory and run the offline checker / simulator (writes nothing)
    python build_story.py --dry           the test variant: a mannequin tagged angel.testplayer stands in for the player
    python build_story.py --out DIR       write the pack into DIR instead (a test copy)

Use the Python of the D:\\voice-assistant environment (numpy).  Adding a scene = adding scenes/sNN.py (see README.md).
"""
import argparse
import importlib
import os
import pkgutil
import re
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import core                                    # noqa: E402
from core import CFG, Out                      # noqa: E402


EXTRA = []
ONLY = []                                    # --scenes: build only these scene numbers (a scene module that is being written does not stop the others)


def discover():
    import scenes
    mods = []
    for m in pkgutil.iter_modules(scenes.__path__):
        if re.match(r"s\d\d", m.name) and (not ONLY or int(m.name[1:3]) in ONLY):
            mod = importlib.import_module(f"scenes.{m.name}")
            mods.append(mod)
    for d in EXTRA:                          # scene modules from another folder (to try a scene without putting it in the repo)
        for m in pkgutil.iter_modules([d]):
            if re.match(r"s\d\d", m.name):
                if d not in sys.path:
                    sys.path.insert(0, d)
                mods = [x for x in mods if x.N != importlib.import_module(m.name).N] + [importlib.import_module(m.name)]
    mods.sort(key=lambda m: m.N)
    ns = [m.N for m in mods]
    if len(set(ns)) != len(ns):
        raise SystemExit(f"two scene modules share a number: {ns}")
    return mods


def build(dry=False, out_dir=None, warn=print, quiet=False):
    """Compile everything; returns (ctx, out, summary dict)."""
    CFG.dry = dry
    t0 = time.time()
    from context import Context
    from engine import Compiler, Scene
    from lines import write_lines
    from system import build_system, register as register_system

    ctx = Context(warn)
    out = Out(out_dir) if out_dir else Out()
    register_system(ctx)
    mods = discover()
    for mod in mods:
        s = Scene(mod.N, mod.TITLE, ctx)
        mod.build(s, ctx)
        s.module = mod
        ctx.scenes.append(s)
    comp = Compiler(out, ctx)
    for s in ctx.scenes:
        comp.compile(s)
    # scene flags: every #f.<name> any file mentions is cleared by halt
    pat = re.compile(r"#f\.([A-Za-z0-9_]+)")
    for text in out.files.values():
        ctx.flags.update(pat.findall(text))
    write_lines(out, ctx.lines)
    build_system(out, ctx)
    summary = {"scenes": [(s.n, s.title, len(s.steps)) for s in ctx.scenes], "functions": len(out.files), "seconds": time.time() - t0}
    return ctx, out, summary


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry", action="store_true", help="test variant with a mannequin as the player")
    ap.add_argument("--out", help="write the pack here instead of datapack/angel")
    ap.add_argument("--check", action="store_true", help="run the offline checker and simulator, write nothing")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--extra", help="a folder of extra scene modules sNN.py (they replace scenes of the same number)")
    ap.add_argument("--scenes", help="build only these scene numbers, e.g. 1,2,3,4,5 (for testing while another scene is being written)")
    ap.add_argument("--steps", help="also write a JSON listing of every scene's steps (for test drivers)")
    ap.add_argument("--stuck-hint", type=float, help="seconds without progress before a generic direction line (default CFG.stuck_hint_s = 60)")
    ap.add_argument("--stuck-skip", type=float, help="seconds without progress before a step is skipped by itself (default CFG.stuck_skip_s = 150)")
    args = ap.parse_args(argv)
    if args.stuck_hint is not None:
        CFG.stuck_hint_s = args.stuck_hint
    if args.stuck_skip is not None:
        CFG.stuck_skip_s = args.stuck_skip
    if args.extra:
        EXTRA.append(os.path.abspath(args.extra))
    if args.scenes:
        ONLY.extend(int(v) for v in args.scenes.split(","))
    ctx, out, summary = build(args.dry, args.out, warn=(lambda m: None) if args.quiet else print)
    if args.steps:
        import json
        listing = {}
        for sc_ in ctx.scenes:
            listing[sc_.n] = [{"i": st.index, "kind": st.kind, "note": getattr(st, "note", ""), "est": getattr(st, "est", None),
                               "line": getattr(st, "lid", None), "mode": getattr(st, "mode", None)} for st in sc_.steps]
        with open(args.steps, "w", encoding="utf-8") as f:
            json.dump(listing, f, indent=1)
    if args.check:
        import sim
        return sim.main_check(ctx, out)
    base = os.path.abspath(args.out) if args.out else core.PACK
    manifest = core.MANIFEST if not args.out else os.path.join(base, "..", "story_manifest.json")
    out.base = base
    written, removed = out.write(manifest)
    print(f"story: {summary['functions']} files ({written} changed, {removed} stale removed) in {summary['seconds']:.1f}s -> {base}")
    if not args.out:
        import cardfont                      # the title-card typeface lives in the resource pack: (re)write it with the datapack (idempotent)
        changed = cardfont.write_assets()
        print(f"card font angel:card: {len(changed)} resource-pack files changed")
    for n, title, steps in summary["scenes"]:
        print(f"  scene {n}: {title} ({steps} steps)")
    if ctx.missing_anchors:
        print("MISSING ANCHORS:", ctx.missing_anchors)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
