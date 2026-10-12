"""Text to speech: the four characters' Chatterbox voices, the SAME ones as the pre-rendered lines (tools\\voices\\tts_lib.py, tts_config.py).

A voice is a reference clip, voices\\tts_refs\\<SPEAKER>.wav, built by `tools\\voices\\tts_lines.py refs` from the user's own voice-converted recordings
(clean, effect-free lines joined).  HARD RULE: never a recording of a real actor or of the TV series, and nothing but the user's own voice
(converted) is ever a reference.  The generation settings of each character (exaggeration, cfg weight, temperature, pace) are in
tools\\voices\\tts_config.py, where the tuning measurements live.

A reply sentence and a scripted line differ only in their text: both are `Synth.raw` (dry voice) -> `tts_lib.master` (the effect of how the
character is heard, then the shared loudness of -19 LUFS).  A character who is only a voice on the radio/intercom (presence 2) gets the radio
effect of the script's `radio` direction, so a live reply sounds like the scripted radio lines.
"""
import os
import sys

from config import CHARACTERS, VOICE_ONLY

TOOLS_VOICES = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tools", "voices")
if TOOLS_VOICES not in sys.path:
    sys.path.append(TOOLS_VOICES)                  # appended: this folder's own config.py / selftest.py keep priority

os.environ.setdefault("TQDM_DISABLE", "1")           # no progress bars for every sentence


class _DropChatter:
    """Chatterbox prints progress lines on every sentence; keep the console readable."""

    def __init__(self, base):
        self.base, self.skip_newline = base, False

    def write(self, text):
        if "S3 Token -> Mel Inference" in text or text.lstrip().startswith("Sampling:"):
            self.skip_newline = True
            return len(text)
        if self.skip_newline and text.strip() == "":
            self.skip_newline = False
            return len(text)
        self.skip_newline = False
        return self.base.write(text)

    def __getattr__(self, name):
        return getattr(self.base, name)


if not isinstance(sys.stdout, _DropChatter):
    sys.stdout = _DropChatter(sys.stdout)


def speaker_of(who):
    return who.upper()


class VoiceBank:
    """The four voices on one Chatterbox model, loaded and warmed once."""

    def __init__(self, engine=None, synth=None):
        import tts_lib
        self.tts_lib = tts_lib
        self.engine = synth or tts_lib.Synth()
        self.sr = tts_lib.SR
        self.source = {c: f"voices\\tts_refs\\{speaker_of(c)}.wav" for c in CHARACTERS}
        self.active = 0                                                           # replies being synthesised right now (the look-ahead waits for them)
        self.synth(CHARACTERS[0], "Warming up.")                                 # first call is slow; pay for it now

    def has_reference(self, who):
        return True

    def busy(self):
        return self.active > 0

    def synth(self, who, text, presence=1, seed=None):
        """-> float32 mono at self.sr, in the character's voice, with the radio effect if the character is only a voice (presence 2)."""
        import random
        sp = speaker_of(who)
        self.active += 1
        try:
            raw = self.engine.raw(sp, text, seed=random.getrandbits(31) if seed is None else seed)
        finally:
            self.active -= 1
        return self.tts_lib.master(sp, raw, "radio" if presence == VOICE_ONLY else "")


# ---- devices -----------------------------------------------------------------------------------------------------
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
