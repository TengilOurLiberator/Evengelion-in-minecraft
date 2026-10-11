"""audio_utils.py - the finishing toolkit for generated sounds (numpy/scipy only, nothing installed).

Loudness, true peak, limiter and Vorbis encoding reuse the procedural pipeline's own functions (tools/sound/dsp.py,
the same libvorbis/ffmpeg route as make_sound.encode) so a generated file is measured exactly like a procedural one.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile
from math import gcd

import numpy as np
import scipy.signal as sg
import soundfile as sf

HERE = os.path.dirname(os.path.abspath(__file__))
SOUND_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(SOUND_DIR))
sys.path.insert(0, SOUND_DIR)
import dsp  # noqa: E402  (procedural toolkit: lufs, true_peak_db, limit)

SR = dsp.SR           # 44100, the pack's rate
PACK = os.path.join(ROOT, "pack", "angel-resources", "assets", "angel")
SOUNDS = os.path.join(PACK, "sounds")
CAND = os.path.join(ROOT, "work", "sound_candidates")
BACKUP = os.path.join(CAND, "procedural_backup")


def find_tool(name):
    p = shutil.which(name)
    if p:
        return p
    for pat in (rf"D:\malmo-vr\tools\ffmpeg\*\bin\{name}.exe", rf"D:\*\tools\ffmpeg\*\bin\{name}.exe", rf"C:\ffmpeg\bin\{name}.exe"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise FileNotFoundError(name)


FFMPEG = find_tool("ffmpeg")


def event_rel(event):
    """repo-relative path of the pack file for an event name ('sfx.crash' -> pack/.../sounds/sfx/crash.ogg)"""
    kind, short = event.split(".", 1)
    return os.path.join("pack", "angel-resources", "assets", "angel", "sounds", kind, short + ".ogg")


def event_file(event):
    return os.path.join(ROOT, event_rel(event))


def backup_file(event):
    return os.path.join(BACKUP, event_rel(event))


def ref_path(event):
    """the PROCEDURAL file of an event: the backup when we have replaced it, else the pack file itself"""
    b = backup_file(event)
    return b if os.path.exists(b) else event_file(event)


# --------------------------------------------------------------------------------------------- io
def N(s):
    return int(round(s * SR))


def load(path):
    """float64 (n, 2) at 44.1 kHz whatever the file was"""
    x, sr = sf.read(path, dtype="float64", always_2d=True)
    if sr != SR:
        g = gcd(SR, sr)
        x = sg.resample_poly(x, SR // g, sr // g, axis=0)
    if x.shape[1] == 1:
        x = np.repeat(x, 2, axis=1)
    return x[:, :2]


def read_pack(path):
    """a file as stored (mono stays 1-D, stereo (n, 2))"""
    x, sr = sf.read(path, dtype="float64", always_2d=False)
    assert sr == SR, (path, sr)
    return x


def mono(x):
    return x if x.ndim == 1 else x.mean(axis=1)


def channels(x, ch):
    if ch == 1:
        return mono(x)
    return np.stack([x, x], axis=1) if x.ndim == 1 else x


def lufs(x):
    return dsp.lufs(x)


def tp(x):
    return dsp.true_peak_db(x)


def db(g):
    return 10.0 ** (g / 20.0)


def todb(v):
    return 20.0 * np.log10(max(float(v), 1e-12))


def encode(x, path, q):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(suffix=".wav")
    os.close(fd)
    sf.write(tmp, x.astype(np.float32), SR, subtype="FLOAT")
    try:
        subprocess.run([FFMPEG, "-v", "error", "-y", "-i", tmp, "-c:a", "libvorbis", "-q:a", str(q), path], check=True)
    finally:
        os.remove(tmp)


def encode_checked(x, path, q, ceil=-1.05, target_lufs=None, tol=0.5):
    """encode, decode again, make sure the decoded true peak is under -1.0 dBTP (shave and retry like make_sound.build_one)
    and return (decoded, info)."""
    n = len(x)
    for attempt in range(6):
        encode(x, path, q)
        y = read_pack(path)
        t = tp(y)
        if t <= ceil:
            break
        x = x * db(-(t - ceil + 0.1))
    info = dict(samples=len(y), expected_samples=n, true_peak=round(t, 2), lufs=round(lufs(y), 2), bytes=os.path.getsize(path),
                channels=1 if y.ndim == 1 else y.shape[1])
    return y, info


# --------------------------------------------------------------------------------------------- shaping
def dc_hp(x, f=10.0):
    x = x - x.mean(axis=0)
    sos = sg.butter(1, f / (SR / 2), "high", output="sos")
    return sg.sosfilt(sos, x, axis=0)


def fade(x, fin=0.0, fout=0.0, shape="cos"):
    return dsp.fade(x, fin, fout, shape)


def onset_index(x, floor_db=-50.0, rel_db=-42.0, win_ms=2.0, back_db=None, back_ms=150.0):
    """first sample where the 2 ms envelope rises above max(floor_db, peak + rel_db) (dBFS); with back_db the start is then walked
    back (at most back_ms) to where the envelope was still back_db below that threshold, so the attack of the hit is kept whole
    while a quiet prelude before it is not"""
    m = np.abs(mono(x))
    w = max(1, int(win_ms / 1000 * SR))
    env = np.sqrt(np.convolve(m ** 2, np.ones(w) / w, mode="same"))
    thr = max(10 ** (floor_db / 20), env.max() * 10 ** (rel_db / 20))
    idx = np.where(env > thr)[0]
    if not len(idx):
        return 0
    i = int(idx[0])
    if back_db is not None:
        lo = max(0, i - N(back_ms / 1000.0))
        j = np.where(env[lo:i + 1] > thr * 10 ** (back_db / 20))[0]
        if len(j):
            i = lo + int(j[0])
    return i


def set_level(x, target, ceil=-1.3, tol=0.15, limit=True):
    """gain to the target LUFS, with the look-ahead limiter keeping true peak under `ceil`; repeats because limiting costs loudness.
    returns (y, dict(lufs, tp, gr_db))"""
    gain0 = gain = target - lufs(x)
    y = x * db(gain)
    for _ in range(14):
        y = x * db(gain)
        t = tp(y)
        if t > ceil and limit:
            y = dsp.limit(y, ceil - 0.2)
            t = tp(y)
            if t > ceil:
                y = y * db(ceil - t)
        err = target - lufs(y)
        if abs(err) <= tol or gain - gain0 > 14.0:
            break
        gain += err
    return y, dict(lufs=round(lufs(y), 2), tp=round(tp(y), 2), makeup_db=round(gain - gain0, 1))


def hp_zero(x, f, order=2):
    """zero-phase high-pass (forward-backward Butterworth): removes the sub rumble Stable Audio puts under everything"""
    if not f or f <= 0:
        return x
    sos = sg.butter(order, f / (SR / 2), "high", output="sos")
    return sg.sosfiltfilt(sos, x, axis=0)


def _ltas_bands(x, edges):
    m = mono(x)
    ff, pw = sg.welch(m, SR, nperseg=8192, noverlap=4096)
    out = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        sel = (ff >= lo) & (ff < hi)
        out.append(10 * np.log10(pw[sel].mean() + 1e-16))
    return np.array(out)


def match_clips(clips, max_db=9.0):
    """bring the long-term spectrum and level of several clips of the same bed to their common average (third-octave resolution, at most
    +-max_db per band) so the crossfade between pieces is not an audible change of timbre"""
    edges = 40.0 * 2 ** (np.arange(0, 28) / 3.0)
    edges = edges[edges < 20000]
    centers = np.sqrt(edges[:-1] * edges[1:])
    spec = np.array([_ltas_bands(c, edges) for c in clips])
    target = spec.mean(axis=0)
    out = []
    for c, s in zip(clips, spec):
        g = np.clip(target - s, -max_db, max_db)
        # smooth the correction across bands, interpolate on a log-frequency axis
        g = np.convolve(np.pad(g, 1, mode="edge"), [0.25, 0.5, 0.25], mode="valid")
        n = len(c)
        F = np.fft.rfftfreq(n, 1 / SR)
        resp = 10 ** (np.interp(np.log(np.maximum(F, 1.0)), np.log(centers), g) / 20.0)
        Z = np.fft.rfft(c, axis=0)
        out.append(np.fft.irfft(Z * (resp[:, None] if c.ndim == 2 else resp), n=n, axis=0))
    rms = np.array([np.sqrt(np.mean(o ** 2)) for o in out])
    tgt = np.exp(np.mean(np.log(rms)))
    return [o * (tgt / r) for o, r in zip(out, rms)]


# --------------------------------------------------------------------------------------------- loops
def _w(n):
    t = (np.arange(n) + 0.5) / n
    return np.sin(0.5 * np.pi * t), np.cos(0.5 * np.pi * t)       # equal power in, out


def circular_xfade(x, start, L, xf):
    """loop of exactly L samples cut from x[start:start+L+xf]: the natural continuation of the end (x[start+L:start+L+xf]) is faded
    out over the first xf samples of the head, which is faded in.  Sample L-1 therefore runs straight into sample 0."""
    seg = x[start:start + L + xf]
    assert len(seg) >= L + xf, (len(seg), L, xf)
    out = seg[:L].copy()
    win, wout = _w(xf)
    sh = (-1, 1) if out.ndim == 2 else (-1,)
    out[:xf] = seg[L:L + xf] * wout.reshape(sh) + seg[:xf] * win.reshape(sh)
    return out


def pieced_loop(clips, L, xf, skip=1.0):
    """a loop of exactly L samples made of one piece per clip, equal-power crossfaded into each other and (circularly) the last into
    the first.  For n pieces each is (L + n*xf)/n long.  Clips must be at least piece + 2*skip seconds."""
    n = len(clips)
    tot = L + n * xf
    lens = [tot // n + (1 if i < tot % n else 0) for i in range(n)]
    pieces = []
    for c, p in zip(clips, lens):
        s = N(skip)
        assert len(c) >= p + 2 * s, f"clip too short: {len(c) / SR:.1f}s for a {p / SR:.1f}s piece"
        pieces.append(c[s:s + p].copy())
    win, wout = _w(xf)
    sh = (-1, 1) if pieces[0].ndim == 2 else (-1,)
    for i, pc in enumerate(pieces):
        pc[:xf] *= win.reshape(sh)             # every piece fades in (the first one under the wrapped tail of the last)
        pc[-xf:] *= wout.reshape(sh)           # and out
    out = np.zeros((L + xf,) + pieces[0].shape[1:])
    pos = 0
    for pc in pieces:
        out[pos:pos + len(pc)] += pc
        pos += len(pc) - xf
    # the last piece's fade-out region lies in [L, L+xf): wrap it onto the start
    res = out[:L].copy()
    res[:xf] += out[L:L + xf]
    return res


# --------------------------------------------------------------------------------------------- tempo
def onset_env(x, hop=441, nfft=2048, band=None):
    m = mono(x)
    f, t, Z = sg.stft(m, SR, nperseg=nfft, noverlap=nfft - hop, boundary=None, padded=False)
    S = np.log1p(30.0 * np.abs(Z))
    if band is not None:
        sel = (f >= band[0]) & (f <= band[1])
        S = S[sel]
    flux = np.maximum(0.0, np.diff(S, axis=1)).sum(axis=0)
    env = np.r_[0.0, flux]
    k = int(1.0 * SR / hop)
    env = env - np.convolve(env, np.ones(k) / k, mode="same")
    return env, SR / hop


def tempo_fit(env, fs, center, rel=0.08, step=0.01, harmonics=4):
    """scan bpm around `center`; score = sum of the onset-envelope's Fourier magnitude at 1..4 x the beat frequency.
    returns (bpm, beat_phase_seconds, strength) with strength = score relative to the envelope energy (0..~1)"""
    t = np.arange(len(env)) / fs
    bpms = np.arange(center * (1 - rel), center * (1 + rel), step)
    best = (-1, None)
    norm = np.sqrt(np.sum(env ** 2) * len(env)) + 1e-12
    scores = np.zeros(len(bpms))
    for i0 in range(0, len(bpms), 200):
        b = bpms[i0:i0 + 200]
        sc = np.zeros(len(b))
        for h in range(1, harmonics + 1):
            ph = np.exp(-2j * np.pi * np.outer(b / 60.0 * h, t))
            sc += np.abs(ph @ env) / np.sqrt(h)
        scores[i0:i0 + 200] = sc
    k = int(np.argmax(scores))
    f = bpms[k] / 60.0
    z1 = np.sum(env * np.exp(-2j * np.pi * f * t))
    phase = (np.angle(z1) / (2 * np.pi * f)) % (1.0 / f)
    return float(bpms[k]), float(phase), float(scores[k] / norm)


def downbeat_index(env_low, fs, bpm, phase, bar=4):
    """which of `bar` beats carries the most low-frequency onset energy (the kick on the one)"""
    period = 60.0 / bpm
    tb = phase + np.arange(int((len(env_low) / fs - phase) / period)) * period
    idx = np.round(tb * fs).astype(int)
    idx = idx[idx < len(env_low)]
    vals = np.maximum(env_low[idx], 0)
    acc = np.array([vals[k::bar].sum() for k in range(bar)])
    return int(np.argmax(acc)), acc / (acc.sum() + 1e-12)


def stretch(x, ratio):
    """time-stretch by `ratio` (>1 = faster, shorter) with Rubber Band through ffmpeg, pitch unchanged"""
    if abs(ratio - 1.0) < 1e-5:
        return x
    cmd = [FFMPEG, "-v", "error", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-", "-af",
           f"rubberband=tempo={ratio:.7f}:pitch=1:transients=crisp:window=standard", "-ar", str(SR), "-ac", "2", "-f", "f32le", "-"]
    r = subprocess.run(cmd, input=np.ascontiguousarray(x, dtype="<f4").tobytes(), capture_output=True)
    if r.returncode:
        raise RuntimeError(r.stderr.decode(errors="replace"))
    return np.frombuffer(r.stdout, dtype="<f4").reshape(-1, 2).astype(np.float64)


# --------------------------------------------------------------------------------------------- features
def frame_db(m, win=0.1):
    w = N(win)
    nb = max(1, len(m) // w)
    return 10 * np.log10(np.mean(m[:nb * w].reshape(nb, w) ** 2, axis=1) + 1e-14)


def profile(x, tempo_hint=None, scan=False):
    """numbers a person would read off a spectrogram: brightness, weight in the lows/highs, dynamics, trend, event density,
    tempo and its clarity, silences, steady narrow tones"""
    m = mono(x)
    dur = len(m) / SR
    f, t, Z = sg.stft(m, SR, nperseg=4096, noverlap=2048, boundary=None, padded=False)
    P = np.abs(Z) ** 2
    tot = P.sum(axis=0) + 1e-20
    cen = (P * f[:, None]).sum(axis=0) / tot
    live = tot > np.percentile(tot, 20)
    E = P.sum()
    lows = P[f < 250].sum() / E
    his = P[f > 4000].sum() / E
    lev = frame_db(m, 1.0)
    thirds = np.array_split(frame_db(m, 0.5), 3)
    env, fs = onset_env(x)
    thr = env.mean() + 1.5 * env.std()
    pk, _ = sg.find_peaks(env, height=thr, distance=int(0.08 * fs))
    out = dict(seconds=round(dur, 2), centroid_hz=round(float(np.median(cen[live])), 0), low_frac=round(float(lows), 3),
               high_frac=round(float(his), 3), dyn_db=round(float(np.percentile(lev, 95) - np.percentile(lev, 5)), 1),
               slope_db=round(float(thirds[-1].mean() - thirds[0].mean()), 1), onset_rate=round(len(pk) / dur, 2),
               clipped=int(np.sum(np.abs(x) >= 0.999)), peak_db=round(todb(np.abs(x).max()), 1))
    fl = frame_db(m, 0.1)
    quiet = fl < max(np.median(fl) - 35.0, -75.0)
    run = best = 0
    for q in quiet:
        run = run + 1 if q else 0
        best = max(best, run)
    out["longest_silence_s"] = round(best * 0.1, 1)
    if tempo_hint:
        bpm, ph, st = tempo_fit(env, fs, tempo_hint, rel=0.12, step=0.05)
        out.update(bpm=round(bpm, 2), tempo_strength=round(st, 3))
    if scan:
        # is there a beat at all? best comb score over 60-180 bpm (loops of a few seconds give little resolution: that is fine here)
        bpm, ph, st = tempo_fit(env, fs, 110.0, rel=0.55, step=0.25)
        out.update(pulse_bpm=round(bpm, 1), pulse_strength=round(st, 3))
    # steady narrow tones (hum): a line in the long-term spectrum that stands out from its surroundings and is there in most 2 s blocks
    if dur >= 2.0:
        ff, pw = sg.welch(m, SR, nperseg=16384, noverlap=8192)
        db_ = 10 * np.log10(pw + 1e-20)
        med = sg.medfilt(db_, 151)
        prom = db_ - med
        cand = [(prom[i], ff[i]) for i in sg.find_peaks(prom, height=18.0)[0] if 40 < ff[i] < 9000]
        cand.sort(reverse=True)
        out["tonal_lines"] = [(round(float(p), 1), round(float(fr), 1)) for p, fr in cand[:3]]
    return out


def mel_like_spectrogram_rows(x, width=900, height=130, fmin=30, fmax=20000, rng=80.0):
    """not used for decisions: a re-export of analyze.spectrogram so sheets match the procedural previews"""
    import analyze
    return analyze.spectrogram(x, width, height=height, fmin=fmin, fmax=fmax, rng=rng)
