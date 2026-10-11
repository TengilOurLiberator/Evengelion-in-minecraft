"""Text to speech with Chatterbox: one distinct voice per character, a radio treatment for voice-only characters.

HARD RULE: a voice reference may come ONLY from D:\\angel-attack\\voices\\final\\<SPEAKER>\\*.wav, the user's own
recorded lines processed into that character's voice. Never a recording of a real actor or of the TV show. Until a
character has such a folder, Chatterbox's own built-in voice is used, shaped by that character's profile in config.py.
"""
import glob
import logging
import math
import os
import threading
import time

from config import (CACHE_DIR, RADIO, SPEAKER_DIRS, VOICE_DIR, VOICE_PROFILES, CHARACTERS, VOICE_ONLY)

REF_MIN_S, REF_TARGET_S, REF_MAX_S = 6.5, 11.0, 16.0

os.environ.setdefault("TQDM_DISABLE", "1")           # no progress bars for every sentence


class _DropChatter:
    """Chatterbox prints 'S3 Token -> Mel Inference...' on every sentence; keep the console readable."""

    def __init__(self, base):
        self.base, self.skip_newline = base, False

    def write(self, text):
        if "S3 Token -> Mel Inference" in text:
            self.skip_newline = True
            return len(text)
        if self.skip_newline and text.strip() == "":
            self.skip_newline = False
            return len(text)
        self.skip_newline = False
        return self.base.write(text)

    def __getattr__(self, name):
        return getattr(self.base, name)


import sys  # noqa: E402
if not isinstance(sys.stdout, _DropChatter):
    sys.stdout = _DropChatter(sys.stdout)


def _inside_voice_dir(path):
    root = os.path.normcase(os.path.realpath(VOICE_DIR))
    p = os.path.normcase(os.path.realpath(path))
    return os.path.commonpath([root, p]) == root


def reference_files(who):
    """The user's processed recordings for this character, or []."""
    if not os.path.isdir(VOICE_DIR):
        return []
    want = SPEAKER_DIRS[who].lower()
    for d in os.listdir(VOICE_DIR):
        full = os.path.join(VOICE_DIR, d)
        if d.lower() == want and os.path.isdir(full):
            return sorted(f for f in glob.glob(os.path.join(full, "*.wav")) if _inside_voice_dir(f))
    return []


def build_reference(who, files):
    """One 7-16 second clip for Chatterbox's voice conditioning, from the user's clips. -> (path, [names used]) or (None, [])."""
    import numpy as np
    import soundfile as sf
    from scipy.signal import resample_poly

    clips = []
    for f in files:
        try:
            data, sr = sf.read(f, dtype="float32", always_2d=True)
        except Exception:
            continue
        mono = data.mean(axis=1)
        if len(mono) / sr >= 1.0:
            clips.append((f, mono, sr))
    if not clips:
        return None, []
    best = min((c for c in clips if REF_MIN_S <= len(c[1]) / c[2] <= REF_MAX_S),
               key=lambda c: abs(len(c[1]) / c[2] - REF_TARGET_S), default=None)
    chosen = [best] if best else []
    if not best:
        total = 0.0
        for c in sorted(clips, key=lambda c: -len(c[1]) / c[2]):
            chosen.append(c)
            total += len(c[1]) / c[2]
            if total >= REF_TARGET_S:
                break
    sr = chosen[0][2]
    parts = []
    for _, mono, s in chosen:
        parts.append(mono if s == sr else resample_poly(mono, sr, s).astype("float32"))
        parts.append(np.zeros(int(0.15 * sr), dtype="float32"))
    audio = np.concatenate(parts)[:int(REF_MAX_S * sr)]
    if len(audio) / sr < 5.2:
        return None, []
    os.makedirs(os.path.join(CACHE_DIR, "refs"), exist_ok=True)
    out = os.path.join(CACHE_DIR, "refs", f"{who}.wav")
    sf.write(out, audio, sr)
    return out, [os.path.basename(c[0]) for c in chosen]


# ---- shaping ------------------------------------------------------------------------------------------------------
def time_stretch(wav, rate):
    """Change speed without changing pitch (phase vocoder). rate > 1 is faster."""
    import torch
    import torchaudio.functional as AF

    x = torch.from_numpy(wav)
    n_fft, hop = 1024, 256
    win = torch.hann_window(n_fft)
    spec = torch.stft(x, n_fft, hop, window=win, return_complex=True)
    advance = torch.linspace(0, math.pi * hop, spec.shape[0])[..., None]
    out = torch.istft(AF.phase_vocoder(spec, rate, advance), n_fft, hop, window=win, length=int(len(x) / rate))
    return out.numpy()


