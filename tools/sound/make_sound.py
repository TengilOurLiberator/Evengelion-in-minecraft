"""Build the sound design for Angel Attack: ambience, effects and score, all synthesised in Python.

    python make_sound.py                      # build everything (parallel), write sounds.json + manifest.json
    python make_sound.py sfx.mine amb.hq      # just these
    python make_sound.py music                # a whole family (amb | sfx | music) or a prefix (sfx.breaker)
    python make_sound.py --list               # what exists, with targets
    python make_sound.py --no-pack ...        # render and encode but leave sounds.json alone
    python make_sound.py --jobs 4 ...         # worker processes (default: cpu count - 2)
    python make_sound.py --preview            # afterwards, render previews (same as analyze.py)

Outputs   pack/angel-resources/assets/angel/sounds/{sfx,amb,music}/<name>.ogg
          pack/angel-resources/assets/angel/sounds.json   only the sfx. / amb. / music. entries are written; every
                                                          other entry (the line.* voice events) is preserved
          tools/sound/manifest.json                       duration, ticks, loudness, loop flags for the datapack
"""
import argparse
import glob
import importlib
import json
import multiprocessing as mp
import os
import shutil
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
ROOT = os.path.dirname(os.path.dirname(HERE))
ASSETS = os.path.join(ROOT, "pack", "angel-resources", "assets", "angel")
SOUNDS = os.path.join(ASSETS, "sounds")
SOUNDS_JSON = os.path.join(ASSETS, "sounds.json")
MANIFEST = os.path.join(HERE, "manifest.json")
MODULES = ["amb", "sfx_world", "sfx_base", "sfx_fight", "music"]
OURS = ("sfx.", "amb.", "music.")
TP_CEILING = -1.25          # pre-encode true-peak ceiling, dBFS; the decoded ogg is checked against -1.0

import numpy as np
import soundfile as sf
import dsp
from dsp import SR
import reg


def load_modules(verbose=False):
    for m in MODULES:
        try:
            importlib.import_module(m)
        except ModuleNotFoundError as e:
            if e.name != m:
                raise
            if verbose:
                print(f"(module {m} not written yet, skipped)")


