"""Signal-processing building blocks for the character voices (numpy / scipy / ffmpeg only).

psola_contour  - re-draw the pitch contour (flatten or exaggerate) without touching the vocal tract
breath         - add shaped breath noise that follows the speech envelope
reverb / comb / ring / telephone / radio / pa - the machine voice
"""
import numpy as np
from scipy import signal
from scipy.ndimage import median_filter, uniform_filter1d, zoom

from common import SR, f0_track, ffmpeg_filter


# ====================================================================================== PSOLA
def _interp_f0(t_grid, f0, n, sr, smooth=7):
    """Dense per-sample voiced mask and f0 curve (Hz) from a 5 ms pitch track."""
    ok = ~np.isnan(f0)
    if ok.sum() < 8:
        return None, None
    f = f0.copy()
    f[ok] = median_filter(f[ok], size=min(smooth, int(ok.sum())), mode="nearest")   # removes octave glitches
    idx = np.arange(len(f))
    fi = np.interp(idx, idx[ok], f[ok])
    # a frame counts as voiced only if it has voiced neighbours (kills isolated detections)
    vm = uniform_filter1d(ok.astype(float), 5) > 0.55
    ts = np.arange(n) / sr
    f_s = np.interp(ts, t_grid, fi)
    v_s = np.interp(ts, t_grid, vm.astype(float)) > 0.5
    return v_s, f_s