def change_pitch(wav, ratio):
    """Raise (>1) or lower (<1) pitch, keeping the speed."""
    from fractions import Fraction
    from scipy.signal import resample_poly

    f = Fraction(1 / ratio).limit_denominator(100)
    shifted = resample_poly(wav, f.numerator, f.denominator).astype("float32")     # varispeed: pitch x ratio, speed x ratio
    return time_stretch(shifted, ratio) if abs(ratio - 1) > 0.005 else shifted     # stretch back to the original length


def radio_filter(wav, sr):
    """Phone/intercom/radio: narrow band, a little grit, a squelch of static either side."""
    import numpy as np
    from scipy.signal import butter, sosfilt

    r = RADIO
    sos = butter(4, [r["low_hz"], min(r["high_hz"], sr / 2 - 100)], btype="bandpass", fs=sr, output="sos")
    y = sosfilt(sos, wav)
    y = np.tanh(r["drive"] * y / max(1e-6, np.abs(y).max())) / math.tanh(r["drive"])
    rng = np.random.default_rng(7)
    hiss = lambda n: sosfilt(sos, rng.standard_normal(n)).astype("float32") * r["noise"]
    pre, post = hiss(int(0.07 * sr)), hiss(int(0.05 * sr))
    y = y + hiss(len(y))
    return np.concatenate([pre, y, post]).astype("float32") * r["gain"]


class VoiceBank:
    """All four voices on one model, loaded and warmed once."""

    def __init__(self, engine="turbo"):
        import numpy as np  # noqa: F401
        logging.getLogger("chatterbox").setLevel(logging.ERROR)
        self.engine, self.lock = engine, threading.Lock()
        if engine == "standard":
            from chatterbox.tts import ChatterboxTTS
            self.tts = ChatterboxTTS.from_pretrained(device="cuda")
        else:
            from chatterbox.tts_turbo import ChatterboxTurboTTS
            self.tts = ChatterboxTurboTTS.from_pretrained(device="cuda")
        self.sr = self.tts.sr
        self.default_conds = self.tts.conds
        self.conds, self.source = {}, {}
        for who in CHARACTERS:
            files = reference_files(who)
            ref, used = build_reference(who, files) if files else (None, [])
            if ref:
                self.tts.prepare_conditionals(ref)
                self.conds[who] = self.tts.conds
                self.source[who] = f"reference from voices\\final\\{SPEAKER_DIRS[who]}: {', '.join(used)}"
            else:
                self.conds[who] = self.default_conds
                self.source[who] = ("default Chatterbox voice, shaped (" + (f"{len(files)} clip(s) in voices\\final but too short"
                                    if files else "no recordings yet") + ")")
        self.tts.conds = self.default_conds
        self.synth(CHARACTERS[0], "Warming up.")                                 # first call is slow; pay for it now

    def has_reference(self, who):
        return self.conds[who] is not self.default_conds

    def synth(self, who, text, presence=1):
        """-> float32 mono array at self.sr, shaped for this character (and radio-filtered if voice only)."""
        import numpy as np

        p = VOICE_PROFILES[who]
        with self.lock:
            self.tts.conds = self.conds[who]
            if self.engine == "standard":
                wav = self.tts.generate(text, exaggeration=p["exaggeration"], cfg_weight=p["cfg_weight"], temperature=p["temperature"])
            else:
                wav = self.tts.generate(text, temperature=p["temperature"])
        wav = wav.squeeze().cpu().numpy().astype("float32")
        if not self.has_reference(who):                       # a recorded voice already IS the character; only shape the built-in one
            if abs(p["pitch"] - 1) > 0.005:
                wav = change_pitch(wav, p["pitch"])
            if abs(p["pace"] - 1) > 0.005:
                wav = time_stretch(wav, p["pace"])
        if presence == VOICE_ONLY:
            wav = radio_filter(wav, self.sr)
        peak = float(np.abs(wav).max()) or 1.0
        return wav / peak * 0.9 * p["gain"]


# ---- playback -----------------------------------------------------------------------------------------------------
def find_device(spec, kind):
    """None -> system default; a number -> that index; text -> first device whose name contains it. kind: 'input'|'output'."""
    if spec in (None, ""):
        return None
    if str(spec).isdigit():
        return int(spec)
    import sounddevice as sd
    key = "max_input_channels" if kind == "input" else "max_output_channels"
    for i, d in enumerate(sd.query_devices()):
        if d[key] > 0 and str(spec).lower() in d["name"].lower():
            return i
    raise SystemExit(f"No {kind} audio device matches {spec!r}. Run: python bridge.py --list-devices")


class Player:
    def __init__(self, device=None):
        self.device = device

    def play(self, wav, sr):
        import sounddevice as sd
        sd.play(wav, sr, device=self.device)
        sd.wait()                       # returns early if stop() is called from another thread

    def stop(self):
        import sounddevice as sd
        sd.stop()