def find_tool(name):
    """same search order as tools/voices/common.py find_tool"""
    p = shutil.which(name)
    if p:
        return p
    for pat in (rf"D:\malmo-vr\tools\ffmpeg\*\bin\{name}.exe", rf"D:\*\tools\ffmpeg\*\bin\{name}.exe", rf"C:\ffmpeg\bin\{name}.exe"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise FileNotFoundError(f"{name} not found on PATH or in the known ffmpeg folders")


def out_path(spec):
    return os.path.join(SOUNDS, spec.kind, spec.short + ".ogg")


def encode(x, path, q):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = tempfile.mktemp(suffix=".wav", dir=tempfile.gettempdir())
    sf.write(tmp, x.astype(np.float32), SR, subtype="FLOAT")
    try:
        subprocess.run([find_tool("ffmpeg"), "-v", "error", "-y", "-i", tmp, "-c:a", "libvorbis", "-q:a", str(q), path], check=True)
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass


def finalize(spec, x):
    x = np.nan_to_num(np.asarray(x, dtype=np.float64))
    if spec.stereo and x.ndim == 1:
        x = np.stack([x, x], axis=1)
    if not spec.stereo and x.ndim == 2:
        x = x.mean(axis=1)
    if spec.loop:
        x = x - x.mean(axis=0)
    else:
        rms = np.sqrt(np.mean(x ** 2)) + 1e-12
        if np.max(np.abs(x.mean(axis=0))) > 0.02 * rms:
            x = dsp.hp(x, 10, 1)
    pk = np.max(np.abs(x))
    if pk < 1e-6:
        raise ValueError(f"{spec.name}: silent")
    if not spec.raw:                       # raw: the function already produced the final level
        gain_db = (spec.lufs - dsp.lufs(x)) if spec.lufs is not None else (spec.peak - dsp.sample_peak_db(x))
        x = x * dsp.db(gain_db)
    fin = spec.fin if spec.fin is not None else (0.0 if spec.loop else 0.0008)
    fout = spec.fout if spec.fout is not None else (0.0 if spec.loop else 0.02)
    x = dsp.fade(x, fin, fout, "lin")
    ceil = spec.ceiling if spec.ceiling is not None else TP_CEILING
    tp = dsp.true_peak_db(x)
    if tp > ceil:
        if spec.limit:
            x = dsp.limit(x, ceil - 0.15)
        x = x * dsp.db(min(0.0, ceil - dsp.true_peak_db(x)))
    return x


def build_one(name):
    spec = reg.REG[name]
    t0 = time.time()
    r = np.random.default_rng(spec.seed)
    res = spec.fn(r)
    meta = {}
    if isinstance(res, tuple):
        res, meta = res
    x = finalize(spec, res)
    path = out_path(spec)
    trim = 0.0
    for attempt in range(4):
        encode(x, path, spec.q)
        y, sr = sf.read(path, dtype="float64", always_2d=False)
        tp = dsp.true_peak_db(y)
        if tp <= -1.0:
            break
        trim = tp + 1.15
        x = x * dsp.db(-trim)
    n = len(y)
    rec = dict(name=name, file=os.path.relpath(path, ROOT).replace("\\", "/"), seconds=round(n / sr, 4), samples=n,
               ticks=round(n / sr * 20, 1), channels=1 if y.ndim == 1 else y.shape[1], sample_rate=sr,
               loop=bool(spec.loop), stream=bool(spec.stream), lufs=round(dsp.lufs(y), 2), true_peak=round(tp, 2),
               sample_peak=round(dsp.sample_peak_db(y), 2), bytes=os.path.getsize(path), note=spec.note,
               build_s=round(time.time() - t0, 1))
    rec.update(meta)
    return rec


def matches(name, pats):
    """no patterns = everything; otherwise a name or any prefix of it (amb, sfx.car, sfx.breaker)"""
    return not pats or any(name == p or name.startswith(p) for p in pats)


def event_entry(spec, files):
    """sounds.json entry for one event (files: list of sound specs)"""
    sounds = []
    for s in files:
        e = {"name": f"angel:{s.kind}/{s.short}"}
        if s.stream:
            e["stream"] = True
        if s.atten and s.atten != 16:
            e["attenuation_distance"] = s.atten
        sounds.append(e)
    return {"sounds": sounds}


def write_sounds_json():
    """merge: keep everything that is not ours (re-read the file right before writing), replace our entries"""
    ours = {}
    for name, spec in sorted(reg.REG.items()):
        if os.path.exists(out_path(spec)):
            ours[name] = event_entry(spec, [spec])
    for ev, names in reg.GROUPS.items():
        files = [reg.REG[n] for n in names if n in reg.REG and os.path.exists(out_path(reg.REG[n]))]
        if len(files) == len(names):
            ours[ev] = event_entry(None, files)
    old = {}
    if os.path.exists(SOUNDS_JSON):
        with open(SOUNDS_JSON, encoding="utf-8") as fh:
            old = json.load(fh)
    n_line_before = sum(1 for k in old if k.startswith("line."))
    merged = {k: v for k, v in old.items() if not k.startswith(OURS)}
    merged.update(ours)
    tmp = SOUNDS_JSON + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(merged, fh, indent=1)
    os.replace(tmp, SOUNDS_JSON)
    with open(SOUNDS_JSON, encoding="utf-8") as fh:
        new = json.load(fh)
    n_line_after = sum(1 for k in new if k.startswith("line."))
    others = [k for k in new if not k.startswith(OURS) and not k.startswith("line.")]
    print(f"sounds.json: {len(ours)} of ours written; line.* entries {n_line_before} -> {n_line_after}; other foreign entries {len(others)}")
    assert n_line_before == n_line_after, "line.* entries changed!"
    return len(ours)


def update_manifest(recs):
    man = {}
    if os.path.exists(MANIFEST):
        with open(MANIFEST, encoding="utf-8") as fh:
            man = json.load(fh)
    for r in recs:
        man[r["name"]] = r
    man = {k: man[k] for k in sorted(man)}
    with open(MANIFEST, "w", encoding="utf-8", newline="\n") as fh:
        json.dump(man, fh, indent=1)
    return man


def _worker(name):
    load_modules()
    try:
        return build_one(name)
    except Exception as e:                    # report which sound failed, keep going
        import traceback
        return dict(name=name, error=f"{type(e).__name__}: {e}", tb=traceback.format_exc())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("names", nargs="*")
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--no-pack", action="store_true")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 4) - 2))
    ap.add_argument("--preview", action="store_true")
    ap.add_argument("--table", action="store_true", help="print the manifest as a markdown table and exit")
    a = ap.parse_args()
    if a.table:
        with open(MANIFEST, encoding="utf-8") as fh:
            man = json.load(fh)
        print("| event | seconds | ticks | ch | LUFS | true peak | loop | notes |")
        print("|---|---|---|---|---|---|---|---|")
        for k, v in man.items():
            extra = ", ".join(f"{x}={v[x]}" for x in ("bloom_s", "buildup_s", "loop_start_s", "loop_seconds", "blast_s", "silence_start_s", "silence_end_s") if x in v)
            print(f"| `{k}` | {v['seconds']:.2f} | {v['ticks']:.0f} | {v['channels']} | {v['lufs']:.1f} | {v['true_peak']:.1f} | {'loop' if v['loop'] else ''} | {extra} |")
        return
    load_modules()
    todo = [n for n in sorted(reg.REG) if matches(n, a.names)]
    if a.names and not todo:
        sys.exit("nothing matches " + " ".join(a.names))
    if a.list:
        for n in todo:
            s = reg.REG[n]
            tgt = f"{s.lufs} LUFS" if s.lufs is not None else f"peak {s.peak}"
            print(f"{n:24s} {'loop ' if s.loop else '     '}{'stereo' if s.stereo else 'mono  '} {tgt}")
        print(len(todo), "sounds")
        return
    t0 = time.time()
    print(f"building {len(todo)} sounds with {a.jobs} workers")
    dsp.svf(np.zeros(64), 1000.0)                      # compile numba kernels once so the workers load the cache
    dsp.delayloop(np.zeros(64), 20.0)
    dsp.hosc(np.full(64, 100.0))
    dsp.limit(np.zeros(64))
    recs, failed = [], []
    if a.jobs <= 1 or len(todo) == 1:
        results = map(_worker, todo)
    else:
        pool = mp.get_context("spawn").Pool(a.jobs)
        results = pool.imap_unordered(_worker, todo)
    for rec in results:
        if "error" in rec:
            failed.append(rec)
            print(f"FAILED {rec['name']}: {rec['error']}\n{rec['tb']}")
        else:
            recs.append(rec)
            print(f"{rec['name']:22s} {rec['seconds']:7.2f}s {rec['channels']}ch  {rec['lufs']:6.1f} LUFS  tp {rec['true_peak']:6.2f}  {'loop' if rec['loop'] else ''}  ({rec['build_s']}s)", flush=True)
    update_manifest(recs)
    if not a.no_pack:
        write_sounds_json()
    total = sum(r["bytes"] for r in recs)
    print(f"{len(recs)} built, {len(failed)} failed, {total / 1e6:.1f} MB, {time.time() - t0:.0f}s")
    if a.preview:
        import analyze
        analyze.main([])
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    mp.freeze_support()
    main()
