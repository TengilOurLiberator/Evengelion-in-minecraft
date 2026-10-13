"""Paths, names, tunables and voice settings for the character bridge.

Everything that someone might want to change without reading the rest of the code lives here.
An optional ``config.json`` next to this file (or the file named by ANGEL_BRIDGE_CONFIG) can override
any value in SETTINGS and any key of any entry in VOICE_PROFILES / COLORS, e.g.

    {"settings": {"model": "claude-sonnet-5-5", "address_range": 10},
     "voices": {"gendo": {"pitch": 0.82}}}
"""
import json
import os

ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT = os.path.dirname(ROOT)

CHARACTER_DIR = os.path.join(PROJECT, "characters")            # <id>.md sheets and beats.md (written by the project lead)
BEATS_FILE = os.path.join(CHARACTER_DIR, "beats.md")
VOICE_DIR = os.path.join(PROJECT, "voices", "final")           # <SPEAKER>\<id>.wav: the PRE-RENDERED TTS take of every line (tools\voices\tts_lines.py); the bridge plays them for verbatim lines and as the fallback.
                                                               # The voices' reference clips are voices\tts_refs (tools\voices\tts_config.py). The user's recordings are in voices\backup_user_recordings.
SERVER_DIR = os.path.join(PROJECT, "server")
CACHE_DIR = os.path.join(ROOT, "cache")                        # reference clips assembled for Chatterbox, an empty cwd for Claude
STATE_FILE = os.path.join(ROOT, "state.json")                  # rolling memory, so a restart does not make them forget
HF_HOME = r"D:\voice-assistant\models\huggingface"
CLAUDE_EXE = os.path.join(os.path.expanduser("~"), ".local", "bin", "claude.exe")

# Order matters: the position (1-based) is the value of the datapack's #speaker score.
CHARACTERS = ["misato", "ritsuko", "gendo", "rei"]
NAMES = {"misato": "Misato", "ritsuko": "Ritsuko", "gendo": "Gendo", "rei": "Rei"}
LONG_NAMES = {"misato": "Captain Misato Katsuragi", "ritsuko": "Dr. Ritsuko Akagi",
              "gendo": "Commander Gendo Ikari", "rei": "Rei Ayanami"}
SPEAKER_DIRS = {c: c.upper() for c in CHARACTERS}              # folder under voices\final (matched case-insensitively)
COLORS = {"misato": "red", "ritsuko": "yellow", "gendo": "gray", "rei": "aqua"}   # subtitle colours in game chat

# Presence values the datapack writes to #present_<id>
ABSENT, IN_PERSON, VOICE_ONLY = 0, 1, 2

# Spoken names. "strong" aliases are names; "kin" aliases are titles that only count as an address when
# they are not introduced by "my / your / the ..." ("my father" is not "Father,"); "weak" aliases are common
# words or likely mishearings that count only at the very start or end of the utterance or before a comma.
ALIASES = {
    "misato":  {"strong": ["misato", "mizato", "misado", "missato", "katsuragi", "katsuragi-san", "misato-san"],
                "kin": ["captain"], "weak": ["misa", "mr sato"]},
    "ritsuko": {"strong": ["ritsuko", "ritzuko", "ritsuko-san", "akagi", "akaji"],
                "kin": ["doctor", "dr", "doc"], "weak": ["rits"]},
    "gendo":   {"strong": ["gendo", "gando", "gendou", "ikari-sensei"],
                "kin": ["father", "dad", "daddy", "commander"], "weak": []},
    "rei":     {"strong": ["rei", "ayanami", "ayanami-san"],
                "kin": [], "weak": ["ray", "rae", "ree", "wray", "ray ayanami"]},
}

