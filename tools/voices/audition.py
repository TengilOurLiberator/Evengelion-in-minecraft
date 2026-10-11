"""Hear the five voices before anything is recorded.

    python audition.py                         # uses a short dry narration clip from D:\\genesis-vr\\verses\\dry
    python audition.py my_voice.wav            # any wav of the user speaking (a few seconds is plenty)
    python audition.py --compare               # also render the plain-DSP version of each human voice (<NAME>__dsp.wav)
    python audition.py --refs                  # rebuild the synthetic conversion targets first
    python audition.py --no-verify             # skip the Whisper intelligibility check (faster)

Writes D:\\angel-attack\\voices\\audition\\<SPEAKER>.wav for MISATO, RITSUKO, GENDO, REI, BASE, a few
transmission variants (BASE__radio.wav, MISATO__radio.wav, RITSUKO__phone.wav, GENDO__above.wav) and
_report.json, and prints measurements: median pitch before/after, formants, loudness, clipping, silence,
and how well Whisper still understands each voice.
"""
import argparse
import glob
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import common
import config
import transform
from common import SR, f0_stats, formant_estimate, lufs, peak_db


def pick_clip():
    cands = []
    for p in sorted(glob.glob(r"D:\genesis-vr\verses\dry\*.wav")):
        x = common.read_audio(p)
        d = len(x) / SR
        if 4.0 <= d <= 8.0:
            cands.append((abs(d - 6.0), p))
    if not cands:
        sys.exit("no dry narration clip found; pass a wav of the user speaking")
    return min(cands)[1]


