"""The TTS version of every line of the four characters: references, tuning, rendering, installing, auditioning.

    tts_lines.py refs                       build voices\\tts_refs\\<SPEAKER>.wav from the user's voice-converted recordings (clean, effect-free clips)
    tts_lines.py tune [--speaker S]         try settings on a sample of lines and print the measurements (nothing is written but a report)
    tts_lines.py render [--speaker S] [--ids a,b] [--force]
                                            speak all 111 lines dry (voices\\tts_raw), each transcribed back and re-rolled on a mismatch
    tts_lines.py backup                     MOVE voices\\final\\<4 speakers> and the pack's four line folders to voices\\backup_user_recordings (nothing deleted)
    tts_lines.py install [--speaker S]      effects by direction + loudness -> voices\\final\\<SPEAKER>\\<id>.wav, then pack_sounds (oggs, sounds.json, durations.json)
    tts_lines.py audition                   three varied lines per character -> voices\\audition_tts\\
    tts_lines.py report                     measurements of the finished set (pitch order, rate, speaker similarity, loudness, silences)

Run with D:\\voice-assistant\\.venv\\Scripts\\python.exe.  BASE lines are never touched.  The effects are transform.py's (its direction rules and numbers);
its voice-conversion stage is not used.  A reference is only ever the user's own (converted) voice.
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

import numpy as np  # noqa: E402

import common  # noqa: E402
import script_lines  # noqa: E402
import tts_config as tc  # noqa: E402
import tts_lib  # noqa: E402
from common import SR  # noqa: E402

HUMANS = tts_lib.HUMANS


def human_lines():
    return [l for l in script_lines.parse() if l["speaker"] in HUMANS]


def final_path(sp, lid, base=None):
    return os.path.join(base or common.FINAL_DIR, sp, lid + ".wav")


def user_final(sp, lid):
    """The user's voice-converted line: voices\\final, or the backup once it has been moved."""
    for d in (common.FINAL_DIR, os.path.join(tc.BACKUP_DIR, "final")):
        p = final_path(sp, lid, d)
        if os.path.exists(p):
            return p
    return None


# ====================================================================================== refs
MIN_SIM = {"GENDO": 0.85, "REI": 0.70}     # the converted voices of the commander (very low) and of the girl (very soft) are harder for Whisper; all others 0.97

