"""Cut one long reading of a character's sheet into one clean file per line.

    python cut_takes.py <reading.wav> --speaker MISATO
    python cut_takes.py <pickups.wav> --speaker MISATO --ids 2.01,5.07      # re-recorded lines only (merges into the report)

The reading is the user going through recording\\<SPEAKER>.md top to bottom, with pauses, flubs and repeated
takes.  What happens:
  1. Silero VAD finds the stretches of speech; neighbouring stretches are grouped (never cut inside speech).
  2. faster-whisper (large-v3, GPU) transcribes each group with word timestamps.  Cached in _words.json.
  3. Every script line of this character is searched for in the word stream (fuzzy, spelling-tolerant), giving
     all the takes of it that were heard, each with a similarity score.
  4. A monotone alignment (dynamic programming) picks, line by line in script order, the LAST take that scores
     as good (>= --good); if there is none, the best one that is at least --low and flags it for re-recording.
     Distinctive lines that were re-read later in the session out of order are also picked up.
  5. Each chosen take is cut at the quietest point between it and its neighbours, trimmed, and written to
        D:\\angel-attack\\voices\\raw\\<SPEAKER>\\<id>.wav     (mono, 48 kHz, 24 bit)
  6. _report.md / _report.json next to them list missing and low-confidence lines and everything else that was heard.
Non-verbal lines (a breath, no words) cannot be matched by text; they are taken positionally (the last
sound between the neighbouring lines) and always flagged to be checked by ear.
"""
import argparse
import difflib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import common
import script_lines
from common import SR

