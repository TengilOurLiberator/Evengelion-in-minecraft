"""gen.py - generate the raw candidates (3 seeds per target) with ACE-Step / Stable Audio Open through ComfyUI, one generation at a time.

    python gen.py                      # every event in prompts.json
    python gen.py music.fight sfx.     # these events / prefixes
    python gen.py --seeds 3 --force    # (re)generate even if the raw file exists
    python gen.py --stop-comfy         # stop ComfyUI at the end only if THIS run started it (default: leave it, `comfy.py stop` later)

Raw audio: work/sound_candidates/raw/<event>/<part>_k<candidate>[_p<piece>].flac, plus gen.json beside it (prompt, seed, timing).
Lengths come from the procedural file of each event (audio_utils.ref_path) so loops are generated long enough to be cut to size.
"""
import argparse
import json
import os
import shutil
import sys
import time
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import comfy
import audio_utils as au
import soundfile as sf

RAW = os.path.join(au.CAND, "raw")


def cfg():
    with open(os.path.join(HERE, "prompts.json"), encoding="utf-8") as fh:
        return json.load(fh)


def seconds_of(event):
    info = sf.info(au.ref_path(event))
    return info.frames / info.samplerate


def variant_cfg(e, k):
    """candidates 1-3 use the event's own prompt; variants[i] (a dict of overrides: tags, prompt, bpm, key, parts ...) gives candidates 3i+1..3i+3"""
    idx = (k - 1) // 3
    if idx == 0 or not e.get("variants"):
        return e
    return dict(e, **e["variants"][idx - 1])


def n_candidates(e):
    return 3 * (1 + len(e.get("variants", [])))


def plan(event, e, P):
    """list of generation jobs for one candidate: dicts(part, piece, engine, seconds, ...) (seed added by the caller)"""
    rec = e["recipe"]
    tail = P["ace_tail"]
    out = []
    if rec in ("music_loop", "music_long_loop"):
        L = seconds_of(e["outputs"][0] if rec == "music_long_loop" else event)
        xf = e["xf_beats"] * 60.0 / e["bpm"] if "xf_beats" in e else e["xf"]
        extra = 14.0 if rec == "music_long_loop" else 12.0
        sec = min(240.0, round((L + xf + extra) * 1.06, 1))
        out.append(dict(part="main", piece=0, engine="ace", seconds=sec, tags=e["tags"] + tail, bpm=e["bpm"], key=e["key"]))
    elif rec == "music_oneshot":
        out.append(dict(part="main", piece=0, engine="ace", seconds=e["gen_seconds"], tags=e["tags"] + tail, bpm=e["bpm"], key=e["key"]))
    elif rec == "music_launch":
        for part, p in e["parts"].items():
            out.append(dict(part=part, piece=0, engine="ace", seconds=p["gen_seconds"], tags=p["tags"] + tail, bpm=e["bpm"], key=e["key"]))
    elif rec == "bed":
        L = seconds_of(event)
        n, xf = e["pieces"], e["xf"]
        piece = (L + n * xf) / n
        sec = min(47.0, round(piece + 3.0, 1))
        for i in range(n):
            out.append(dict(part="main", piece=i, engine="sao", seconds=sec, prompt=e["prompt"], neg=P[e["neg"]]))
    elif rec == "oneshot":
        out.append(dict(part="main", piece=0, engine="sao", seconds=min(47.0, e["gen_seconds"]), prompt=e["prompt"], neg=P[e["neg"]]))
    else:
        raise ValueError(f"{event}: unknown recipe {rec}")
    return out


def raw_name(job, k):
    return f"{job['part']}_k{k}_p{job['piece']}.flac"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--stop-comfy", action="store_true")
    a = ap.parse_args()
    P = cfg()
    todo = [n for n in P["events"] if not a.names or any(n == p or n.startswith(p) for p in a.names)]
    started = comfy.start()
    try:
        for event in todo:
            e = P["events"][event]
            folder = os.path.join(RAW, event)
            os.makedirs(folder, exist_ok=True)
            logp = os.path.join(folder, "gen.json")
            log = json.load(open(logp)) if os.path.exists(logp) else {}
            for k in range(1, n_candidates(e) + 1):
                jobs = plan(event, variant_cfg(e, k), P)
                for j in jobs:
                    name = raw_name(j, k)
                    dst = os.path.join(folder, name)
                    if os.path.exists(dst) and not a.force:
                        continue
                    seed = zlib.crc32(event.encode()) % 90000 + 1000 * k + 37 * j["piece"] + (7 if j["part"] == "drive" else 0)
                    t0 = time.time()
                    try:
                        if j["engine"] == "ace":
                            src = comfy.ace(j["tags"], j["seconds"], seed, j["bpm"], j["key"], prefix=f"{event}_{name[:-5]}")
                        else:
                            src = comfy.sao(j["prompt"], j["seconds"], seed, negative=j["neg"], prefix=f"{event}_{name[:-5]}")
                    except Exception as ex:                         # one failure must not stop the batch
                        print(f"FAILED {event} {name}: {ex}", flush=True)
                        continue
                    shutil.copyfile(src, dst)
                    log[name] = {key: v for key, v in dict(j, seed=seed, took_s=round(time.time() - t0, 1)).items()}
                    json.dump(log, open(logp, "w"), indent=1)
                    print(f"{event:24s} {name:22s} {j['seconds']:6.1f}s seed {seed}  ({time.time() - t0:.0f}s)", flush=True)
    finally:
        if started and a.stop_comfy:
            comfy.stop()


if __name__ == "__main__":
    main()