def cmd_refs(a):
    import asr
    lines = [l for l in human_lines() if not l["direction"] and not l["nonverbal"]]
    os.makedirs(tc.REFS_DIR, exist_ok=True)
    report = {}
    dry_engine = None
    for sp in ([a.speaker.upper()] if a.speaker else HUMANS):
        cands = []
        pool = [l for l in lines if l["speaker"] == sp]
        if sp == "GENDO":                                       # every line of his has an effect: re-render the raw recordings WITHOUT one
            pool = [l for l in human_lines() if l["speaker"] == sp and not l["nonverbal"]]
            import transform
            dry_engine = dry_engine or transform.Engine()
        for l in pool:
            if sp == "GENDO":
                raw = os.path.join(common.RAW_DIR, sp, l["id"] + ".wav")
                if not os.path.exists(raw) or l["direction"] and any(k in l["direction"] for k in ("handset", "radio")):
                    continue
                x, _ = transform.render(sp, common.read_audio(raw), "", None, dry_engine, seed=zlib.crc32(l["id"].encode()))
            else:
                p = user_final(sp, l["id"])
                if not p:
                    continue
                x = common.read_audio(p)
            dur = len(x) / SR
            if dur < 2.0:
                continue
            heard, _ = asr.transcribe(x)
            sim = tts_lib.similarity(l["text"], heard)
            st = common.f0_stats(x)
            spread = st["p90"] / max(st["p10"], 1.0)
            peak = common.peak_db(x)
            act = tts_lib.active_stats(x)
            calm = 1.0 / (1.0 + max(0.0, min(spread, 3.0) - 1.35) * 2.5)        # (a spread beyond x3 is the pitch tracker slipping on a very low voice)
            score = min(dur, 9.0) * (1.0 if sim >= MIN_SIM.get(sp, 0.97) else 0.0) * calm * (0.8 if "!" in l["text"] else 1.0) * (0.0 if act["inner_silence_s"] > 0.9 else 1.0)
            cands.append(dict(id=l["id"], dur=round(dur, 2), sim=round(sim, 3), f0=round(st["median"]), spread=round(spread, 2),
                              peak=round(peak, 1), score=round(score, 2), text=l["text"], audio=x))
        cands.sort(key=lambda c: -c["score"])
        want_total, max_clips = (11.0, 4) if sp == "REI" else (14.0, 3)
        chosen, total = [], 0.0
        for c in cands:
            if c["score"] <= 0 or len(chosen) >= max_clips or total >= want_total or (c["score"] < 1.5 and total >= 8.0):
                break
            if total + c["dur"] > 17.5:
                continue
            chosen.append(c)
            total += c["dur"]
        print(f"\n{sp}: {len(cands)} usable clips; candidates by score:")
        for c in cands[:8]:
            print(f"   {c['id']:5} {c['dur']:5.1f}s  sim {c['sim']:.2f}  F0 {c['f0']}  spread x{c['spread']}  peak {c['peak']} dB  score {c['score']}  {c['text'][:48]}")
        if not chosen:
            print(f"   NO CLIP for {sp}")
            continue
        gap = np.zeros(int(0.22 * SR), np.float32)
        audio = np.concatenate([np.concatenate([c["audio"], gap]) for c in chosen])
        shape = tc.REF_SHAPE.get(sp)
        if shape:
            import dsp
            audio = common.rubberband(audio, pitch=shape["pitch"], formant="preserved") if shape.get("pitch", 1.0) != 1.0 else audio
            audio = common.formant_shift_only(audio, shape["formant"]) if shape.get("formant", 1.0) != 1.0 else audio
            audio = dsp.breath(audio, SR, level_db=shape["breath_db"]) if shape.get("breath_db") is not None else audio
        common.write_wav(tc.ref_path(sp), audio)
        report[sp] = {"clips": [c["id"] for c in chosen], "seconds": round(len(audio) / SR, 1), "median_f0": round(common.f0_stats(audio)["median"]),
                      "source": "dry re-render of the raw recordings through the voice conversion (no effect)" if sp == "GENDO" else "voices\\final (no direction)",
                      "reshaped": shape or None}
        print(f"   -> {tc.ref_path(sp)}: {', '.join(report[sp]['clips'])}  {report[sp]['seconds']} s  median F0 {report[sp]['median_f0']} Hz")
    p = os.path.join(tc.REFS_DIR, "refs.json")
    old = json.load(open(p)) if os.path.exists(p) else {}
    old.update(report)
    json.dump(old, open(p, "w"), indent=1)


# ====================================================================================== measuring a take
def measure(sp, line, x, synth_embed=None):
    import asr
    heard, _ = asr.transcribe(x)
    st = common.f0_stats(x)
    act = tts_lib.active_stats(x)
    sim = tts_lib.similarity(line["text"], heard)
    return dict(heard=heard, sim=round(sim, 3), f0=round(st["median"], 1), p10=round(st["p10"], 1), p90=round(st["p90"], 1),
                dur=round(len(x) / SR, 2), speech=round(act["speech_s"], 2), wps=round(tts_lib.rate_wps(line["text"], x), 2),
                inner=round(act["inner_silence_s"], 2), peak=round(act["peak"], 3))


def take_score(m, nwords, sp):
    """Higher is better.  Similarity first; then penalties for clipping, a long pause, a pace far outside the character's range."""
    s = m["sim"]
    if m["peak"] >= tc.PEAK_MAX:
        s -= 0.15
    if m["inner"] > tc.MAX_INNER_SILENCE_S:
        s -= 0.1 * min(3.0, m["inner"] - tc.MAX_INNER_SILENCE_S + 0.5)
    if nwords >= 3 and m["f0"] == 0:
        s -= 0.08                                   # a take with no voiced speech at all is a whisper: not the same person as the other lines
    lo, hi = tc.RATE_TARGET[sp]
    if nwords >= 4 and m["wps"]:
        wps_final = m["wps"]
        if wps_final < lo * 0.7 or wps_final > hi * 1.4:
            s -= 0.1
    return s


# ====================================================================================== tune
SAMPLE_IDS = {
    "MISATO": ["1.04", "2.01", "2.07", "3.09", "4.17", "5.24", "5.34", "6.19"],
    "RITSUKO": ["2.13", "4.16", "5.02", "5.14", "5.23", "5.33", "6.11", "7.17"],
    "GENDO": ["5.04", "5.05", "5.18", "5.20", "5.26", "5.41", "6.17", "7.18"],
    "REI": ["5.28", "5.36", "5.37", "5.38", "5.39", "5.44"],
}