# ---------------------------------------------------------------------------------------- text
_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen " \
        "seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def num_words(n):
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    if n < 1000:
        return _ONES[n // 100] + " hundred" + ("" if n % 100 == 0 else " " + num_words(n % 100))
    if n < 1000000:
        return num_words(n // 1000) + " thousand" + ("" if n % 1000 == 0 else " " + num_words(n % 1000))
    return str(n)


def norm_tokens(text):
    """Lower-case word tokens, digits spelled out, punctuation and apostrophes gone."""
    t = text.lower().replace("\u2019", "'").replace("\u2018", "'").replace("%", " percent ")
    t = re.sub(r"(\d+)\.(\d+)", lambda m: f"{m.group(1)} point {' '.join(m.group(2))}", t)
    t = re.sub(r"\d+", lambda m: num_words(int(m.group(0))), t)
    t = t.replace("'", "").replace("-", " ").replace("\u2014", " ")
    return re.findall(r"[a-z]+", t)


def glossary(lines):
    """Proper nouns / acronyms in the sheet, to bias Whisper's spelling."""
    cap, low = {}, set()
    for l in lines:
        for m in re.finditer(r"[A-Za-z][A-Za-z']+", l["text"]):
            w = m.group(0)
            if w.isupper() and len(w) > 1:
                cap[w] = True
            elif w[0].isupper() and m.start() > 0 and l["text"][:m.start()].rstrip()[-1:] not in ".!?:\u2014\"":
                cap[w] = True
            if w.islower():
                low.add(w)
    names = [w for w in cap if w.lower() not in low or w.isupper()]
    return ", ".join(sorted(set(names))[:50])


# ---------------------------------------------------------------------------------------- speech -> words
def vad_chunks(x16):
    import torch
    from silero_vad import get_speech_timestamps, load_silero_vad
    model = load_silero_vad()
    ts = get_speech_timestamps(torch.from_numpy(x16), model, sampling_rate=16000, threshold=0.40,
                               min_speech_duration_ms=120, min_silence_duration_ms=300, speech_pad_ms=120,
                               return_seconds=True)
    return [(t["start"], t["end"]) for t in ts]


def groups_of(chunks, max_gap=1.2, max_len=27.0):
    groups = []
    for s, e in chunks:
        if groups and s - groups[-1][1] <= max_gap and e - groups[-1][0] <= max_len:
            groups[-1][1] = e
        else:
            groups.append([s, e])
    return groups


def transcribe_words(x16, chunks, prompt, model_name):
    import asr
    if model_name != "large-v3":
        import common as c
        c.setup_torch_dlls()
        from faster_whisper import WhisperModel
        asr._model = WhisperModel(model_name, device="cuda", compute_type="float16")
    words = []
    gs = groups_of(chunks)
    for n, (s, e) in enumerate(gs, 1):
        a, b = max(0.0, s - 0.3), min(len(x16) / 16000, e + 0.3)
        seg = x16[int(a * 16000):int(b * 16000)]
        _, segs = asr.transcribe(seg, 16000, word_timestamps=True, initial_prompt=prompt or None)
        for sg in segs:
            for w in (sg.words or []):
                toks = norm_tokens(w.word)
                if not toks:
                    continue
                ws, we = a + w.start, a + w.end
                step = (we - ws) / len(toks)
                for k, t in enumerate(toks):
                    words.append((t, round(ws + k * step, 3), round(ws + (k + 1) * step, 3), round(float(w.probability), 3)))
        if n % 10 == 0 or n == len(gs):
            print(f"  transcribed {n}/{len(gs)} groups", flush=True)
    words.sort(key=lambda w: w[1])
    return words


def get_words(path, x16, prompt, model_name, cache_dir, redo):
    cache = os.path.join(cache_dir, "_words.json")
    st = os.stat(path)
    key = {"src": os.path.abspath(path), "size": st.st_size, "mtime": int(st.st_mtime), "model": model_name}
    if os.path.exists(cache) and not redo:
        c = json.load(open(cache, encoding="utf-8"))
        if c.get("key") == key:
            print(f"using cached transcription ({len(c['words'])} words)")
            return [tuple(w) for w in c["words"]], [tuple(v) for v in c["chunks"]]
    t0 = time.time()
    chunks = vad_chunks(x16)
    print(f"VAD: {len(chunks)} speech stretches, {sum(e - s for s, e in chunks):.0f}s of speech in {len(x16) / 16000:.0f}s")
    words = transcribe_words(x16, chunks, prompt, model_name)
    print(f"{len(words)} words heard ({time.time() - t0:.0f}s)")
    os.makedirs(cache_dir, exist_ok=True)
    json.dump({"key": key, "words": words, "chunks": chunks}, open(cache, "w", encoding="utf-8"))
    return words, chunks


# ---------------------------------------------------------------------------------------- matching
def tok_sim(a, b):
    return difflib.SequenceMatcher(None, a, b).ratio()


def candidates(line_toks, words, min_score=0.55, max_inner_gap=3.5):
    """All non-overlapping places in the word stream that resemble the line: (i, j, score), j exclusive."""
    n = len(line_toks)
    target = " ".join(line_toks)
    sm = difflib.SequenceMatcher(None, autojunk=False)
    sm.set_seq2(target)
    toks = [w[0] for w in words]
    heads = line_toks[:2] if n > 1 else line_toks[:1]
    cands = []
    for i in range(len(words)):
        if not any(tok_sim(toks[i], h) >= 0.72 for h in heads):
            continue
        best = None
        gap_ok = True
        for m in range(max(1, int(0.55 * n)), int(1.5 * n) + 3):
            j = i + m
            if j > len(words):
                break
            if m > 1 and words[j - 1][1] - words[j - 2][2] > max_inner_gap:
                break
            sm.set_seq1(" ".join(toks[i:j]))
            r = sm.ratio()
            if best is None or r > best[0] + 1e-9 or (abs(r - best[0]) < 1e-9 and abs(m - n) < abs(best[1] - n)):
                best = (r, m)
        if best and best[0] >= min_score:
            cands.append((i, i + best[1], best[0]))
    cands.sort(key=lambda c: -c[2])
    kept = []
    for c in cands:
        if all(c[1] <= k[0] or c[0] >= k[1] for k in kept):
            kept.append(c)
    kept.sort()
    return kept


def pick(per_line, words, good, low, tol=0.25):
    """Monotone dynamic programming over the lines.  per_line[k] = list of (i, j, score)."""
    states = []                              # (k, cand, quality, start_time, end_time)
    for k, cs in enumerate(per_line):
        goods = sorted((c for c in cs if c[2] >= good), key=lambda c: words[c[0]][1])
        for c in cs:
            if c[2] >= good:
                q = 1.0 + min(0.1, 0.02 * goods.index(c))        # later good takes win ties
            elif c[2] >= low:
                q = 0.5 * c[2]
            else:
                continue
            states.append((k, c, q, words[c[0]][1], words[c[1] - 1][2]))
    best = [0.0] * len(states)
    back = [-1] * len(states)
    for a, (k, c, q, s, e) in enumerate(states):
        bv, bb = 0.0, -1
        for b in range(a):
            kb, _, _, _, eb = states[b]
            if kb < k and eb <= s + tol and best[b] > bv:
                bv, bb = best[b], b
        best[a], back[a] = q + bv, bb
    chosen = {}
    if states:
        a = int(np.argmax(best))
        while a >= 0:
            chosen[states[a][0]] = states[a][1]
            a = back[a]
    return chosen


# ---------------------------------------------------------------------------------------- cutting
def quietest(db, a, b, win=0.06):
    """Time of the quietest `win` seconds between a and b (db has 10 ms frames)."""
    lo, hi = int(a * 100), int(b * 100)
    k = max(1, int(win * 100))
    if hi - lo <= k:
        return (a + b) / 2
    sums = np.convolve(db[lo:hi], np.ones(k), mode="valid")
    return (lo + int(np.argmin(sums)) + k / 2) / 100


def cut_one(x, db, words, c, total):
    i, j = c[0], c[1]
    s0, e0 = words[i][1], words[j - 1][2]
    prev_end = words[i - 1][2] if i > 0 else 0.0
    next_start = words[j][1] if j < len(words) else total
    lo = max(0.0, s0 - 0.20)
    hi = min(total, e0 + 0.35)
    if prev_end > lo:                                    # neighbours are close: split at the quietest point between
        lo = max(lo, quietest(db, prev_end, max(prev_end + 0.05, s0)) if s0 - prev_end > 0.12 else (prev_end + s0) / 2)
    if next_start < hi:
        hi = min(hi, quietest(db, e0, max(e0 + 0.05, next_start)) if next_start - e0 > 0.12 else (e0 + next_start) / 2)
    y = x[int(lo * SR):int(hi * SR)]
    return common.trim_silence(y, SR, thresh_db=-50, lead=0.10, tail=0.25, fade=0.010), lo, hi


def nonverbal_segment(x, db, words, lo, hi, taken):
    """Last stretch of sound between lo and hi that no word and no other take occupies."""
    if hi - lo < 0.3:
        return None
    floor = np.percentile(db, 10)
    act = db > floor + 12
    spans, s = [], None
    a, b = int(lo * 100), min(int(hi * 100), len(db))
    for f in range(a, b):
        t = f / 100
        busy = any(w[1] - 0.12 <= t <= w[2] + 0.12 for w in words if w[3] >= 0.2) or any(u <= t <= v for u, v in taken)
        if act[f] and not busy:
            s = f if s is None else s
        elif s is not None:
            spans.append((s / 100, f / 100))
            s = None
    if s is not None:
        spans.append((s / 100, b / 100))
    spans = [sp for sp in spans if sp[1] - sp[0] >= 0.25]
    return spans[-1] if spans else None


def flags_for(y, text, dur_med):
    f = []
    if int((np.abs(y) >= 0.999).sum()) >= 3:
        f.append("clipped")
    elif common.peak_db(y) > -0.1:
        f.append("peaks at full scale (may be clipped)")
    if common.peak_db(y) < -30:
        f.append("very quiet")
    db = common.frame_db(y)
    if len(db) > 20 and np.percentile(db, 90) - np.percentile(db, 10) < 18:
        f.append("noisy or no clear pauses (low dynamic range)")
    if text and dur_med and len(text.split()) >= 4:
        cps = len(text) / max(len(y) / SR, 0.1)
        if cps > 2.4 * dur_med or cps < dur_med / 2.6:
            f.append("pace is odd for its length")
    return f


# ---------------------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("wav")
    ap.add_argument("--speaker", required=True, choices=common.SPEAKERS)
    ap.add_argument("--script", default=common.SCRIPT_MD)
    ap.add_argument("--out", default=common.RAW_DIR, help="raw folder (default D:\\angel-attack\\voices\\raw)")
    ap.add_argument("--ids", help="only these lines (pick-up session); the report is merged with the previous one")
    ap.add_argument("--good", type=float, default=0.90, help="similarity at or above which a take counts as good")
    ap.add_argument("--low", type=float, default=0.70, help="below this a take is not used at all")
    ap.add_argument("--keep-alts", action="store_true", help="also save earlier takes as _alt\\<id>_<n>.wav")
    ap.add_argument("--redo-asr", action="store_true", help="ignore the cached transcription")
    ap.add_argument("--model", default="large-v3")
    ap.add_argument("--dry-run", action="store_true", help="match and report, write no wav files")
    a = ap.parse_args()

    sp = a.speaker
    allines = [l for l in script_lines.parse(a.script) if l["speaker"] == sp]
    if not allines:
        sys.exit(f"no lines for {sp} in {a.script}")
    sel = set(a.ids.split(",")) if a.ids else None
    lines = [l for l in allines if not sel or l["id"] in sel]
    out = os.path.join(a.out, sp)
    os.makedirs(out, exist_ok=True)

    print(f"{sp}: {len(lines)} lines to find in {a.wav}")
    x = common.read_audio(a.wav, SR)
    x16 = common.resample(x, SR, 16000)
    total = len(x) / SR
    db = common.frame_db(x)
    words, chunks = get_words(a.wav, x16, glossary(allines), a.model, out, a.redo_asr)
    words = [w for w in words if w[3] >= 0.03]               # Whisper inventing words out of breaths and noise has ~0 confidence

    verbal = [l for l in lines if not l["nonverbal"]]
    ltoks = [norm_tokens(l["text"]) for l in verbal]
    per_line = []
    for l, lt in zip(verbal, ltoks):
        per_line.append(candidates(lt, words) if lt else [])
    chosen = pick(per_line, words, a.good, a.low)

    # distinctive lines re-read later, out of order: take their last good take
    sheet_toks = [norm_tokens(l["text"]) for l in allines if not l["nonverbal"]]
    for k, l in enumerate(verbal):
        me = " ".join(ltoks[k])
        distinct = len(ltoks[k]) >= 4 or sum(1 for t in sheet_toks if " ".join(t) == me) == 1
        distinct = distinct and not any(" ".join(t) != me and tok_sim(" ".join(t), me) >= 0.8 for t in sheet_toks)
        if not distinct:
            continue
        cur = chosen.get(k)
        later = [c for c in per_line[k] if c[2] >= a.good and (cur is None or words[c[0]][1] > words[cur[0]][1])]
        later = [c for c in later if not any(o != k and not (c[1] <= oc[0] or c[0] >= oc[1]) for o, oc in chosen.items())]
        if later:
            chosen[k] = max(later, key=lambda c: words[c[0]][1])

    # lines Whisper could not recognise (typically one-word lines like "Why?"): if exactly one stray stretch of speech
    # sits where the line should be (between its neighbours' takes) and resembles no other line, take it, flagged low
    positional = set()
    used = {i for c in chosen.values() for i in range(c[0], c[1])}
    all_texts = [" ".join(t) for t in sheet_toks]
    for k, l in enumerate(verbal):
        if k in chosen or not ltoks[k]:
            continue
        prev_end = max([words[chosen[q][1] - 1][2] for q in range(k) if q in chosen][-1:] or [0.0])
        next_start = min([words[chosen[q][0]][1] for q in range(k + 1, len(verbal)) if q in chosen][:1] or [total])
        runs, cur = [], []
        for i, w in enumerate(words):
            if i in used or w[1] < prev_end - 0.1 or w[2] > next_start + 0.1:
                if cur:
                    runs.append(cur)
                    cur = []
                continue
            if cur and w[1] - words[cur[-1]][2] > 0.8:
                runs.append(cur)
                cur = []
            cur.append(i)
        if cur:
            runs.append(cur)
        me, n = " ".join(ltoks[k]), len(ltoks[k])
        good_runs = []
        for r in runs:
            txt = " ".join(words[i][0] for i in r)
            if not (max(1, int(0.5 * n) - 1) <= len(r) <= 2 * n + 2):
                continue
            if any(o != me and (o == txt or o.startswith(txt + " ") or (len(r) >= 3 and tok_sim(txt, o) >= 0.6))
                   for o in all_texts):
                continue
            good_runs.append(r)
        if good_runs:
            r = good_runs[-1]
            chosen[k] = (r[0], r[-1] + 1, round(tok_sim(" ".join(words[i][0] for i in r), me), 3))
            positional.add(k)
            used.update(r)

    # ---- cut and write
    taken =[(words[c[0]][1], words[c[1] - 1][2]) for c in chosen.values()]
    dur_cps = []
    for k, c in chosen.items():
        dur_cps.append(len(verbal[k]["text"]) / max(words[c[1] - 1][2] - words[c[0]][1], 0.1))
    cps_med = float(np.median(dur_cps)) if dur_cps else 0.0
    report = {}
    clips = {}
    for k, l in enumerate(verbal):
        cs = per_line[k]
        rec = {"id": l["id"], "text": l["text"], "direction": l["direction"], "takes_heard": sum(1 for c in cs if c[2] >= a.low)}
        c = chosen.get(k)
        if c is None:
            near = max(cs, key=lambda q: q[2]) if cs else None
            rec.update(status="missing", score=round(near[2], 3) if near else 0.0,
                       heard=" ".join(w[0] for w in words[near[0]:near[1]]) if near else "",
                       note="nothing close enough was heard" if not near else "closest match is below the threshold")
            report[l["id"]] = rec
            continue
        y, lo, hi = cut_one(x, db, words, c, total)
        heard = " ".join(w[0] for w in words[c[0]:c[1]])
        fl = flags_for(y, l["text"], cps_med)
        rec.update(status="ok" if c[2] >= a.good else "low", score=round(c[2], 3), heard=heard, start=round(lo, 2), end=round(hi, 2),
                   dur=round(len(y) / SR, 2), flags=fl)
        if k in positional:
            rec["status"] = "low"
            rec["flags"] = fl + ["taken by position (nothing matched the text); listen to it"]
        elif c[2] >= a.good and fl:
            rec["status"] = "check"
        clips[l["id"]] = y
        report[l["id"]] = rec
        if a.keep_alts:
            alts = sorted((q for q in cs if q[2] >= a.low and q != c), key=lambda q: words[q[0]][1])
            for n, q in enumerate(alts, 1):
                ya, _, _ = cut_one(x, db, words, q, total)
                if not a.dry_run:
                    common.write_wav(os.path.join(out, "_alt", f"{l['id']}_{n}.wav"), ya)
    # non-verbal lines, positionally, between the neighbouring verbal lines of the whole sheet
    order = [l["id"] for l in allines]
    for l in lines:
        if not l["nonverbal"]:
            continue
        pos = order.index(l["id"])
        prev_end = 0.0
        for q in range(pos - 1, -1, -1):
            r = report.get(order[q])
            if r and r.get("end") is not None:
                prev_end = r["end"]
                break
        next_start = total
        for q in range(pos + 1, len(order)):
            r = report.get(order[q])
            if r and r.get("start") is not None:
                next_start = r["start"]
                break
        seg = nonverbal_segment(x, db, words, prev_end, next_start, taken)
        rec = {"id": l["id"], "text": "", "direction": l["direction"], "takes_heard": 0}
        if seg is None:
            rec.update(status="missing", score=0.0, heard="", note="no sound found between the neighbouring lines")
        else:
            y = common.trim_silence(x[int(max(0, seg[0] - 0.15) * SR):int(min(total, seg[1] + 0.2) * SR)], SR, -50, 0.1, 0.2)
            clips[l["id"]] = y
            rec.update(status="check", score=0.0, heard="(non-verbal)", start=round(seg[0], 2), end=round(seg[1], 2),
                       dur=round(len(y) / SR, 2), flags=["non-verbal: taken by position, listen to it"])
        report[l["id"]] = rec

    if not a.dry_run:
        for lid, y in clips.items():
            common.write_wav(os.path.join(out, lid + ".wav"), y)

    # ---- report (merged with the previous one for pick-up sessions)
    jpath = os.path.join(out, "_report.json")
    merged = {}
    if sel and os.path.exists(jpath):
        merged = json.load(open(jpath, encoding="utf-8")).get("lines", {})
    merged.update(report)
    for l in allines:                                         # lines never found, but an earlier session left a file
        r = merged.get(l["id"])
        if r is None:
            merged[l["id"]] = r = {"id": l["id"], "text": l["text"], "direction": l["direction"], "status": "missing", "score": 0.0,
                                   "heard": "", "note": "not found", "takes_heard": 0}
        if r["status"] == "missing" and os.path.exists(os.path.join(out, l["id"] + ".wav")):
            r["status"] = "kept"
            r["note"] = "not in this recording; the file from an earlier session is kept"
    ordered = [merged[l["id"]] for l in allines if l["id"] in merged]
    covered = [(c[0], c[1]) for c in chosen.values()]
    extra = []                                                # speech that did not become a take
    used = {i for c in chosen.values() for i in range(c[0], c[1])}
    run = []
    for i, w in enumerate(words):
        if i in used:
            if run:
                extra.append(run)
                run = []
        else:
            if run and w[1] - words[run[-1]][2] > 1.2:
                extra.append(run)
                run = []
            run.append(i)
    if run:
        extra.append(run)
    unused = [{"at": round(words[r[0]][1], 1), "text": " ".join(words[i][0] for i in r)} for r in extra]
    json.dump({"speaker": sp, "source": os.path.abspath(a.wav), "good": a.good, "low": a.low, "lines": merged, "unused_speech": unused},
              open(jpath, "w", encoding="utf-8"), indent=1)
    counts = {}
    for r in ordered:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    md = [f"# {sp}: cut report", "", f"Source `{a.wav}`.  " + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())), ""]
    for title, st in (("Missing, record these again", ("missing",)), ("Low confidence, probably misread or cut off; listen",
                                                                   ("low",)), ("Check by ear", ("check",))):
        rs = [r for r in ordered if r["status"] in st]
        if rs:
            md += [f"## {title}", ""]
            for r in rs:
                md.append(f"- `{r['id']}` (score {r.get('score', 0):.2f}): {r['text'] or r['direction']}")
                if r.get("heard"):
                    md.append(f"    - heard: {r['heard']}")
                for f_ in r.get("flags", []) + ([r["note"]] if r.get("note") else []):
                    md.append(f"    - {f_}")
            md.append("")
    md += ["## All lines", "", "| id | status | score | takes heard | seconds |", "|---|---|---|---|---|"]
    for r in ordered:
        md.append(f"| {r['id']} | {r['status']} | {r.get('score', 0):.2f} | {r.get('takes_heard', 0)} | {r.get('dur', '')} |")
    if unused:
        md += ["", "## Speech that was not used (flubs, earlier takes, chatter)", ""]
        md += [f"- {u['at']}s: {u['text']}" for u in unused[:60]]
    open(os.path.join(out, "_report.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")

    print("\n" + ", ".join(f"{v} {k}" for k, v in sorted(counts.items())))
    for r in ordered:
        if r["status"] in ("missing", "low", "check"):
            print(f"  {r['status']:8} {r['id']:6} score {r.get('score', 0):.2f}  expected: {r['text'] or r['direction']!r}"
                  + (f"\n{'':20}heard:    {r['heard']!r}" if r.get("heard") else ""))
    print(f"\nreport: {os.path.join(out, '_report.md')}")


if __name__ == "__main__":
    main()
