"""evaluate.py - judge the finished candidates by evidence and draw the contact sheets.

    python evaluate.py                    # ASR + expectations + ranking for every candidate that has no verdict yet, then sheets
    python evaluate.py music. --redo      # redo these
    python evaluate.py --sheets-only

Per candidate (cand<k>.json is updated with an "asr" block and a "verdict" block):
  * speech: tools/voices/asr.py (faster-whisper large-v3, the project's helper) over the decoded file, once with its voice-activity filter
    and once without.  Any word found by the filtered pass, or two or more confident words from the plain pass, rejects the candidate.
  * contract failures from finish.py (level, peak, channels, samples, join, fades) reject it.
  * clipping, long silences (profile.longest_silence_s vs the event's expectation), steady narrow tonal lines in non-musical sounds
    (hum), and the event's own `expect` ranges from prompts.json (spectral/tempo/onset/dynamics profile vs the brief) cost points.
The best surviving candidate by score is "suggested"; the final pick is made after looking at the sheets (choices.json).
"""
import argparse
import json
import os
import sys

import numpy as np
from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio_utils as au
from audio_utils import SR

VOICES = os.path.join(au.ROOT, "tools", "voices")
SHEETS = os.path.join(au.CAND, "contact_sheets")


def prompts():
    return json.load(open(os.path.join(HERE, "prompts.json"), encoding="utf-8"))["events"]


def all_outputs(P):
    outs = []
    for ev, e in P.items():
        for o in e.get("outputs", [ev]):
            outs.append((o, ev))
    return outs


_asr = None


def asr_mod():
    global _asr
    if _asr is None:
        sys.path.insert(0, VOICES)
        import asr
        _asr = asr
    return _asr


def speech_check(path):
    asr = asr_mod()
    x = au.mono(au.read_pack(path))
    out = {}
    tv, sv = asr.transcribe(x, SR, vad=True)
    tn, sn = asr.transcribe(x, SR, vad=False)
    wv, wn = asr.words_of(tv), asr.words_of(tn)
    conf = [(s.text.strip(), round(float(s.avg_logprob), 2), round(float(s.no_speech_prob), 2)) for s in sn if asr.words_of(s.text)]
    confident = [c for c in conf if len(asr.words_of(c[0])) >= 2 and c[1] > -0.6 and c[2] < 0.5]
    out.update(vad_text=tv, plain_text=tn, plain_segments=conf[:6], vad_words=len(wv), plain_words=len(wn))
    out["reject"] = bool(wv) or bool(confident)
    out["note"] = "words found by the voice-activity pass" if wv else ("confident words in the plain pass" if confident else
                                                                  ("only low-confidence plain-pass text (probable hallucination on non-speech)" if wn else "no words"))
    return out


def judge(event, rec, e, asr_res):
    """returns (reject: bool, score: float, notes: list)"""
    notes = []
    score = 0.0
    p = rec["profile"]
    if rec["fail"]:
        return True, -99.0, ["contract: " + "; ".join(rec["fail"])]
    if asr_res and asr_res.get("reject"):
        return True, -98.0, ["speech: " + asr_res["note"] + f" ({asr_res['vad_text'] or asr_res['plain_text']!r})"]
    is_music = event.startswith("music.")
    for feat, (lo, hi) in e.get("expect", {}).items():
        v = p.get(feat)
        if v is None:
            continue
        if v < lo or v > hi:
            span = max(hi - lo, 1e-6) if hi < 1e8 else max(abs(lo), 1.0)
            miss = (lo - v) / span if v < lo else (v - hi) / span
            score -= 1.0 + min(2.0, miss)
            notes.append(f"{feat}={v} outside [{lo},{hi}]")
    if p["longest_silence_s"] > (0.3 if event.startswith("amb.") else 1.5) and not (event.startswith("sfx.") and p["longest_silence_s"] < 2.0):
        score -= 1.5
        notes.append(f"silence {p['longest_silence_s']} s")
    if not is_music and not e.get("tonal_ok"):          # a siren, a klaxon and a light pillar are SUPPOSED to be tones
        for prom, fr in p.get("tonal_lines", []):
            if prom > 24:
                score -= 2.0
                notes.append(f"steady tone line {fr} Hz (+{prom} dB)")
            elif prom > 20:
                score -= 0.7
                notes.append(f"tone line {fr} Hz (+{prom} dB)")
    if rec["warn"]:
        score -= 0.5 * len(rec["warn"])
        notes += rec["warn"]
    log = rec["log"]
    if log.get("aligned") is False or log.get("fallback"):
        score -= 2.0
        notes.append("tempo alignment failed: " + str(log.get("fallback", "")))
    lags = log.get("lag_ms")
    if lags and lags[-1] is not None and abs(lags[-1]) > 15:
        score -= 1.0
        notes.append(f"repeat lag {lags[-1]} ms")
    if "level" in log and log["level"].get("makeup_db", 0) > 10:
        score -= 0.5
        notes.append(f"limiter-heavy (makeup {log['level']['makeup_db']} dB)")
    if log.get("padded_s", 0) > 0.5:
        score -= 1.0
        notes.append(f"short generation, padded {log['padded_s']} s")
    return False, score, notes