def metrics(x):
    s = f0_stats(x)
    db = common.frame_db(x)
    return {"dur": round(len(x) / SR, 2), "f0": round(s["median"], 1), "p10": round(s["p10"], 1), "p90": round(s["p90"], 1),
            "spread": round(s["p90"] / max(s["p10"], 1), 2), "iqr": round(s["p75"] / max(s["p25"], 1), 2),
            "centroid": round(common.spectral_centroid(x)), "formants": [round(v) for v in formant_estimate(x)],
            "lufs": round(lufs(x), 1), "peak": round(peak_db(x), 1),
            "clipped": int((np.abs(x) >= 0.999).sum()), "active_pct": round(float((db > -50).mean() * 100), 0)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav", nargs="?")
    ap.add_argument("--out", default=common.AUDITION_DIR)
    ap.add_argument("--compare", action="store_true")
    ap.add_argument("--refs", action="store_true")
    ap.add_argument("--no-extras", action="store_true")
    ap.add_argument("--no-verify", action="store_true")
    a = ap.parse_args()

    src = a.wav or pick_clip()
    x = common.read_audio(src)
    print(f"source: {src}  ({len(x) / SR:.1f}s)")
    if a.refs:
        transform.make_refs()
    eng = transform.Engine()
    base = metrics(x)
    base["file"] = src
    print(f"source voice: median F0 {base['f0']} Hz (p10 {base['p10']}, p90 {base['p90']}), formants {base['formants']}, {base['lufs']} LUFS\n")
    jobs = [(s, s, None, None) for s in common.SPEAKERS]                     # (label, speaker, method, fx)
    if a.compare:
        jobs += [(f"{s}__dsp", s, "dsp", None) for s in common.HUMANS]
    if not a.no_extras:
        jobs += [("BASE__dry", "BASE", None, "none"), ("BASE__radio", "BASE", None, "radio"),
                 ("MISATO__radio", "MISATO", None, "radio"), ("RITSUKO__phone", "RITSUKO", None, "phone"),
                 ("GENDO__above", "GENDO", None, "above")]
    os.makedirs(a.out, exist_ok=True)
    results = {}
    outs = {}
    for label, sp, method, fxname in jobs:
        t0 = time.time()
        y, info = transform.render(sp, x, "", method, eng, seed=1, force_fx=fxname)
        common.write_wav(os.path.join(a.out, label + ".wav"), y)
        outs[label] = y
        m = metrics(y)
        m.update(method=info["method"], fx=info["fx"], seconds_to_render=round(time.time() - t0, 1))
        results[label] = m
        print(f"{label:15} {m['dur']:5.1f}s  F0 {m['f0']:5.0f} Hz (p10-p90 {m['p10']:.0f}-{m['p90']:.0f}, spread x{m['spread']:.2f})  "
              f"formants {m['formants']}  bright {m['centroid']} Hz  {m['lufs']} LUFS  peak {m['peak']} dB  clipped {m['clipped']}  active {m['active_pct']:.0f}%  [{info['method']}]")

    if not a.no_verify:
        import asr
        ref_text, _ = asr.transcribe(x)
        print(f"\nWhisper hears the source as: {ref_text!r}")
        for label, y in outs.items():
            h, _ = asr.transcribe(y)
            results[label]["word_error_rate"] = round(asr.wer(ref_text, h), 3)
            results[label]["heard"] = h
            print(f"  {label:15} word error rate {results[label]['word_error_rate']:.2f}")

    # ---- are they five different people?  (speaker-encoder cosine similarity; ~0.5-0.75 is "different people")
    sims = None
    if not a.no_verify:
        import speaker_embed
        five = {"source": x, **{s: outs["BASE__dry" if s == "BASE" and "BASE__dry" in outs else s] for s in common.SPEAKERS}}
        labels, M = speaker_embed.similarity_matrix(five)
        sims = {"labels": labels, "matrix": [[round(float(v), 2) for v in r] for r in M]}
        print("\nspeaker similarity (1.0 = same voice; different people are usually 0.5-0.75):")
        print(" " * 9 + "".join(f"{l[:7]:>8}" for l in labels))
        for l, r in zip(labels, M):
            print(f"{l:9}" + "".join(f"{v:8.2f}" for v in r))

    # ---- the checks: did each voice move the way it was meant to?
    f = {k: v["f0"] for k, v in results.items()}
    src_f0 = base["f0"]
    checks = [
        ("MISATO is higher than the source", f["MISATO"] > src_f0 * 1.25),
        ("RITSUKO is higher than the source", f["RITSUKO"] > src_f0 * 1.15),
        ("RITSUKO is lower than MISATO", f["RITSUKO"] < f["MISATO"]),
        ("GENDO is lower than the source", f["GENDO"] < src_f0 * 0.95),
        ("REI is the highest voice", f["REI"] > f["MISATO"]),
        ("GENDO has a narrow pitch range (spread < 1.25)", results["GENDO"]["spread"] < 1.25),
        ("REI has a narrow pitch range (spread < 1.35)", results["REI"]["spread"] < 1.35),
        ("BASE is monotone (inter-quartile pitch ratio < 1.08)", results.get("BASE__dry", results["BASE"])["iqr"] < 1.08),
    ]
    if sims:
        M = np.array(sims["matrix"])
        L = sims["labels"]
        for i, p in enumerate(L):
            for j, q in enumerate(L):
                if i < j and p != "source":
                    checks.append((f"{p} and {q} sound like different people (similarity {M[i][j]:.2f} < 0.85)", M[i][j] < 0.85))
                if i < j and p == "source" and q != "BASE":
                    checks.append((f"{q} no longer sounds like the user (similarity {M[i][j]:.2f} < 0.80)", M[i][j] < 0.80))
    for label, r in results.items():
        checks.append((f"{label}: not silent (>25% active)", r["active_pct"] > 25))
        checks.append((f"{label}: no clipping", r["clipped"] == 0 and r["peak"] <= config.PEAK_CEILING_DB + 0.3))
        checks.append((f"{label}: sane duration ({base['dur'] * 0.7:.1f}-{base['dur'] * 1.8:.1f}s)", base["dur"] * 0.7 <= r["dur"] <= base["dur"] * 1.8))
        if "word_error_rate" in r and not label.startswith(("BASE", "MISATO__radio")):
            checks.append((f"{label}: still understood (WER < 0.25)", r["word_error_rate"] < 0.25))
    print()
    bad = 0
    for name, ok in checks:
        bad += (not ok)
        print(("PASS  " if ok else "FAIL  ") + name)
    json.dump({"source": base, "voices": results, "speaker_similarity": sims, "checks": [{"check": n, "pass": bool(o)} for n, o in checks]},
              open(os.path.join(a.out, "_report.json"), "w"), indent=1)
    print(f"\n{len(checks) - bad}/{len(checks)} checks passed. Files are in {a.out}")


if __name__ == "__main__":
    main()
