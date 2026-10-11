"""Speak the BASE lines with Chatterbox's built-in voice instead of recording them.

    python synth_base.py               # every BASE line that has no raw file yet
    python synth_base.py --force       # all of them again
    python synth_base.py --ids 6.09    # just these

Writes D:\\angel-attack\\voices\\raw\\BASE\\<id>.wav, which transform.py then turns into the machine voice like any
recorded line.  Each line is checked by transcribing it back; a line that comes out with wrong words is spoken
again with another seed, and the closest attempt is kept and reported.
"""
import argparse
import os

import numpy as np

import asr
import common
import script_lines

SR = common.SR
TRIES = 5
GOOD = 0.97


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ids", help="comma list of line ids")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    want = {common.norm_id(i) for i in args.ids.split(",")} if args.ids else None
    lines = [l for l in script_lines.lines_for("BASE", script_lines.parse()) if want is None or l["id"] in want]
    out = os.path.join(common.RAW_DIR, "BASE")
    os.makedirs(out, exist_ok=True)
    todo = [l for l in lines if args.force or not os.path.exists(os.path.join(out, l["id"] + ".wav"))]
    if not todo:
        print("nothing to do")
        return
    common.setup_torch_dlls()
    import torch
    from chatterbox.tts import ChatterboxTTS
    tts = ChatterboxTTS.from_pretrained("cuda" if torch.cuda.is_available() else "cpu")
    poor = []
    for l in todo:
        best = (-1.0, None, "")
        for seed in range(TRIES):
            torch.manual_seed(100 + seed)
            w = tts.generate(l["text"], exaggeration=0.25, cfg_weight=0.6, temperature=0.6).squeeze().cpu().numpy()
            w = common.resample(np.asarray(w, np.float32), tts.sr, SR)
            heard, _ = asr.transcribe(w)
            score = asr.similarity(l["text"], heard)
            if score > best[0]:
                best = (score, w, heard)
            if score >= GOOD:
                break
        score, w, heard = best
        common.write_wav(os.path.join(out, l["id"] + ".wav"), common.trim_silence(w, SR))
        print(f"BASE {l['id']}  {len(w) / SR:4.1f}s  score {score:.2f}")
        if score < GOOD:
            poor.append((l["id"], l["text"], heard))
    for i, text, heard in poor:
        print(f"  check {i}: wanted '{text}'\n             heard  '{heard}'")
    print(f"{len(todo)} lines spoken, {len(poor)} to check")


if __name__ == "__main__":
    main()