def cmd_tune(a):
    import speaker_embed
    synth = tts_lib.Synth()
    lines = {l["id"]: l for l in human_lines()}
    grid_e = [float(v) for v in a.exaggeration.split(",")] if a.exaggeration else None
    grid_c = [float(v) for v in a.cfg.split(",")] if a.cfg else None
    results = {}
    for sp in ([a.speaker.upper()] if a.speaker else HUMANS):
        ref = common.read_audio(tc.ref_path(sp))
        ref_emb = speaker_embed.embed(ref)
        base = tc.VOICES[sp]
        es = grid_e or [round(base["exaggeration"] + d, 2) for d in (-0.1, 0.0, 0.15)]
        cs = grid_c or [round(base["cfg_weight"] + d, 2) for d in (-0.15, 0.0, 0.15)]
        print(f"\n=== {sp}  ({base['brief']})  reference median F0 {common.f0_stats(ref)['median']:.0f} Hz; target words/s {tc.RATE_TARGET[sp]}")
        for e in es:
            for c in cs:
                rows, t0 = [], time.time()
                for lid in SAMPLE_IDS[sp][:a.n]:
                    ln = lines[lid]
                    x = synth.raw(sp, ln["text"], seed=tts_lib.seed_for(lid), exaggeration=e, cfg_weight=c, tempo=1.0)
                    m = measure(sp, ln, x)
                    m["spk"] = round(float(speaker_embed.embed(x) @ ref_emb.T), 3) if len(x) > 0.6 * SR else 0.0
                    m["id"] = lid
                    rows.append(m)
                ok = [r for r in rows if r["wps"]]
                agg = dict(sim=np.mean([r["sim"] for r in rows]), wps=np.mean([r["wps"] for r in ok]) if ok else 0,
                           f0=np.median([r["f0"] for r in rows if r["f0"]]), spk=np.mean([r["spk"] for r in rows]),
                           inner=max(r["inner"] for r in rows), peak=max(r["peak"] for r in rows),
                           bad=sum(1 for r in rows if r["sim"] < 0.9))
                results[f"{sp}/{e}/{c}"] = {"agg": {k: float(v) for k, v in agg.items()}, "rows": rows}
                print(f"  exag {e:4.2f} cfg {c:4.2f} temp {base['temperature']:.2f}: sim {agg['sim']:.3f} (bad {agg['bad']})  words/s {agg['wps']:.2f} "
                      f"(x tempo {base['tempo']:.2f} = {agg['wps'] * base['tempo']:.2f})  F0 {agg['f0']:.0f}  vs-ref {agg['spk']:.2f}  longest pause {agg['inner']:.2f}s  "
                      f"peak {agg['peak']:.2f}  [{time.time() - t0:.0f}s]")
    json.dump(results, open(os.path.join(tc.VOICES_DIR, "tts_tune.json"), "w"), indent=1)


