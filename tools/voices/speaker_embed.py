"""Speaker-identity numbers from Chatterbox's own voice encoder (already installed with chatterbox-tts).

Cosine similarity of two utterances: ~1.0 = the encoder hears one speaker; different real speakers usually sit
around 0.5-0.75.  Used by audition.py to check that the five characters really are five different voices and
that a converted voice has moved away from the user's.
"""
import numpy as np

import common

_ve = None


def _model():
    global _ve
    if _ve is None:
        import warnings
        warnings.filterwarnings("ignore")
        from huggingface_hub import hf_hub_download
        from safetensors.torch import load_file
        from chatterbox.models.voice_encoder import VoiceEncoder
        ve = VoiceEncoder()
        ve.load_state_dict(load_file(hf_hub_download("ResembleAI/chatterbox", "ve.safetensors")))
        _ve = ve.eval()
    return _ve


def embed(x, sr=common.SR):
    e = _model().embeds_from_wavs([common.resample(np.asarray(x, np.float32), sr, 16000)], sample_rate=16000, as_spk=True)
    return e / np.linalg.norm(e)


def similarity_matrix(named):
    """named: {label: audio}. Returns (labels, matrix)."""
    labels = list(named)
    E = [embed(named[k]) for k in labels]
    return labels, np.array([[float(a @ b) for b in E] for a in E])
