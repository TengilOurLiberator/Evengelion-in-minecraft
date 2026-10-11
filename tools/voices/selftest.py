"""End-to-end self-test of the pipeline on a made-up session (no real recording needed).

    python selftest.py [--keep]

It builds a small fixture script (Genesis verses standing in for lines) and a long "reading" from the user's dry
Genesis clips with the things a real session has: pauses, a flub, a repeated take, a skipped line, a non-verbal
sound and a late out-of-order retake.  Then it runs cut_takes -> transform -> pack_sounds into a temporary folder
and checks the results.  Nothing under D:\\angel-attack\\voices or the pack is touched.
"""
import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np

import common
from common import SR

PY = sys.executable
VERSES = {"1:1": "1.01", "1:3": "1.02", "1:4": "1.03", "1:5": "1.04", "1:6": "1.05", "1:7": "1.06", "1:9": "1.07", "1:10": "1.08"}
DIRS = {"1.03": "radio", "1.06": "telephone"}


def verse_text():
    t = {}
    for line in open(r"D:\genesis-vr\narration-script.md", encoding="utf-8"):
        m = re.match(r"\*\*(\d+:\d+)\*\*\s+(.*)", line.strip())
        if m:
            t[m.group(1)] = m.group(2)
    return t


def run(*args):
    print("\n$", " ".join(os.path.basename(a) if os.sep in a and len(a) > 60 else a for a in args))
    r = subprocess.run([PY, "-W", "ignore", *args], cwd=HERE)
    if r.returncode:
        sys.exit(f"step failed with exit code {r.returncode}")