def _pitch_marks(x, sr, voiced, f0s, unvoiced_period):
    """Glottal-ish pulse positions: peaks of the low-passed waveform spaced by the local period in voiced
    stretches, a fixed 5 ms grid in unvoiced ones."""
    n = len(x)
    sos = signal.butter(2, 900, "low", fs=sr, output="sos")
    xs = signal.sosfiltfilt(sos, x)
    marks = []
    # contiguous voiced runs
    d = np.diff(np.concatenate([[0], voiced.astype(np.int8), [0]]))
    starts, ends = np.where(d == 1)[0], np.where(d == -1)[0]
    cover = np.zeros(n, bool)
    for s, e in zip(starts, ends):
        if e - s < int(0.03 * sr):
            continue
        cover[s:e] = True
        seg = xs[s:e]
        pol = 1.0 if seg.max() >= -seg.min() else -1.0
        anchor = s + int(np.argmax(pol * seg))
        run = [anchor]
        for direction in (1, -1):
            p = anchor
            while True:
                T = sr / float(np.clip(f0s[min(max(p, 0), n - 1)], 55, 500))
                q = p + direction * T
                if q < s or q >= e:
                    break
                lo, hi = int(q - 0.25 * T), int(q + 0.25 * T) + 1
                lo, hi = max(lo, s), min(hi, e)
                if hi <= lo:
                    break
                q = lo + int(np.argmax(pol * xs[lo:hi]))
                if (q - p) * direction <= 0.5 * T:
                    break
                run.append(q)
                p = q
        marks += run
    marks = sorted(set(marks))
    # fill the unvoiced stretches
    step = int(unvoiced_period * sr)
    unv = ~cover
    dd = np.diff(np.concatenate([[0], unv.astype(np.int8), [0]]))
    for s, e in zip(np.where(dd == 1)[0], np.where(dd == -1)[0]):
        marks += list(range(s + step // 2, e, step))
    return np.array(sorted(set(marks)), dtype=np.int64)


def psola_contour(x, sr=SR, inflection=1.0, formant=1.0, pitch=1.0, pivot_hz=None, max_ratio=(0.6, 1.7)):
    """TD-PSOLA re-synthesis.

    inflection  1.0 keeps the pitch movement, 0.0 makes it a monotone, >1 exaggerates it. The movement is
                scaled in the log domain around `pivot_hz` (default: this clip's median pitch).
    pitch       extra overall F0 ratio (keep it modest, 0.75..1.35, PSOLA is for fine work)
    formant     vocal-tract ratio: grains are resampled so the spectral envelope moves, F0 does not
    Duration is unchanged.
    """
    if abs(inflection - 1) < 1e-3 and abs(formant - 1) < 1e-3 and abs(pitch - 1) < 1e-3:
        return x
    n = len(x)
    t_grid, f0 = f0_track(x, sr)
    voiced, f0s = _interp_f0(t_grid, f0, n, sr)
    if voiced is None:
        return x
    med = float(np.exp(np.median(np.log(f0s[voiced])))) if pivot_hz is None else pivot_hz
    new_f0 = np.exp(np.log(med * pitch) + inflection * (np.log(np.clip(f0s, 40, 600)) - np.log(med)))
    new_f0 = np.clip(new_f0, med * pitch * max_ratio[0], med * pitch * max_ratio[1])
    unv = 0.005
    marks = _pitch_marks(x, sr, voiced, f0s, unv)
    if len(marks) < 4:
        return x
    # local analysis period at each mark
    gaps = np.diff(marks)
    ta = np.concatenate([[gaps[0]], gaps]) * 0.5 + np.concatenate([gaps, [gaps[-1]]]) * 0.5
    ta = np.clip(ta, sr / 500, sr / 50)
    pad = int(0.1 * sr)
    out = np.zeros(n + 2 * pad, np.float64)
    wsum = np.zeros(n + 2 * pad, np.float64)
    t_out = float(marks[0])
    while t_out < n:
        ti = int(t_out)
        k = int(np.searchsorted(marks, ti))
        if k == 0:
            j = 0
        elif k >= len(marks):
            j = len(marks) - 1
        else:
            j = k if abs(marks[k] - ti) < abs(marks[k - 1] - ti) else k - 1
        m, T = int(marks[j]), float(ta[j])
        L = max(int(T), 8)
        lo, hi = m - L, m + L
        g = np.zeros(2 * L)
        a0, a1 = max(lo, 0), min(hi, n)
        g[a0 - lo:a1 - lo] = x[a0:a1]
        w = np.hanning(2 * L)
        g = g * w
        if abs(formant - 1) > 1e-3:
            newlen = max(int(round(2 * L / formant)), 8)
            g = zoom(g, newlen / (2 * L), order=1, mode="nearest", grid_mode=True)
            w = zoom(w, len(g) / len(w), order=1, mode="nearest", grid_mode=True)
        c = len(g) // 2
        s = int(t_out) - c + pad
        if s >= 0 and s + len(g) <= len(out):
            out[s:s + len(g)] += g
            wsum[s:s + len(g)] += w
        # advance by the synthesis period
        v = voiced[min(ti, n - 1)]
        step = (sr / new_f0[min(ti, n - 1)]) if v else unv * sr
        t_out += max(step, 16)
    out = out[pad:pad + n]
    wsum = wsum[pad:pad + n]
    out = out / np.maximum(wsum, 0.25 * np.median(wsum[wsum > 0]) if (wsum > 0).any() else 1.0)
    # keep the original level
    ref = np.sqrt(np.mean(x ** 2) + 1e-12)
    cur = np.sqrt(np.mean(out ** 2) + 1e-12)
    return (out * (ref / cur)).astype(np.float32)


# ====================================================================================== textures
def envelope(x, sr=SR, ms=40):
    return uniform_filter1d(np.abs(x), max(1, int(sr * ms / 1000)), mode="nearest")


def breath(x, sr=SR, level_db=-24.0, lo=1400.0, hi=9000.0, follow=0.7, seed=3):
    """Mix in breathy noise (aspiration) whose loudness follows the voice, so it only appears while speaking."""
    rng = np.random.default_rng(seed)
    nz = rng.standard_normal(len(x)).astype(np.float32)
    sos = signal.butter(2, [lo, min(hi, sr / 2 - 100)], "band", fs=sr, output="sos")
    nz = signal.sosfilt(sos, nz)
    env = envelope(x, sr, 30)
    env = env / (env.max() + 1e-9)
    mod = follow * env + (1 - follow) * 0.15
    nz = nz / (np.sqrt(np.mean(nz ** 2)) + 1e-9) * np.sqrt(np.mean(x ** 2) + 1e-12)
    return (x + nz * mod * 10 ** (level_db / 20)).astype(np.float32)


def saturate(x, drive=1.5, mix=0.5):
    """Gentle tanh saturation, level-matched, blended with the clean signal."""
    y = np.tanh(x * drive) / np.tanh(drive)
    return ((1 - mix) * x + mix * y).astype(np.float32)


def bandlimit(x, lo, hi, sr=SR, order=4):
    sos = signal.butter(order, [lo, hi], "band", fs=sr, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def comb(x, delay_ms=3.1, gain=0.45, sr=SR, feedback=True):
    """A short comb filter - the hollow 'speaker in a tube' ring."""
    d = max(1, int(sr * delay_ms / 1000))
    if feedback:
        b, a = np.zeros(d + 1), np.zeros(d + 1)
        b[0], a[0], a[d] = 1.0, 1.0, -gain
        return signal.lfilter(b, a, x).astype(np.float32)
    y = x.copy()
    y[d:] += gain * x[:-d]
    return y.astype(np.float32)


def ring(x, freq=58.0, depth=0.25, sr=SR):
    """Partial ring modulation: (1-depth)*x + depth*x*sin. Adds sidebands without destroying the words."""
    t = np.arange(len(x)) / sr
    return ((1 - depth) * x + depth * x * np.sin(2 * np.pi * freq * t)).astype(np.float32)


def _ir(sr, seconds, rt60, seed, dark_hz=4500.0, predelay_ms=0.0, early=None):
    rng = np.random.default_rng(seed)
    n = int(sr * seconds)
    t = np.arange(n) / sr
    h = rng.standard_normal(n) * np.exp(-6.91 * t / rt60)
    sos = signal.butter(1, dark_hz, "low", fs=sr, output="sos")
    h = signal.sosfilt(sos, h)
    h *= np.minimum(t / 0.004, 1.0)
    if early:
        for ms, g in early:
            i = int(sr * ms / 1000)
            if i < n:
                h[i] += g * np.abs(h).max() * 4
    h = np.concatenate([np.zeros(int(sr * predelay_ms / 1000)), h])
    return (h / np.sqrt(np.sum(h ** 2))).astype(np.float32)


def reverb(x, sr=SR, rt60=1.6, wet_db=-9.0, predelay_ms=12, dark_hz=3800, early=None, tail_s=None, seed=11):
    """Convolution reverb with a synthetic impulse response; returns dry+wet with the tail appended."""
    ir = _ir(sr, min(rt60 * 1.3, 4.0), rt60, seed, dark_hz, predelay_ms, early)
    tail = int(sr * (rt60 if tail_s is None else tail_s))
    xp = np.concatenate([x, np.zeros(tail, np.float32)])
    wet = signal.fftconvolve(xp, ir)[:len(xp)]
    wet *= np.sqrt(np.mean(xp ** 2) + 1e-12) / (np.sqrt(np.mean(wet ** 2)) + 1e-12)
    return (xp + wet * 10 ** (wet_db / 20)).astype(np.float32)


def noise_bed(n, sr=SR, level_db=-48.0, hum_hz=0.0, seed=5):
    rng = np.random.default_rng(seed)
    nz = rng.standard_normal(n).astype(np.float32)
    sos = signal.butter(2, 6000, "low", fs=sr, output="sos")
    nz = signal.sosfilt(sos, nz) * 10 ** (level_db / 20)
    if hum_hz:
        nz += 10 ** ((level_db - 6) / 20) * np.sin(2 * np.pi * hum_hz * np.arange(n) / sr)
    return nz.astype(np.float32)