# ====================================================================================== render
def cmd_render(a):
    import asr
    synth = tts_lib.Synth()
    want = set(a.ids.split(",")) if a.ids else None
    sps = [a.speaker.upper()] if a.speaker else HUMANS
    done = bad = 0
    t_all = time.time()
    for sp in sps:
        d = os.path.join(tc.RAW_TTS_DIR, sp)
        os.makedirs(d, exist_ok=True)
        rp = os.path.join(d, "_report.json")
        rep = json.load(open(rp)) if os.path.exists(rp) else {}
        for ln in [l for l in human_lines() if l["speaker"] == sp]:
            lid = ln["id"]
            if want and lid not in want:
                continue
            dst = os.path.join(d, lid + ".wav")
            if os.path.exists(dst) and not a.force and not want and lid in rep:
                continue
            t0 = time.time()
            if ln["nonverbal"]:
                x = tts_lib.breath_in()
                common.write_wav(dst, x)
                rep[lid] = dict(nonverbal=True, tries=0, sim=1.0, dur=round(len(x) / SR, 2), heard="")
                print(f"{sp:8} {lid:5} breath (made from noise)  {len(x) / SR:.1f}s")
                continue
            nw = len(tts_lib.canon(ln["text"]))
            best, tried = None, []
            for k in range(a.tries if nw > 2 else max(a.tries, 24)):           # (a single word is the weak spot of the model: more seeds)
                x = synth.raw(sp, ln["text"], seed=tts_lib.seed_for(lid, k))
                m = measure(sp, ln, x)
                sc = take_score(m, nw, sp)
                tried.append((k, round(sc, 3), m["heard"]))
                if best is None or sc > best[0]:
                    best = (sc, x, m, k)
                need = tc.ASR_GOOD if nw > 3 else 0.999
                if sc >= need and m["inner"] <= tc.MAX_INNER_SILENCE_S and m["peak"] < tc.PEAK_MAX:
                    break
            sc, x, m, k = best
            common.write_wav(dst, x)
            rep[lid] = dict(tries=len(tried), seed=k, sim=m["sim"], score=round(sc, 3), heard=m["heard"], dur=m["dur"], speech=m["speech"], wps=m["wps"],
                            f0=m["f0"], inner=m["inner"], peak=m["peak"], text=ln["text"])
            poor = m["sim"] < tc.ASR_GOOD
            bad += poor
            done += 1
            print(f"{sp:8} {lid:5} {m['dur']:5.1f}s  sim {m['sim']:.2f} after {len(tried)} take(s)  {m['wps']:.1f} w/s  F0 {m['f0']:4.0f}  "
                  f"pause {m['inner']:.1f}s  ({time.time() - t0:.1f}s){'  CHECK: heard ' + repr(m['heard']) if poor else ''}")
            json.dump(rep, open(rp, "w"), indent=1)
        json.dump(rep, open(rp, "w"), indent=1)
    print(f"\n{done} lines rendered, {bad} below the transcript threshold, {time.time() - t_all:.0f}s")


# ====================================================================================== backup, install
def cmd_backup(a):
    pack_line = os.path.join(common.PACK_DIR, "assets", "angel", "sounds", "line")
    moves = []
    for sp in HUMANS:
        moves.append((os.path.join(common.FINAL_DIR, sp), os.path.join(tc.BACKUP_DIR, "final", sp)))
        moves.append((os.path.join(pack_line, sp.lower()), os.path.join(tc.BACKUP_DIR, "pack_sounds_line", sp.lower())))
    for extra in ("durations.json",):
        pass
    moved = 0
    for src, dst in moves:
        if not os.path.isdir(src):
            print(f"   (nothing at {src})")
            continue
        if os.path.exists(dst):
            sys.exit(f"{dst} already exists: refusing to overwrite a backup")
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.move(src, dst)
        moved += 1
        print(f"moved {src}\n   -> {dst}")
    # the sounds.json and durations.json as they were (copies: pack_sounds rewrites both)
    sj = os.path.join(common.PACK_DIR, "assets", "angel", "sounds.json")
    for src, name in ((sj, "sounds.json.before"), (common.DURATIONS_JSON, "durations.json.before")):
        dst = os.path.join(tc.BACKUP_DIR, name)
        if os.path.exists(src) and not os.path.exists(dst):
            shutil.copy2(src, dst)
    print(f"{moved} folders moved into {tc.BACKUP_DIR}")


def cmd_install(a):
    sps = [a.speaker.upper()] if a.speaker else HUMANS
    out = common.FINAL_DIR
    n = 0
    for sp in sps:
        for ln in [l for l in human_lines() if l["speaker"] == sp]:
            src = os.path.join(tc.RAW_TTS_DIR, sp, ln["id"] + ".wav")
            if not os.path.exists(src):
                print(f"   missing take for {ln['id']} ({sp}): run render")
                continue
            raw = common.read_audio(src)
            y = tts_lib.master(sp, raw, ln["direction"], ln["nonverbal"])
            common.write_wav(final_path(sp, ln["id"], out), y)
            n += 1
    print(f"{n} finished lines written under {out}")
    if not a.no_pack:
        import subprocess
        subprocess.run([sys.executable, os.path.join(HERE, "pack_sounds.py")] + (["--speaker", ",".join(sps)] if a.speaker else []), check=True)


# ====================================================================================== audition and report
AUDITION_IDS = {"MISATO": ["1.04", "3.09", "5.34"], "RITSUKO": ["4.16", "5.14", "7.17"], "GENDO": ["5.05", "5.20", "5.26"], "REI": ["5.36", "5.37", "5.39"]}


