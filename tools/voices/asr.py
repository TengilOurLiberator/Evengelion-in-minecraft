"""faster-whisper helpers (same model and setup Genesis used: large-v3 on the GPU, CPU fallback)."""
import difflib
import re

import numpy as np

import common

_model = None


def model():
    global _model
    if _model is None:
        common.setup_torch_dlls()
        from faster_whisper import WhisperModel
        try:
            _model = WhisperModel("large-v3", device="cuda", compute_type="float16")
        except Exception as e:                      # no GPU / DLL trouble
            print("whisper: cuda failed, using cpu:", e)
            _model = WhisperModel("large-v3", device="cpu", compute_type="int8")
    return _model


def words_of(text):
    """Normalise to comparable words: lower case, letters/digits/apostrophes only."""
    text = text.lower().replace("’", "'")
    return [w for w in re.findall(r"[a-z0-9']+", text) if w]


def transcribe(x, sr=common.SR, language="en", word_timestamps=False, initial_prompt=None, vad=False):
    """x: float mono at any rate. Returns (text, segments)."""
    x16 = common.resample(np.asarray(x, np.float32), sr, 16000)
    segs, _ = model().transcribe(x16, language=language, beam_size=5, condition_on_previous_text=False,
                                 word_timestamps=word_timestamps, vad_filter=vad, temperature=0.0,
                                 no_speech_threshold=None, log_prob_threshold=None, compression_ratio_threshold=None,
                                 initial_prompt=initial_prompt)
    segs = list(segs)
    return " ".join(s.text.strip() for s in segs).strip(), segs


def similarity(a, b):
    """0..1 word-level similarity of two strings (SequenceMatcher ratio over normalised words)."""
    wa, wb = words_of(a), words_of(b)
    if not wa and not wb:
        return 1.0
    return difflib.SequenceMatcher(None, wa, wb, autojunk=False).ratio()


def wer(ref, hyp):
    """Word error rate of hyp against ref."""
    r, h = words_of(ref), words_of(hyp)
    if not r:
        return 0.0 if not h else 1.0
    d = list(range(len(h) + 1))
    for i, rw in enumerate(r, 1):
        prev, d[0] = d[0], i
        for j, hw in enumerate(h, 1):
            cur = min(d[j] + 1, d[j - 1] + 1, prev + (rw != hw))
            prev, d[j] = d[j], cur
    return d[len(h)] / len(r)
