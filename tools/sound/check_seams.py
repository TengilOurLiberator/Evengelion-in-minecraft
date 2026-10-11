"""check_seams.py - verify the hand-offs between files that are meant to be played one after the other:
    music.decision -> music.decision_loop, music.launch -> music.launch_loop, sfx.launch -> sfx.launch_roar
Prints the high-frequency click ratio at the seam (<= ~1 is indistinguishable from the middle of the file), the level on
either side, and how closely the tail of the long file matches the loop file."""
import os
import sys

import numpy as np
import scipy.signal as sg
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dsp
import make_sound as ms


def load(name):
    kind, short = name.split(".", 1)
    return sf.read(os.path.join(ms.SOUNDS, kind, short + ".ogg"))[0]


def seam(a, b, tag):
    mm = np.concatenate([dsp.mono(a)[-8192:], dsp.mono(b)[:8192]])
    hpf = sg.butter(4, 2000 / 22050, "high", output="sos")
    hs = np.abs(sg.sosfiltfilt(hpf, mm))
    ref = np.percentile(np.abs(sg.sosfilt(hpf, dsp.mono(b))), 99.9)
    ratio = hs[8192 - 22:8192 + 22].max() / max(ref, 1e-4)
    print(f"{tag:34s} seam hf ratio {ratio:5.2f} | last 100 ms {dsp.rms_db(a[-4410:]):6.1f} dB, first 100 ms {dsp.rms_db(b[:4410]):6.1f} dB")


def similarity(a, b, tag, skip=4.0):
    n = min(len(a), len(b))
    a, b = a[-n:], b[:n]
    s = int(skip * dsp.SR)
    c = [np.corrcoef(a[s:, k], b[s:, k])[0, 1] for k in range(2)]
    print(f"{tag:34s} tail-of-long vs loop correlation (after {skip:.0f} s) L/R: {c[0]:.3f} {c[1]:.3f}")


def main():
    for long_, loop_ in [("music.decision", "music.decision_loop"), ("music.launch", "music.launch_loop"), ("sfx.launch", "sfx.launch_roar")]:
        a, b = load(long_), load(loop_)
        seam(a, b, f"{long_} -> {loop_}")
        similarity(a[-len(b):], b, f"{long_} tail")


if __name__ == "__main__":
    main()
