"""Chatterbox speaking the four characters (MISATO, RITSUKO, GENDO, REI): one synthesiser, one set of settings (tts_config.py), the
transmission effects of transform.py, the loudness of the finished lines.  Used by tts_lines.py (the pre-render of every line) and by
the character bridge (its live replies and the adapted lines) so that a voice is the same everywhere.

    synth = Synth()                                     # loads Chatterbox once, builds the four voices from voices\\tts_refs
    raw = synth.raw("MISATO", "Get in!", seed=3)        # float32 mono 48 kHz, the voice dry (tempo of the character applied)
    final = master("MISATO", raw, "radio")              # the direction's effects, then -19 LUFS / -1.5 dB peaks like every recorded line

The effect stage is transform.py's, not a copy: `master` calls transform.directions / fx.apply / transform.finish with the rules and numbers of
config.py.  The voice-conversion stage of transform.py is NOT used here.
"""
import importlib.util
import os
import re
import sys
import threading
import types
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.append(HERE)                 # appended: a host process with its own `config` / `selftest` (the bridge) keeps its own

import common  # noqa: E402
import tts_config as tc  # noqa: E402
from common import SR  # noqa: E402

HUMANS = ["MISATO", "RITSUKO", "GENDO", "REI"]
_VM = None


def voice_modules():
    """transform.py, fx.py, dsp.py and config.py of tools\\voices, importable from a process that has a different `config` module of its own."""
    global _VM
    if _VM is not None:
        return _VM
    saved = sys.modules.get("config")
    if saved is not None and hasattr(saved, "DIRECTION_RULES"):
        vc = saved
    else:
        spec = importlib.util.spec_from_file_location("voices_config", os.path.join(HERE, "config.py"))
        vc = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(vc)
        sys.modules["voices_config"] = vc
        sys.modules["config"] = vc
    try:
        import transform
        import fx
        import dsp
    finally:
        if vc is not saved:
            if saved is not None:
                sys.modules["config"] = saved
            else:
                sys.modules.pop("config", None)
    _VM = types.SimpleNamespace(config=vc, transform=transform, fx=fx, dsp=dsp)
    return _VM


# ====================================================================================== text
_ONES = "zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen".split()
_TENS = "_ _ twenty thirty forty fifty sixty seventy eighty ninety".split()