SETTINGS = {
    "model": os.environ.get("ANGEL_MODEL", "claude-haiku-5-5"),   # low latency; set ANGEL_MODEL or --model to change
    "effort": "low",                  # Claude Code --effort for the talking models
    "stt_model": "large-v3-turbo",    # faster-whisper; "large-v3" is what Genesis uses (slower, a little more exact)
    "stt_prompt": "Shinji, Misato, Ritsuko, Gendo, Rei, Ayanami, Katsuragi, Akagi, Ikari, Commander, Captain, Doctor, Father, NERV.",
    "tts_engine": "turbo",            # "turbo" (fast, what Genesis uses) or "standard" (honours exaggeration / cfg_weight)
    "silence_s": 0.8,                 # silence that ends an utterance
    "vad_threshold": 0.5,
    "address_range": 8.0,             # blocks: "nearest present character" must be within this
    "gaze_range": 12.0,               # blocks: a character the player is looking at counts up to here
    "gaze_degrees": 20.0,             # half-angle of the gaze cone (a little extra is added for close characters)
    "eye_height": 1.62,               # player Pos is at the feet
    "body_height": 0.9,               # aim at this height above a character's feet
    "memory_turns": 8,                # exchanges kept per character
    "shared_log_lines": 8,            # what the others said, shown to each character
    "max_sentences": 3,
    "max_reply_chars": 320,
    "talk_wait": 8.0,                 # seconds to wait for a recorded line (#talking) to end before dropping the utterance
    "poll_s": 0.4,                    # how often the live bridge watches #talking
    "recycle_turns": 10,              # restart each Claude process after this many turns (keeps its history short)
    "claude_timeout": 40.0,
    "subtitles": True,                # also tellraw every spoken sentence to the game chat
}

# --- re-voiced (adapted) scripted lines: how far they may stray from the script line, by the story's pacing (tools\story\pace.py: build_story.py --pace).
# (words_min, words_max, take_max): the re-voiced line must have between words_min x and words_max x the script line's words, and its synthesised take may be at most
# take_max x the length of the pre-rendered take (the lower bound of the take, 0.55, stays as it is).  "full" is the original +-20 % / 1.45; "video" keeps an
# adapted line NO LONGER than the script line (+0 %, -25 %), because the video pacing has no air left to absorb a longer one: a live voice that runs long
# lengthens the whole film by exactly that much.  `adapt_bounds()` is what adapter.validate / its prompt should call instead of the literals 0.8 / 1.2 / 1.45.
ADAPT_BOUNDS = {"full": (0.8, 1.2, 1.45), "video": (0.75, 1.0, 1.0)}
SETTINGS["adapt_pace"] = os.environ.get("ANGEL_PACE", "video")      # must be the preset the story was built with (build_story.py --pace); video is the default build


def adapt_bounds(pace=None):
    return ADAPT_BOUNDS.get(pace or SETTINGS.get("adapt_pace", "video"), ADAPT_BOUNDS["video"])


# LEGACY (unused since the voices became tools\voices\tts_config.py; kept so an old config.json still loads).
# Fallback voices, used until voices\final\<SPEAKER>\*.wav exist. All use Chatterbox's own built-in voice.
#   pitch        >1 higher, <1 lower (resample, speed is restored afterwards)
#   pace         >1 faster, <1 slower
#   temperature  Turbo sampling temperature (lower = flatter, steadier)
#   exaggeration, cfg_weight   only used by tts_engine "standard" (Turbo ignores them)
#   gain         output level
VOICE_PROFILES = {
    "misato":  {"pitch": 1.03, "pace": 1.06, "temperature": 0.85, "exaggeration": 0.65, "cfg_weight": 0.35, "gain": 1.0},
    "ritsuko": {"pitch": 0.96, "pace": 1.00, "temperature": 0.70, "exaggeration": 0.35, "cfg_weight": 0.55, "gain": 1.0},
    "gendo":   {"pitch": 0.84, "pace": 0.92, "temperature": 0.60, "exaggeration": 0.20, "cfg_weight": 0.70, "gain": 1.0},
    "rei":     {"pitch": 1.07, "pace": 0.90, "temperature": 0.55, "exaggeration": 0.10, "cfg_weight": 0.75, "gain": 0.8},
}
# Applied on top of a character's voice when they are only a voice (presence 2).
RADIO = {"low_hz": 380.0, "high_hz": 3200.0, "drive": 2.2, "noise": 0.012, "gain": 0.9}


def _load_overrides():
    path = os.environ.get("ANGEL_BRIDGE_CONFIG", os.path.join(ROOT, "config.json"))
    if not os.path.exists(path):
        return
    data = json.load(open(path, encoding="utf-8"))
    SETTINGS.update(data.get("settings", {}))
    for who, vals in data.get("voices", {}).items():
        VOICE_PROFILES.setdefault(who, {}).update(vals)
    COLORS.update(data.get("colors", {}))
    RADIO.update(data.get("radio", {}))


_load_overrides()
os.environ.setdefault("HF_HOME", HF_HOME)