def cmd_audition(a):
    os.makedirs(tc.AUDITION_DIR, exist_ok=True)
    lines = {l["id"]: l for l in human_lines()}
    gap = np.zeros(int(0.9 * SR), np.float32)
    for sp in HUMANS:
        parts = []
        for lid in AUDITION_IDS[sp]:
            src = os.path.join(tc.RAW_TTS_DIR, sp, lid + ".wav")
            if not os.path.exists(src):
                sys.exit(f"{src} missing: run render first")
            # the audition is the dry voice (no transmission effect) at the finished loudness, so the voice itself can be judged
            y = tts_lib.master(sp, common.read_audio(src), "", False)
            parts += [y, gap]
        out = os.path.join(tc.AUDITION_DIR, f"{sp}.wav")
        common.write_wav(out, np.concatenate(parts))
        print(f"{out}  ({', '.join(AUDITION_IDS[sp])})")
    # and each character on the radio / from above, as it is heard in the game
    for sp, lid in (("MISATO", "6.19"), ("GENDO", "5.20"), ("RITSUKO", "2.13")):
        src = os.path.join(tc.RAW_TTS_DIR, sp, lid + ".wav")
        if os.path.exists(src):
            y = tts_lib.master(sp, common.read_audio(src), lines[lid]["direction"], False)
            common.write_wav(os.path.join(tc.AUDITION_DIR, f"{sp}__{lines[lid]['direction'].replace(' ', '_').replace(',', '')}.wav"), y)


def cmd_rescore(a):
    """Recompute every take's transcript similarity from the stored transcript with the current word normaliser (no synthesis); print what is still below the threshold."""
    low = []
    for sp in HUMANS:
        rp = os.path.join(tc.RAW_TTS_DIR, sp, "_report.json")
        if not os.path.exists(rp):
            continue
        rep = json.load(open(rp))
        for lid, r in rep.items():
            if r.get("nonverbal") or "text" not in r:
                continue
            r["sim"] = round(tts_lib.similarity(r["text"], r.get("heard", "")), 3)
            if r["sim"] < tc.ASR_GOOD:
                low.append((sp, lid, r["sim"], r["text"], r.get("heard", "")))
        json.dump(rep, open(rp, "w"), indent=1)
    print(f"{len(low)} takes below {tc.ASR_GOOD}:")
    for sp, lid, s, t, h in low:
        print(f"  {sp:8} {lid:5} {s:.2f}  want {t!r}\n{'':24}heard {h!r}")
    if low:
        print("re-roll them with:  tts_lines.py render --force --ids " + ",".join(l[1] for l in low) + "  (per speaker if the ids clash)")