def real_sheet(speaker, tmp):
    """Read a REAL sheet of script.md with Chatterbox's built-in synthetic voice (no real person), with flubs,
    repeats and one skipped line, and check that cut_takes finds the right takes."""
    import logging
    import warnings
    warnings.filterwarnings("ignore")
    logging.getLogger("chatterbox").setLevel(logging.ERROR)
    import torch
    import script_lines
    from chatterbox.tts import ChatterboxTTS
    lines = [l for l in script_lines.parse(common.SCRIPT_MD) if l["speaker"] == speaker]
    tts = ChatterboxTTS.from_pretrained("cuda")
    rng = np.random.default_rng(3)
    room = lambda s: (rng.standard_normal(int(s * SR)) * 0.0015).astype(np.float32)
    parts, where, expect, t = [room(3.0)], {}, {}, 3.0

    def add(y, gap):
        nonlocal t
        parts.extend([y, room(gap)])
        t += (len(y) + int(gap * SR)) / SR

    skip = lines[2]["id"] if len(lines) > 3 else None
    for k, l in enumerate(lines):
        if l["id"] == skip:
            expect[l["id"]] = "missing"
            continue
        if l["nonverbal"]:
            n = int(0.9 * SR)
            where.setdefault(l["id"], []).append(t)
            add((rng.standard_normal(n) * np.hanning(n) * 0.03).astype(np.float32), 2.2)
            expect[l["id"]] = "check"
            continue
        torch.manual_seed(100 + k)
        y = common.resample(tts.generate(l["text"], exaggeration=0.5, cfg_weight=0.4).squeeze().cpu().numpy(), tts.sr, SR)
        y = y / max(1e-6, float(np.abs(y).max())) * 0.7
        if k % 4 == 1:
            add(y[: int(len(y) * 0.45)], 1.8)                      # a flub, then start over
        if k % 7 == 3:
            where.setdefault(l["id"], []).append(t)
            add(y * 0.8, 2.0)                                       # a first take, then the keeper
        where.setdefault(l["id"], []).append(t)
        add(y, 2.0 + 0.5 * (k % 3))
        expect[l["id"]] = "ok"
    reading = os.path.join(tmp, f"reading_{speaker}.wav")
    common.write_wav(reading, np.concatenate(parts))
    print(f"synthetic reading of {speaker}: {len(lines)} lines, {t:.0f}s")
    raw = os.path.join(tmp, "raw")
    run("cut_takes.py", reading, "--speaker", speaker, "--out", raw)
    rep = json.load(open(os.path.join(raw, speaker, "_report.json")))["lines"]
    problems = []
    for lid, want in expect.items():
        r = rep[lid]
        # a line the recogniser mishears can legitimately come back as "low" (taken by position); it must still be
        # the right take
        if r["status"] != want and not (want == "ok" and r["status"] == "low" and r.get("start") is not None):
            problems.append(f"{speaker} {lid}: expected {want}, got {r['status']} (score {r.get('score')}, heard {r.get('heard')!r})")
        elif want == "ok" and r["start"] < where[lid][-1] - 1.0:
            problems.append(f"{speaker} {lid}: took an earlier take ({r['start']}s, last is at {where[lid][-1]:.0f}s)")
    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--keep", action="store_true", help="keep the temporary folder and print its path")
    ap.add_argument("--real", help="comma list of speakers whose REAL sheet in script.md is read by a synthetic voice, "
                                   "e.g. GENDO,BASE (needs script.md and the GPU; adds a few minutes)")
    a = ap.parse_args()
    tmp = tempfile.mkdtemp(prefix="voices_selftest_")
    if a.real:
        problems = []
        for sp in a.real.upper().split(","):
            problems += real_sheet(sp, tmp)
        print("\n" + ("REAL-SHEET TEST PASSED" if not problems else "REAL-SHEET TEST FOUND PROBLEMS:\n  " + "\n  ".join(problems)))
        sys.exit(1 if problems else 0)
    texts = verse_text()
    clips = {}
    for v, lid in VERSES.items():
        c, n = v.split(":")
        p = glob.glob(rf"D:\genesis-vr\verses\dry\*_gen-{c}-{int(n):02d}.wav")
        clips[lid] = common.read_audio(p[0])

    # fixture script: one MISATO sheet with directions, a non-verbal line 1.05b, plus other speakers for the pack step
    sc = ["# Fixture", "", "## Scene 1. Test", "", "> A test.", ""]
    order = list(VERSES.values())
    for lid in order:
        d = f" *({DIRS[lid]})*" if lid in DIRS else ""
        sc.append(f"**MISATO** `{lid}` {texts[[k for k, v in VERSES.items() if v == lid][0]]}{d}")
        sc.append("")
        if lid == "1.04":
            sc.append("**MISATO** `1.09` *(No words. One long breath in through the teeth.)*")
            sc.append("")
    script = os.path.join(tmp, "script.md")
    open(script, "w", encoding="utf-8").write("\n".join(sc) + "\n")

    # the reading
    rng = np.random.default_rng(1)
    z = lambda s: np.zeros(int(s * SR), np.float32)
    breath = (rng.standard_normal(int(0.9 * SR)) * np.hanning(int(0.9 * SR)) * 0.03).astype(np.float32)
    parts = [z(3.0)]
    log = {}

    def add(lid, y, gap=2.2):
        log.setdefault(lid, []).append(sum(len(p) for p in parts) / SR)
        parts.extend([y, z(gap)])

    add("1.01", clips["1.01"])
    add("1.02", clips["1.02"][: int(len(clips["1.02"]) * 0.35)], 1.8)           # a flub: stops half way
    add("1.02", clips["1.02"])
    add("1.03", clips["1.03"])
    add("1.04", clips["1.04"] * 0.7)                                             # first take
    add("1.04", clips["1.04"])                                                   # retake: this is the one to keep
    add("1.09", breath)                                                          # the non-verbal sound
    add("1.05", clips["1.05"])
    # 1.06 is skipped on purpose
    add("1.07", clips["1.07"])
    add("1.08", clips["1.08"])
    add("1.03", clips["1.03"])                                                   # out-of-order retake at the end
    reading = os.path.join(tmp, "reading.wav")
    common.write_wav(reading, np.concatenate(parts))
    print(f"fixture in {tmp}  (reading {sum(len(p) for p in parts) / SR:.0f}s, takes at {json.dumps({k: [round(t) for t in v] for k, v in log.items()})})")

    raw, final, pack = os.path.join(tmp, "raw"), os.path.join(tmp, "final"), os.path.join(tmp, "pack")
    run("cut_takes.py", reading, "--speaker", "MISATO", "--script", script, "--out", raw)
    rep = json.load(open(os.path.join(raw, "MISATO", "_report.json")))["lines"]
    problems = []
    for lid in order + ["1.09"]:
        r = rep[lid]
        want = "missing" if lid == "1.06" else ("check" if lid == "1.09" else "ok")
        if r["status"] != want:
            problems.append(f"{lid}: expected {want}, got {r['status']} ({r.get('score')})")
    late = rep["1.03"]
    if not (late.get("start", 0) > log["1.03"][1] - 1):
        problems.append(f"1.03 should come from the late retake at {log['1.03'][1]:.0f}s, got start {late.get('start')}")
    if not (rep["1.04"].get("start", 0) > log["1.04"][1] - 1):
        problems.append(f"1.04 should be the last take at {log['1.04'][1]:.0f}s, got start {rep['1.04'].get('start')}")
    if not (rep["1.02"].get("start", 0) > log["1.02"][1] - 1):
        problems.append(f"1.02 should be the full take at {log['1.02'][1]:.0f}s, got start {rep['1.02'].get('start')}")
    for lid in ("1.01", "1.05", "1.08"):
        d = len(clips[lid]) / SR
        got = rep[lid].get("dur", 0)
        if abs(got - d) > 0.7:
            problems.append(f"{lid}: cut is {got}s, source clip is {d:.1f}s")

    run("transform.py", "--raw", raw, "--out", final, "--script", script, "--force")
    run("pack_sounds.py", "--finals", final, "--pack", pack, "--durations", os.path.join(tmp, "durations.json"))
    sj = json.load(open(os.path.join(pack, "assets", "angel", "sounds.json")))
    dj = json.load(open(os.path.join(tmp, "durations.json")))
    for lid in order + ["1.09"]:
        if lid == "1.06":
            continue
        ev = "line.misato." + lid.replace(".", "_")
        if ev not in sj:
            problems.append(f"sounds.json lacks {ev}")
        ogg = os.path.join(pack, "assets", "angel", "sounds", "line", "misato", lid.replace(".", "_") + ".ogg")
        if not os.path.exists(ogg):
            problems.append(f"missing {ogg}")
        if lid not in dj:
            problems.append(f"durations.json lacks {lid}")
    print("\n" + ("SELF-TEST PASSED" if not problems else "SELF-TEST FOUND PROBLEMS:\n  " + "\n  ".join(problems)))
    if a.keep or problems:
        print("files kept in", tmp)
    else:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
