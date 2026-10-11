"""Shared helpers for the voice pipeline: paths, audio I/O, pitch measurement, ffmpeg, loudness.

Everything here runs in the D:\\voice-assistant environment:
    D:\\voice-assistant\\.venv\\Scripts\\python.exe
"""
import glob
import os
import re
import shutil
import subprocess
import sys

import numpy as np

# ---------------------------------------------------------------------------------------- paths
TOOLS = os.path.dirname(os.path.abspath(__file__))
ROOT = r"D:\angel-attack"
SCRIPT_MD = os.path.join(ROOT, "script.md")
RECORDING_DIR = os.path.join(ROOT, "recording")
VOICES = os.path.join(ROOT, "voices")
RAW_DIR = os.path.join(VOICES, "raw")
FINAL_DIR = os.path.join(VOICES, "final")
AUDITION_DIR = os.path.join(VOICES, "audition")
REFS_DIR = os.path.join(VOICES, "refs")            # synthetic voice-conversion targets
DURATIONS_JSON = os.path.join(VOICES, "durations.json")
PACK_DIR = os.path.join(ROOT, "pack", "angel-resources")
SPEAKERS = ["MISATO", "RITSUKO", "GENDO", "REI", "BASE"]
HUMANS = ["MISATO", "RITSUKO", "GENDO", "REI"]

SR = 48000                                          # working rate for everything

os.environ.setdefault("HF_HOME", r"D:\voice-assistant\models\huggingface")
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
try:                                                # console may be cp1252; never die on a curly quote
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def setup_torch_dlls():
    """CTranslate2 (faster-whisper) needs the cuDNN/cuBLAS DLLs that ship inside the torch wheel."""
    import torch
    lib = os.path.join(os.path.dirname(torch.__file__), "lib")
    os.add_dll_directory(lib)
    os.environ["PATH"] = lib + os.pathsep + os.environ["PATH"]


# ---------------------------------------------------------------------------------------- ffmpeg
def find_tool(name):
    p = shutil.which(name)
    if p:
        return p
    for pat in (rf"D:\malmo-vr\tools\ffmpeg\*\bin\{name}.exe", rf"D:\*\tools\ffmpeg\*\bin\{name}.exe",
                rf"C:\ffmpeg\bin\{name}.exe"):
        hits = sorted(glob.glob(pat))
        if hits:
            return hits[-1]
    raise FileNotFoundError(f"{name} not found on PATH or in the known ffmpeg folders")


FFMPEG = find_tool("ffmpeg")
FFPROBE = find_tool("ffprobe")


def ffmpeg_filter(x, graph, sr=SR, out_sr=None):
    """Run mono float audio through an ffmpeg -af graph via pipes; returns float32 mono."""
    out_sr = out_sr or sr
    cmd = [FFMPEG, "-v", "error", "-f", "f32le", "-ar", str(sr), "-ac", "1", "-i", "-", "-af", graph,
           "-ar", str(out_sr), "-ac", "1", "-f", "f32le", "-"]
    r = subprocess.run(cmd, input=np.ascontiguousarray(x, dtype="<f4").tobytes(), capture_output=True)
    if r.returncode:
        raise RuntimeError(f"ffmpeg failed for '{graph}': {r.stderr.decode(errors='replace')}")
    return np.frombuffer(r.stdout, dtype="<f4").copy()


def rubberband(x, pitch=1.0, formant="preserved", tempo=1.0, sr=SR):
    """Rubber Band via ffmpeg. pitch = F0 ratio. formant 'preserved' keeps the vocal tract where it was,
    'shifted' moves it with the pitch (so the speaker sounds bigger/smaller)."""
    if abs(pitch - 1) < 1e-4 and abs(tempo - 1) < 1e-4:
        return x
    g = f"rubberband=tempo={tempo:.5f}:pitch={pitch:.5f}:pitchq=quality:formant={formant}:transients=smooth"
    return ffmpeg_filter(x, g, sr)


def formant_shift_only(x, ratio, sr=SR):
    """Move the formants by `ratio` and leave F0 and duration alone (two rubberband passes)."""
    if abs(ratio - 1) < 1e-3:
        return x
    y = rubberband(x, pitch=ratio, formant="shifted", sr=sr)       # F0 and formants both x ratio
    return rubberband(y, pitch=1 / ratio, formant="preserved", sr=sr)   # F0 back, formants stay