def cmd_report(a):
    import speaker_embed
    lines = {l["id"]: l for l in human_lines()}
    per = {sp: [] for sp in HUMANS}
    emb = {sp: [] for sp in HUMANS}
    rp = {}
    for sp in HUMANS:
        p = os.path.join(tc.RAW_TTS_DIR, sp, "_report.json")
        rp[sp] = json.load(open(p)) if os.path.exists(p) else {}
        for lid, r in rp[sp].items():
            src = os.path.join(tc.RAW_TTS_DIR, sp, lid + ".wav")
            if r.get("nonverbal") or not os.path.exists(src):
                continue
            x = common.read_audio(src)
            per[sp].append(dict(id=lid, f0=r["f0"], wps=r["wps"], sim=r["sim"], inner=r["inner"], peak=r["peak"], dur=r["dur"]))
            if len(x) > 1.5 * SR:
                emb[sp].append(speaker_embed.embed(x))
    print(f"{'':8} {'lines':>5} {'ASR>=.97':>8} {'median F0':>9} {'words/s':>8} {'target':>10} {'longest pause':>13} {'peak':>6}")
    med = {}
    for sp in HUMANS:
        rows = per[sp]
        if not rows:
            continue
        med[sp] = float(np.median([r["f0"] for r in rows if r["f0"]]))
        w = float(np.median([r["wps"] for r in rows if r["wps"]]))
        good = sum(1 for r in rows if r["sim"] >= tc.ASR_GOOD)
        print(f"{sp:8} {len(rows):5} {good:8} {med[sp]:9.0f} {w:8.2f} {str(tc.RATE_TARGET[sp]):>10} {max(r['inner'] for r in rows):13.2f} {max(r['peak'] for r in rows):6.2f}")
    order = sorted(med, key=lambda s: -med[s])
    print("pitch order (high to low):", " > ".join(order), "  expected:", " > ".join(tc.PITCH_ORDER), "  OK" if order == tc.PITCH_ORDER else "  DIFFERENT")
    cen = {sp: np.mean(emb[sp], axis=0) for sp in HUMANS if emb[sp]}
    cen = {k: v / np.linalg.norm(v) for k, v in cen.items()}
    print("\nspeaker similarity between the characters (mean voice of each; different people want < %.2f):" % tc.SIM_DISTINCT)
    print(" " * 9 + "".join(f"{s:>9}" for s in cen))
    for a_ in cen:
        print(f"{a_:9}" + "".join(f"{float(cen[a_] @ cen[b_]):9.2f}" for b_ in cen))
    print("\nconsistency inside a character (mean cosine of each line's voice to the character's mean voice; want > %.2f):" % tc.SIM_SAME)
    cons = {}
    for sp in cen:
        v = [float(e @ cen[sp]) for e in emb[sp]]
        cons[sp] = (float(np.mean(v)), float(min(v)))
        print(f"  {sp:8} mean {np.mean(v):.2f}  lowest {min(v):.2f}")
    # the finished lines (effects and loudness applied) as they sit in voices\final
    print("\nthe finished lines (voices\\final): loudness, peak, clipping, durations")
    fin = {}
    for sp in HUMANS:
        d = os.path.join(common.FINAL_DIR, sp)
        L, Pk, clip, dur = [], [], 0, []
        for f in sorted(os.listdir(d)) if os.path.isdir(d) else []:
            if f.endswith(".wav") and not f.startswith("_"):
                x = common.read_audio(os.path.join(d, f))
                L.append(common.lufs(x))
                Pk.append(common.peak_db(x))
                clip += int((np.abs(x) >= 0.999).sum())
                dur.append(len(x) / SR)
        if L:
            fin[sp] = dict(n=len(L), lufs_min=min(L), lufs_median=float(np.median(L)), lufs_max=max(L), peak_db_max=max(Pk), clipped_samples=clip,
                           seconds=sum(dur), longest_s=max(dur))
            print(f"  {sp:8} {len(L):3d} lines  LUFS {min(L):.1f} / {np.median(L):.1f} / {max(L):.1f}  highest peak {max(Pk):.2f} dB  clipped samples {clip}  {sum(dur):.0f} s of speech")
    out = dict(per_speaker={sp: dict(lines=len(per[sp]), median_f0=med.get(sp), median_words_per_s=float(np.median([r["wps"] for r in per[sp] if r["wps"]])) if per[sp] else None,
                                     target_words_per_s=tc.RATE_TARGET[sp], longest_pause_s=max((r["inner"] for r in per[sp]), default=0),
                                     asr_ok=sum(1 for r in per[sp] if r["sim"] >= tc.ASR_GOOD)) for sp in HUMANS},
               pitch_order=order, pitch_order_expected=tc.PITCH_ORDER,
               speaker_similarity={a_: {b_: round(float(cen[a_] @ cen[b_]), 3) for b_ in cen} for a_ in cen},
               consistency={k: dict(mean=round(v[0], 3), lowest=round(v[1], 3)) for k, v in cons.items()}, finished=fin,
               settings={sp: tc.VOICES[sp] for sp in HUMANS}, refs=json.load(open(os.path.join(tc.REFS_DIR, "refs.json"))) if os.path.exists(os.path.join(tc.REFS_DIR, "refs.json")) else {})
    json.dump(out, open(tc.REPORT_JSON, "w"), indent=1, default=float)
    print(f"\nreport: {tc.REPORT_JSON}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("refs")
    p.add_argument("--speaker")
    p = sub.add_parser("tune")
    p.add_argument("--speaker")
    p.add_argument("--n", type=int, default=8)
    p.add_argument("--exaggeration", help="comma list")
    p.add_argument("--cfg", help="comma list")
    p = sub.add_parser("render")
    p.add_argument("--speaker")
    p.add_argument("--ids")
    p.add_argument("--force", action="store_true")
    p.add_argument("--tries", type=int, default=tc.TRIES)
    sub.add_parser("backup")
    p = sub.add_parser("install")
    p.add_argument("--speaker")
    p.add_argument("--no-pack", action="store_true")
    sub.add_parser("audition")
    sub.add_parser("report")
    sub.add_parser("rescore")
    a = ap.parse_args()
    {"refs": cmd_refs, "tune": cmd_tune, "render": cmd_render, "backup": cmd_backup, "install": cmd_install,
     "audition": cmd_audition, "report": cmd_report, "rescore": cmd_rescore}[a.cmd](a)


if __name__ == "__main__":
    main()