def run_eval(names, redo, no_asr):
    P = prompts()
    summary = {}
    for out_ev, src_ev in all_outputs(P):
        if names and not any(out_ev == n or out_ev.startswith(n) for n in names):
            continue
        folder = os.path.join(au.CAND, out_ev)
        rows = []
        for k in range(1, 13):
            jp = os.path.join(folder, f"cand{k}.json")
            if not os.path.exists(jp):
                continue
            rec = json.load(open(jp))
            if redo or "asr" not in rec:
                rec["asr"] = None if no_asr else speech_check(os.path.join(au.ROOT, rec["file"]))
            reject, score, notes = judge(out_ev, rec, P[src_ev], rec["asr"])
            rec["verdict"] = dict(reject=reject, score=round(score, 2), notes=notes)
            json.dump(rec, open(jp, "w"), indent=1, default=float)
            rows.append((k, reject, score, notes))
        summary[out_ev] = rows
        ok = [r for r in rows if not r[1]]
        best = max(ok, key=lambda r: r[2])[0] if ok else None
        print(f"{out_ev:24s} suggested: {best}   " + " | ".join(f"c{k}:{'REJ' if rj else f'{sc:.1f}'}" for k, rj, sc, _ in rows), flush=True)
        for k, rj, sc, notes in rows:
            if notes:
                print(f"      c{k}: " + "; ".join(notes)[:240])
    return summary


# ------------------------------------------------------------------------------------------------- sheets
def panel(x, label, width, color=(235, 235, 235), wf_h=46, sp_h=96):
    import analyze
    sp = Image.fromarray(analyze.spectrogram(x, width, height=sp_h))
    wf = analyze.waveform(x, width, height=wf_h)
    img = Image.new("RGB", (width, 16 + wf_h + sp_h), (0, 0, 0))
    d = ImageDraw.Draw(img)
    d.text((4, 2), label, fill=color, font=analyze.font(12))
    img.paste(wf, (0, 16))
    img.paste(sp, (0, 16 + wf_h))
    return img


def event_sheet(out_ev, chosen=None, width=800):
    ref = au.read_pack(au.ref_path(out_ev))
    panels = [panel(ref, f"{out_ev}  PROCEDURAL  {len(ref) / SR:.1f}s  {au.lufs(ref):.1f} LUFS", width, (255, 210, 120))]
    for k in range(1, 13):
        jp = os.path.join(au.CAND, out_ev, f"cand{k}.json")
        if not os.path.exists(jp):
            continue
        rec = json.load(open(jp))
        y = au.read_pack(os.path.join(au.ROOT, rec["file"]))
        v = rec.get("verdict", {})
        tag = "REJECTED" if v.get("reject") else f"score {v.get('score', 0):.1f}"
        mark = "  <== INSTALL" if chosen == k else ""
        col = (255, 110, 110) if v.get("reject") else ((130, 255, 150) if chosen == k else (235, 235, 235))
        panels.append(panel(y, f"cand{k}  {tag}  {rec['contract']['lufs']:.1f} LUFS{mark}", width, col))
    H = sum(p.height + 3 for p in panels)
    img = Image.new("RGB", (width, H), (0, 0, 0))
    yy = 0
    for p in panels:
        img.paste(p, (0, yy))
        yy += p.height + 3
    return img


def make_sheets(names, choices):
    P = prompts()
    os.makedirs(SHEETS, exist_ok=True)
    made = []
    for out_ev, _ in all_outputs(P):
        if names and not any(out_ev == n or out_ev.startswith(n) for n in names):
            continue
        img = event_sheet(out_ev, choices.get(out_ev, {}).get("candidate") if choices else None)
        path = os.path.join(SHEETS, out_ev + ".png")
        img.save(path)
        made.append((out_ev, img))
    # overview pages: two events side by side
    by_family = {}
    for ev, img in made:
        by_family.setdefault(ev.split(".")[0], []).append((ev, img))
    for fam, items in by_family.items():
        for pg in range(0, len(items), 4):
            chunk = items[pg:pg + 4]
            cols = 2
            rows = (len(chunk) + 1) // 2
            hh = max(i[1].height for i in chunk)
            sheet = Image.new("RGB", (800 * cols + 4, (hh + 4) * rows), (30, 30, 30))
            for i, (ev, im) in enumerate(chunk):
                sheet.paste(im, ((i % cols) * 804, (i // cols) * (hh + 4)))
            sheet.save(os.path.join(SHEETS, f"_overview_{fam}_{pg // 4 + 1}.png"))
    return made


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("names", nargs="*")
    ap.add_argument("--redo", action="store_true")
    ap.add_argument("--no-asr", action="store_true")
    ap.add_argument("--sheets-only", action="store_true")
    a = ap.parse_args()
    if not a.sheets_only:
        run_eval(a.names, a.redo, a.no_asr)
    cp = os.path.join(HERE, "installed.json")
    choices = {}
    if os.path.exists(cp):
        choices = json.load(open(cp)).get("events", {})
    make_sheets(a.names, choices)
    print("sheets in", SHEETS)


if __name__ == "__main__":
    main()