def _num_words(n):
    if n < 20:
        return _ONES[n]
    if n < 100:
        return _TENS[n // 10] + ("" if n % 10 == 0 else " " + _ONES[n % 10])
    return " ".join(_ONES[int(d)] for d in str(n))


# How Whisper spells the names the way they are pronounced (Rei is said "ray"): both sides of a comparison go through this.
ASR_ALIASES = {"ray": "rei", "rae": "rei", "wray": "rei", "ree": "rei", "ray's": "rei's", "nerve": "nerv", "nerf": "nerv", "ritzuko": "ritsuko",
               "katsuragi": "katsuragi", "katsurag": "katsuragi", "akaji": "akagi", "evangelian": "evangelion"}


def canon(text):
    """Comparable words: lower case, numbers spelled out, hyphens as spaces, letters and apostrophes only, names as Whisper hears them."""
    t = text.lower().replace("’", "'").replace("-", " ").replace("—", " ").replace("alright", "all right")
    t = re.sub(r"\b0(\d)\b", lambda m: "zero " + _ONES[int(m.group(1))], t)
    t = re.sub(r"(\d+)\.(\d+)", lambda m: _num_words(int(m.group(1))) + " point " + " ".join(_ONES[int(d)] for d in m.group(2)), t)
    t = re.sub(r"\d+", lambda m: _num_words(int(m.group(0))), t)
    return [ASR_ALIASES.get(w, w) for w in re.findall(r"[a-z']+", t)]


def similarity(ref, hyp):
    """0..1 word similarity of a transcript to the script text, forgiving of how a name is spelled (nerv / nerve, katsuragi / katsuragi-san)."""
    import difflib
    wa, wb = canon(ref), canon(hyp)
    if not wa and not wb:
        return 1.0
    snapped = []
    for w in wb:
        best = max(wa, key=lambda r: difflib.SequenceMatcher(None, r, w).ratio(), default=None)
        snapped.append(best if best is not None and difflib.SequenceMatcher(None, best, w).ratio() >= 0.8 else w)
    return difflib.SequenceMatcher(None, wa, snapped, autojunk=False).ratio()


def spoken_text(text):
    """What Chatterbox is given: the script text with the respellings of tts_config.RESPELL."""
    for a, b in tc.RESPELL.items():
        text = re.sub(rf"\b{re.escape(a)}\b", b, text)
    return text


# ====================================================================================== measurements
def active_stats(x, sr=SR):
    """-> dict: seconds of speech between the first and last sound, the longest silence inside, peak, the voiced share."""
    db = common.frame_db(x, sr)
    on = np.where(db > -45)[0]
    if len(on) == 0:
        return {"speech_s": 0.0, "inner_silence_s": 0.0, "peak": float(np.abs(x).max()), "active": 0.0}
    seg = db[on[0]:on[-1] + 1] > -45
    runs, cur = [], 0
    for v in seg:
        if not v:
            cur += 1
        elif cur:
            runs.append(cur)
            cur = 0
    return {"speech_s": (on[-1] - on[0] + 1) * 0.01, "inner_silence_s": max(runs, default=0) * 0.01,
            "peak": float(np.abs(x).max()), "active": float(seg.mean())}


def rate_wps(text, x, sr=SR):
    st = active_stats(x, sr)
    n = len(canon(text))
    return n / st["speech_s"] if st["speech_s"] > 0.2 else 0.0


# ====================================================================================== the synthesiser
class Synth:
    """Chatterbox (standard) with the four voices prepared.  generate() is serialised by a lock; ask from any thread."""

    def __init__(self, device=None, speakers=HUMANS, log=print):
        common.setup_torch_dlls()
        import logging
        import warnings
        logging.getLogger("chatterbox").setLevel(logging.ERROR)
        warnings.filterwarnings("ignore")
        import torch
        self.torch = torch
        os.environ.setdefault("TQDM_DISABLE", "1")
        from chatterbox.tts import ChatterboxTTS
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tts = ChatterboxTTS.from_pretrained(self.device)
        self.sr = self.tts.sr
        self.lock = threading.RLock()
        self.conds = {}
        for sp in speakers:
            p = tc.ref_path(sp)
            if not os.path.exists(p):
                raise FileNotFoundError(f"{p} is missing: run  tts_lines.py refs")
            with self.lock:
                self.tts.prepare_conditionals(p, exaggeration=tc.VOICES[sp]["exaggeration"])
                self.conds[sp] = self.tts.conds
        log(f"[tts] Chatterbox {tc.ENGINE} on {self.device}: voices {', '.join(speakers)}")

    def settings(self, speaker, **override):
        s = dict(tc.VOICES[speaker])
        s.update(override)
        return s

    def raw(self, speaker, text, seed=0, **override):
        """-> float32 mono at SR (48 kHz), the dry voice with the character's tempo applied.  Untrimmed."""
        s = self.settings(speaker, **override)
        with self.lock:
            self.tts.conds = self.conds[speaker]
            self.torch.manual_seed(int(seed) & 0x7FFFFFFF)
            kw = {k: s[k] for k in ("repetition_penalty", "min_p", "top_p") if k in s}
            wav = self.tts.generate(spoken_text(text), exaggeration=s["exaggeration"], cfg_weight=s["cfg_weight"],
                                    temperature=s["temperature"], **kw)
        x = wav.squeeze().detach().cpu().numpy().astype(np.float32)
        x = common.resample(x, self.sr, SR)
        if abs(s.get("tempo", 1.0) - 1.0) > 0.005:
            x = common.rubberband(x, tempo=s["tempo"], formant="preserved")
        return x.astype(np.float32)


# ====================================================================================== the effect and loudness stage (transform.py's)
def effects_for(speaker, direction):
    vm = voice_modules()
    return vm.transform.directions(speaker, direction)


def master(speaker, raw, direction="", nonverbal=False):
    """The dry voice -> the finished line: the effects the line's direction asks for (transform.py's rules and numbers), then trimmed to
    LEAD_S / TAIL_S, brought to TARGET_LUFS (plus the character's gain_db) and limited under PEAK_CEILING_DB, exactly as the recorded lines were."""
    vm = voice_modules()
    cfg = vm.config.CHARACTERS[speaker]
    y = raw
    names = [n for n in vm.transform.directions(speaker, direction) if n and n != "none"]
    for n in names:
        y = vm.fx.apply(y, n, vm.config.FX[n], SR)
    return vm.transform.finish(y, cfg, tail_extra=0.6 if any(n in ("pa", "street", "above") for n in names) else 0.0)


def breath_in(seed=5):
    """Rei's 5.31 has no words: one long breath in through the teeth, held, let go shaking.  Made from shaped noise (no voice to clone)."""
    from scipy import signal
    rng = np.random.default_rng(seed)
    n = int(1.5 * SR)
    noise = rng.standard_normal(n).astype(np.float32)
    sos = signal.butter(3, [1800, 7500], "band", fs=SR, output="sos")
    hiss = signal.sosfilt(sos, noise)
    t = np.arange(n) / SR
    env = np.clip(t / 0.55, 0, 1) ** 1.6                                     # the breath in
    env *= np.where(t < 0.8, 1.0, np.clip(1 - (t - 0.8) / 0.62, 0, 1))        # held, then let go
    env *= 1.0 + 0.35 * np.sin(2 * np.pi * 8.5 * t) * np.clip((t - 0.8) / 0.2, 0, 1)   # shaking as it goes
    body = signal.sosfilt(signal.butter(2, [250, 900], "band", fs=SR, output="sos"), rng.standard_normal(n).astype(np.float32))
    y = (hiss * 0.8 + body * 0.35) * env
    return (y / max(1e-6, float(np.abs(y).max())) * 0.5).astype(np.float32)


def seed_for(lid, k=0):
    return zlib.crc32(f"{lid}/{k}".encode()) & 0x7FFFFFFF