# ---------------------------------------------------------------------------------------- audio I/O
def read_audio(path, sr=SR):
    """Any audio file -> mono float32 at `sr`."""
    import soundfile as sf
    try:
        x, fs = sf.read(path, dtype="float32", always_2d=True)
        x = x.mean(axis=1)
        if fs != sr:
            import soxr
            x = soxr.resample(x, fs, sr)
        return np.ascontiguousarray(x, dtype=np.float32)
    except Exception:
        r = subprocess.run([FFMPEG, "-v", "error", "-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                           capture_output=True)
        if r.returncode:
            raise RuntimeError(f"cannot read {path}: {r.stderr.decode(errors='replace')}")
        return np.frombuffer(r.stdout, dtype="<f4").copy()


def write_wav(path, x, sr=SR, subtype="PCM_24"):
    import soundfile as sf
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sf.write(path, np.clip(x, -1, 1), sr, subtype=subtype)


def resample(x, a, b):
    if a == b:
        return x
    import soxr
    return soxr.resample(x, a, b).astype(np.float32)


# ---------------------------------------------------------------------------------------- analysis
def frame_db(x, sr=SR, hop_ms=10):
    hop = int(sr * hop_ms / 1000)
    n = len(x) // hop
    if n == 0:
        return np.array([-120.0])
    r = np.sqrt(np.mean(x[:n * hop].reshape(n, hop) ** 2, axis=1))
    return 20 * np.log10(np.maximum(r, 1e-7))


def f0_track(x, sr=SR, fmin=55.0, fmax=450.0, hop_ms=5.0):
    """(times, f0 with NaN where unvoiced) using librosa's pYIN on a 16 kHz copy."""
    import librosa
    x16 = resample(x, sr, 16000)
    hop = int(16000 * hop_ms / 1000)
    f0, voiced, prob = librosa.pyin(x16, fmin=fmin, fmax=fmax, sr=16000, frame_length=1536, hop_length=hop,
                                    fill_na=np.nan, resolution=0.1)
    f0 = np.where(voiced, f0, np.nan)
    # pYIN sometimes lands an octave away for a few frames; pull those back next to their neighbours
    ok = np.where(~np.isnan(f0))[0]
    if len(ok) > 10:
        v = f0[ok].copy()
        for _ in range(2):
            pad = np.pad(v, 20, mode="edge")
            loc = np.array([np.median(pad[i:i + 41]) for i in range(len(v))])
            r = v / loc
            v = np.where((r > 1.75) & (r < 2.3), v / 2, np.where((r > 0.43) & (r < 0.57), v * 2, v))
        f0[ok] = v
    t = np.arange(len(f0)) * hop / 16000
    return t, f0


def f0_stats(x, sr=SR, **kw):
    """Median F0 in Hz, and the 10th/90th percentile (a measure of how much the voice moves)."""
    t, f0 = f0_track(x, sr, **kw)
    v = f0[~np.isnan(f0)]
    if len(v) < 10:
        return {"median": 0.0, "p10": 0.0, "p90": 0.0, "p25": 0.0, "p75": 0.0, "voiced_s": 0.0}
    return {"median": float(np.median(v)), "p10": float(np.percentile(v, 10)), "p90": float(np.percentile(v, 90)),
            "p25": float(np.percentile(v, 25)), "p75": float(np.percentile(v, 75)),
            "voiced_s": float(len(v) * 0.005)}


def formant_estimate(x, sr=SR, n=3):
    """Rough median F1..F3 (Hz) from LPC on voiced, loud frames. For before/after comparison only."""
    import librosa
    x16 = resample(x, sr, 11025)
    x16 = np.append(x16[0], x16[1:] - 0.97 * x16[:-1])
    fl, hop = 512, 256
    out = []
    thr = np.percentile(np.abs(x16), 90) * 0.5
    for i in range(0, len(x16) - fl, hop):
        fr = x16[i:i + fl] * np.hanning(fl)
        if np.sqrt(np.mean(fr ** 2)) < thr * 0.35:
            continue
        try:
            a = librosa.lpc(fr, order=12)
        except Exception:
            continue
        r = np.roots(a)
        r = r[np.imag(r) > 0.01]
        freqs = np.angle(r) * 11025 / (2 * np.pi)
        bws = -np.log(np.abs(r)) * 11025 / np.pi             # bandwidth in Hz; narrow = a real formant
        sel = sorted(f for f, b in zip(freqs, bws) if f > 250 and b < 400)
        if len(sel) >= n:
            out.append(sel[:n])
    if not out:
        return [0.0] * n
    return [float(v) for v in np.median(np.array(out), axis=0)]


def spectral_centroid(x, sr=SR):
    """Mean spectral centroid (Hz, 100-6000) of the louder frames: a quick 'brightness / vocal-tract size' number."""
    from scipy import signal as sg
    f, t, S = sg.stft(x, sr, nperseg=2048, noverlap=1536)
    P = np.abs(S) ** 2
    band = (f >= 100) & (f <= 6000)
    e = P[band].sum(axis=0)
    keep = e > np.percentile(e, 60)
    cen = (f[band, None] * P[band]).sum(axis=0) / np.maximum(e, 1e-12)
    return float(np.mean(cen[keep])) if keep.any() else 0.0


# ---------------------------------------------------------------------------------------- loudness
def lufs(x, sr=SR):
    """Integrated BS.1770 loudness; falls back to an RMS estimate for clips shorter than the 400 ms block."""
    if len(x) < int(0.45 * sr):
        x = np.concatenate([x, np.zeros(int(0.45 * sr) - len(x), np.float32)])
    import pyloudnorm as pyln
    v = pyln.Meter(sr).integrated_loudness(x.astype(np.float64))
    if not np.isfinite(v):
        rms = np.sqrt(np.mean(x ** 2) + 1e-12)
        v = 20 * np.log10(rms) - 0.7
    return float(v)


def peak_db(x):
    return float(20 * np.log10(max(float(np.abs(x).max()), 1e-9)))


def trim_silence(x, sr=SR, thresh_db=-48.0, lead=0.10, tail=0.25, fade=0.012):
    db = frame_db(x, sr)
    on = np.where(db > thresh_db)[0]
    if len(on) == 0:
        return x
    a = max(0, int((on[0] * 0.01 - lead) * sr))
    b = min(len(x), int(((on[-1] + 1) * 0.01 + tail) * sr))
    y = x[a:b].copy()
    f = min(int(fade * sr), len(y) // 4)
    if f > 0:
        y[:f] *= np.linspace(0, 1, f, dtype=np.float32)
        y[-f:] *= np.linspace(1, 0, f, dtype=np.float32)
    return y


def norm_id(i):
    """'2.01' -> '2_01' (a Minecraft resource-location-safe form)."""
    return i.replace(".", "_")
