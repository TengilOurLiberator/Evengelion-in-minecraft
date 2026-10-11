"""Transmission / space effects ('over the radio', 'public address', 'from above'...).

Every effect takes its numbers from config.FX[name] so they can be tuned by ear without touching code.
"""
import numpy as np

import dsp
from common import SR, ffmpeg_filter
from dsp import bandlimit, comb, noise_bed, reverb, saturate


def _gated_noise(y, level_db, hum_hz, sr):
    """Line noise that is only there while the voice is (plus a short hold), faded in and out, like a squelched link."""
    from scipy.ndimage import maximum_filter1d, uniform_filter1d
    env = dsp.envelope(y, sr, 20)
    active = (env > 0.03 * (env.max() + 1e-9)).astype(np.float32)
    mask = uniform_filter1d(maximum_filter1d(active, int(0.18 * sr)), int(0.04 * sr))
    return (noise_bed(len(y), sr, level_db, hum_hz) * mask).astype(np.float32)


def _comp(y, spec, sr):
    return ffmpeg_filter(y, spec, sr) if spec else y


def apply(x, name, p, sr=SR):
    """Apply effect `name` with parameters dict `p`. Returns float32 (may be longer: tails and squelch)."""
    if name in (None, "", "none"):
        return x
    y = x
    if name in ("phone", "radio", "intercom"):
        y = bandlimit(y, p["lo"], p["hi"], sr, p.get("order", 4))
        y = saturate(y, p.get("drive", 2.0), p.get("mix", 0.45))
        if p.get("ring_hz"):
            y = dsp.ring(y, p["ring_hz"], p.get("ring_depth", 0.1), sr)
        if p.get("comb_ms"):
            y = comb(y, p["comb_ms"], p.get("comb_gain", 0.25), sr)
        y = _comp(y, p.get("comp"), sr)
        if name == "radio" and p.get("squelch", True):
            y = np.concatenate([y, np.zeros(int(0.04 * sr), np.float32)])
            rng = np.random.default_rng(9)
            sq = bandlimit(rng.standard_normal(int(p.get("squelch_ms", 70) * sr / 1000)).astype(np.float32), 600, 4200, sr, 2)
            sq *= p.get("squelch_level", 0.05) * np.linspace(1, 0, len(sq)) ** 2
            y = np.concatenate([y, sq])
        y = y + _gated_noise(y, p.get("noise_db", -48), p.get("hum_hz", 0.0), sr)
        return y.astype(np.float32)
    if name in ("pa", "street"):
        y = bandlimit(y, p["lo"], p["hi"], sr, p.get("order", 3))
        y = saturate(y, p.get("drive", 1.6), p.get("mix", 0.25))
        y = reverb(y, sr, rt60=p["rt60"], wet_db=p["wet_db"], predelay_ms=p.get("predelay_ms", 25),
                   dark_hz=p.get("dark_hz", 3200), early=p.get("early"), tail_s=p.get("tail_s", 1.2))
        return y
    if name == "above":                                   # a voice from a high booth: big, distant, a little dark
        y = bandlimit(y, p.get("lo", 90), p.get("hi", 7500), sr, 2)
        y = reverb(y, sr, rt60=p["rt60"], wet_db=p["wet_db"], predelay_ms=p.get("predelay_ms", 30),
                   dark_hz=p.get("dark_hz", 3600), early=p.get("early"), tail_s=p.get("tail_s", 1.0))
        return (y * 10 ** (p.get("gain_db", 0.0) / 20)).astype(np.float32)
    if name == "cockpit":                                 # inside the entry plug: close, tight, a touch metallic
        y = bandlimit(y, p.get("lo", 220), p.get("hi", 5200), sr, 3)
        y = comb(y, p.get("comb_ms", 1.7), p.get("comb_gain", 0.22), sr)
        y = reverb(y, sr, rt60=p.get("rt60", 0.28), wet_db=p.get("wet_db", -9), predelay_ms=2,
                   dark_hz=p.get("dark_hz", 5000), tail_s=p.get("tail_s", 0.3))
        return (y + _gated_noise(y, p.get("noise_db", -52), 0.0, sr)).astype(np.float32)
    if name == "muffled":                                 # through a wall or a hull
        y = ffmpeg_filter(y, f"lowpass=f={p.get('hi', 1700)}:p=2,equalizer=f=250:t=q:w=1:g=3", sr)
        return (y * 10 ** (p.get("gain_db", -2.0) / 20)).astype(np.float32)
    raise ValueError(f"unknown effect {name!r}")


def effects_for(direction, rules):
    """Ordered list of effect names whose pattern matches the direction text (rules = [(regex, name), ...])."""
    import re
    out = []
    for pat, name in rules:
        if re.search(pat, direction or "", re.I) and name not in out:
            out.append(name)
    return out
