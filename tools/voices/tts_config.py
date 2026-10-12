"""The synthetic voices of the four characters: Chatterbox, cloned from a short reference clip each.

THIS IS THE FILE TO EDIT TO TUNE THE TTS VOICES (the recorded-voice pipeline is config.py).  tts_lines.py renders every line with these numbers
and the character bridge speaks its live replies and adapted lines with the SAME numbers, so a line sounds like the same person wherever it
comes from.

Engine: Chatterbox "standard" (`chatterbox.tts.ChatterboxTTS`).  The Turbo model ignores exaggeration and cfg_weight, which are the two knobs that
make Rei breathe and Gendo drone, so it is not used.

Per character
  exaggeration   0..1+   how much the delivery is pushed.  low = flat and level, high = animated.
  cfg_weight     0..1    how closely the speech follows the reference clip's own pace.  low = faster, freer; high = slower, more deliberate.
  temperature    0.3..1  sampling noise.  low = steady and repeatable, high = livelier and riskier.
  tempo          pace multiplied on afterwards without changing pitch (Rubber Band): 1.0 as spoken, <1 slower.
  top_p / min_p / repetition_penalty   sampler; the library defaults unless set.
The pitch of a voice comes from its reference clip (voices\\tts_refs\\<SPEAKER>.wav), not from a number here.

The references are built by `tts_lines.py refs` from the user's own voice-converted recordings (voices\\final, or voices\\backup_user_recordings\\final
once they have been moved), 2 to 4 clean, effect-free clips joined; the Gendo clip is re-rendered dry from his raw recording because every one of his
lines carries an effect.  NEVER from a recording of a real actor or of the TV series.
"""
import os

ROOT = r"D:\angel-attack"
VOICES_DIR = os.path.join(ROOT, "voices")
REFS_DIR = os.path.join(VOICES_DIR, "tts_refs")            # <SPEAKER>.wav (+ refs.json: which lines went into it)
RAW_TTS_DIR = os.path.join(VOICES_DIR, "tts_raw")          # <SPEAKER>\<id>.wav  the dry takes (no effect, no loudness work), + _report.json
AUDITION_DIR = os.path.join(VOICES_DIR, "audition_tts")
BACKUP_DIR = os.path.join(VOICES_DIR, "backup_user_recordings")
REPORT_JSON = os.path.join(VOICES_DIR, "tts_report.json")

ENGINE = "standard"

# Tuned by measurement (tts_lines.py tune): see README.md of tools\voices for the numbers each setting produced.
VOICES = {
    "MISATO":  {"exaggeration": 0.55, "cfg_weight": 0.30, "temperature": 0.80, "tempo": 1.10,
                "brief": "bright, quick, warm"},
    "RITSUKO": {"exaggeration": 0.35, "cfg_weight": 0.35, "temperature": 0.70, "tempo": 0.85,
                "brief": "level, dry, exact"},
    "GENDO":   {"exaggeration": 0.10, "cfg_weight": 0.45, "temperature": 0.60, "tempo": 0.82,
                "brief": "low, slow, flat"},
    "REI":     {"exaggeration": 0.20, "cfg_weight": 0.40, "temperature": 0.60, "tempo": 0.80,
                "brief": "very soft, breathy, flat"},
}

# A reference can be reshaped (DSP on the user's converted voice, never another voice) so that two characters built from similar voices come out as two
# people: Rei's clip is raised, its vocal tract made smaller and a breath added.  Measured: Misato-Rei speaker similarity 0.87 -> 0.75.
REF_SHAPE = {"REI": {"pitch": 1.08, "formant": 1.2, "breath_db": -12.0}}

# What the measurements are judged against (tts_lines.py report): words per second of speech (silence at both ends trimmed), median pitch order,
# speaker similarity between two different characters (below SIM_DISTINCT) and between two lines of one character (above SIM_SAME).
RATE_TARGET = {"MISATO": (2.8, 3.6), "RITSUKO": (2.3, 3.0), "GENDO": (1.7, 2.4), "REI": (1.6, 2.4)}
PITCH_ORDER = ["REI", "MISATO", "RITSUKO", "GENDO"]          # highest to lowest median F0
SIM_DISTINCT = 0.78
SIM_SAME = 0.80

# Candidate acceptance when a line is rendered: the take is transcribed back and compared with the script text.
ASR_GOOD = 0.97              # word similarity at which a take is accepted at once
TRIES = 6                    # seeds tried before the best take is kept (and reported)
MAX_INNER_SILENCE_S = 1.3    # a pause longer than this inside a take counts against it
PEAK_MAX = 2.5             # a dry take whose float peak goes beyond this has a spike in it (Chatterbox output is not limited; the finished line is limited to -1.5 dB)

# Words Chatterbox is told to say differently from how the script spells them (the script itself is never changed).  Filled in by `tts_lines.py render`
# after listening to the transcripts; empty until a word is mispronounced.
RESPELL = {}


def ref_path(speaker):
    return os.path.join(REFS_DIR, f"{speaker}.wav")
