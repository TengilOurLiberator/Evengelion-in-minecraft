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
import pace                                    # noqa: E402
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

    from lines import Line
    ctx = Context(warn)
    out = Out(out_dir) if out_dir else Out()
    register_system(ctx)
    mods = discover()
    Line.touched.clear()
    Line.tracking = True                     # which lines' LENGTHS the scenes read while they are built (sim.check_timing_bound)
    try:
        for mod in mods:
            s = Scene(mod.N, mod.TITLE, ctx)
            mod.build(s, ctx)
            s.module = mod
            ctx.scenes.append(s)
    finally:
        Line.tracking = False
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


def pace_table():
    """Runs `--check` three times (as subprocesses: the presets are build-time state) and prints each scene's nominal duration side by side:
         full, estimator as recorded    the original pacing, a line said while a character walks counted on top of the walk (what --check always printed)
         full, overlap counted          the same pacing, the estimator that counts those lines as part of the walk
         video                          the default pacing (overlap counted)
       and the errors / warnings of the video run."""
    import subprocess
    here = os.path.join(HERE, "build_story.py")
    runs = [("full (as recorded)", ["--pace", "full", "--est-overlap", "off"]), ("full (overlap)", ["--pace", "full", "--est-overlap", "on"]), ("video", ["--pace", "video"])]
    res = []
    for name, extra in runs:
        r = subprocess.run([sys.executable, here, "--check", "--quiet"] + extra, capture_output=True, text=True, cwd=HERE, encoding="utf-8", errors="replace")
        rows = {int(m.group(1)): (float(m.group(3)), m.group(2)) for m in re.finditer(r"^SCENE (\d+): (.*?)\s+nominal duration\s+([\d.]+)s", r.stdout, re.M)}
        tail = re.findall(r"^(\d+) errors, (\d+) warnings", r.stdout, re.M)
        res.append((name, rows, tail[-1] if tail else ("?", "?")))
    titles = {n: t for n, t in ((n, v[1]) for n, v in res[0][1].items())}
    print(f"{'scene':28s}" + "".join(f"{name:>22s}" for name, _, _ in res))
    for n in sorted(titles):
        print(f"{n}  {titles[n]:25s}" + "".join(f"{rows.get(n, (0, ''))[0]:15.0f} s ({rows.get(n, (0, ''))[0] / 60:4.1f})" for _, rows, _ in res))
    tot = [sum(v[0] for v in rows.values()) for _, rows, _ in res]
    print(f"{'TOTAL':28s}" + "".join(f"{t:15.0f} s ({t / 60:4.1f})" for t in tot))
    print("checker: " + "; ".join(f"{name}: {e} errors, {w} warnings" for name, _, (e, w) in res))
    return 0 if all(t[0] == "0" for _, _, t in res) else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dry", action="store_true", help="test variant with a mannequin as the player")
    ap.add_argument("--out", help="write the pack here instead of datapack/angel")
    ap.add_argument("--check", action="store_true", help="run the offline checker and simulator, write nothing")
    ap.add_argument("--quiet", action="store_true")
    ap.add_argument("--extra", help="a folder of extra scene modules sNN.py (they replace scenes of the same number)")
    ap.add_argument("--scenes", help="build only these scene numbers, e.g. 1,2,3,4,5 (for testing while another scene is being written)")
    ap.add_argument("--steps", help="also write a JSON listing of every scene's steps (for test drivers and the voice bridge)")
    ap.add_argument("--steps-only", action="store_true", help="with --steps: stop after writing the listing (nothing is written to the datapack)")
    ap.add_argument("--stuck-hint", type=float, help="seconds without progress before a generic direction line (default: the pace preset's stuck_hint_s)")
    ap.add_argument("--stuck-skip", type=float, help="seconds without progress before a step is skipped by itself (default: the pace preset's stuck_skip_s)")
    ap.add_argument("--pace", default="video", choices=sorted(pace.PRESETS),
                    help="pacing preset (tools/story/pace.py): video (default; a playthrough in about 13 minutes) or full (the original, unhurried values)")
    ap.add_argument("--est-overlap", choices=["on", "off"],
                    help="how --check counts a line said while a character walks: on = as part of the walk (the default of video), off = on top of it (the original estimator: full)")
    ap.add_argument("--table", action="store_true",
                    help="run --check for the original pacing (the recorded estimator), full and video, and print the nominal duration of every scene side by side")
    args = ap.parse_args(argv)
    pace.use(args.pace)
    if args.est_overlap:
        pace.PACE.override(est_overlap=args.est_overlap == "on")
    if args.table:
        return pace_table()
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
        import re as _re
        listing = {}
        for sc_ in ctx.scenes:
            rows = []
            for st in sc_.steps:
                row = {"i": st.index, "kind": st.kind, "note": getattr(st, "note", ""), "est": getattr(st, "est", None),
                       "line": getattr(st, "lid", None), "mode": getattr(st, "mode", None)}
                if st.kind in ("goto", "branch"):
                    row["target"] = sc_.labels[st.label]                          # step index the jump goes to
                    if st.kind == "branch":
                        row["cond"] = st.cond.text()
                if st.kind in ("sleep", "after"):
                    row["sec"] = st.sec
                if st.kind == "handover":
                    row["to"] = st.to
                if st.kind == "wait":
                    nud = getattr(st, "nudges", None)
                    row.update(speaker=st.speaker, prompt=st.prompt, timeout=st.timeout, answer_ends=bool(getattr(st, "answer_ends", False)),
                               nudge_lines=list(nud.lines) if nud is not None else [],
                               nudge_first=nud.first if nud is not None else None, nudge_repeat=nud.repeat if nud is not None else None)
                if st.kind == "until":
                    nag = getattr(st, "nag", None)
                    row["nag_lines"] = sorted({m.group(1).replace("_", ".") for c in (nag[2] if nag else []) for m in [_re.search(r"say/(\d+_\d+)", c)] if m})
                    row["timeout"] = st.timeout
                rows.append(row)
            listing[sc_.n] = rows
        n_scenes = len(listing)
        listing["_meta"] = {"setup_end": {str(sc_.n): int(getattr(sc_, "setup_end", 0) or 0) for sc_ in ctx.scenes}}
        with open(args.steps, "w", encoding="utf-8") as f:
            json.dump(listing, f, indent=1)
        if args.steps_only:
            print(f"step listing: {sum(len(v) for k, v in listing.items() if k != '_meta')} steps of {n_scenes} scenes -> {args.steps}")
            return 0
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
