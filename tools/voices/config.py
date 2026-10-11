"""Voice settings for the five characters.  THIS IS THE FILE TO EDIT TO TUNE BY EAR.

After changing anything:   python audition.py            (5 quick renders, a minute)
                           python transform.py --force   (re-render every recorded line)

The four human voices are the voice conversion and nothing after it (the user judged that the natural one by ear;
the pitch/inflection reshaping made them robotic): pitch_lock 0, inflection 1, tempo 1, no eq/comp/saturation/breath.
Only the transmission effects from the line's direction are added.

How a human voice is made (method "vc+dsp", the default):
  1. cleanup            high-pass, gentle denoise, level
  2. voice conversion   Chatterbox VC re-speaks the recording in a SYNTHETIC target voice (voices\\refs\\<NAME>.wav,
                        made from Chatterbox's own default voice + DSP; never a real person).  This changes the
                        timbre properly, not just the pitch.
  3. pitch + formants   PSOLA / Rubber Band: median F0 pulled to `f0`, vocal tract moved by `formant`,
                        pitch movement scaled by `inflection`
  4. tempo, colour      tempo, EQ, compression, saturation, breath noise
  5. transmission       'radio' / 'telephone' / 'public address' ... chosen from the line's *(direction)*
  6. loudness           one integrated-LUFS target for everyone, plus `gain_db` per character
Method "dsp" skips step 2 and does the whole transformation with Rubber Band + PSOLA (more robust, less natural
for big changes).  Use  python audition.py --compare  to hear both side by side.

Notes on the numbers
  f0           target MEDIAN pitch in Hz.  The recording is the user's voice, median about 112 Hz.
  pitch_lock   0..1, how firmly each line is pulled to `f0`. 1 = every line lands on f0, 0 = leave the
               pitch each line already has after conversion.  0.8 keeps some natural line-to-line variation.
  formant      vocal-tract ratio applied AFTER conversion (1.0 = leave the converted timbre alone).
  dsp_formant  vocal-tract ratio used by the plain "dsp" method (>1 smaller/younger, <1 bigger/older).
  inflection   1.0 = the user's own pitch movement, 0 = monotone, >1 = more animated.
  tempo        1.0 = as read.  <1 slower, >1 faster (pitch and formants are preserved).
  eq / comp    ffmpeg filter strings (equalizer, bass, treble, highpass, lowpass, acompressor ...)
"""

# ------------------------------------------------------------------------------------------ global
TARGET_LUFS = -19.0          # integrated loudness of every final line (Genesis narration was -18)
PEAK_CEILING_DB = -1.5       # nothing in a final line goes above this
LEAD_S = 0.06                # silence kept before the first word of a final line
TAIL_S = 0.25                # ... and after the last (effects with their own tail extend it)

CLEANUP = {
    "highpass_hz": 70,       # rumble
    "denoise_db": 9,         # afftdn noise reduction in dB (0 = off); keep low, it is already a quiet room
    "noise_floor_db": -50,   # afftdn noise floor estimate
}

DEFAULT_METHOD = "vc+dsp"    # or "dsp"

# ------------------------------------------------------------------------------------------ characters
CHARACTERS = {
    "MISATO": {   # woman, late twenties, bright, quick, warm, a little rough
        "method": "vc+dsp",
        "vc_ref": {"base": "turbo", "pitch": 0.93, "formant": 1.03, "exaggeration": 0.55, "cfg": 0.35,
                   "colour": {"eq": "equalizer=f=3200:t=q:w=1:g=3,treble=g=2:f=7000", "saturate": {"drive": 2.2, "mix": 0.25}},
                   "text": "Good morning, everyone. I know it is early, and I know the coffee is terrible, but we have "
                           "a long day ahead of us, so let us get started. Does anyone have any questions before we go?"},
        "f0": 212, "pitch_lock": 0.0,
        "formant": 1.00, "dsp_formant": 1.17,
        "inflection": 1.0, "tempo": 1.0,
        "eq": None,
        "comp": None,
        "saturate": None,
        "breath_db": None,
        "gain_db": 0.0,
    },
    "RITSUKO": {  # woman, thirty, level, dry, precise, lower and cooler than Misato
        "method": "vc+dsp",
        "vc_ref": {"pitch": 1.22, "formant": 1.04, "exaggeration": 0.30, "cfg": 0.45,
                   "colour": {"eq": "bass=g=2:f=220,treble=g=-3:f=4500,lowpass=f=9000"},
                   "text": "The results are in, and they are not what we expected. I have checked the figures twice. "
                           "Please be precise when you report this, because everything depends on the numbers being right."},
        "f0": 168, "pitch_lock": 0.0,
        "formant": 1.00, "dsp_formant": 1.08,
        "inflection": 1.0, "tempo": 1.0,
        "eq": None,
        "comp": None,
        "saturate": None,
        "breath_db": None,
        "gain_db": 0.0,
    },
    "GENDO": {    # man, late forties, low, slow, hard, almost no inflection
        "method": "vc+dsp",
        "vc_ref": {"pitch": 0.72, "formant": 0.93, "exaggeration": 0.25, "cfg": 0.5,
                   "colour": {"eq": "bass=g=4:f=120,treble=g=-3:f=6000"},
                   "text": "Sit down. I will say this once. You were not brought here to ask questions. "
                           "You were brought here because there is no one else, and that is the only reason."},
        "f0": 90, "pitch_lock": 0.0,
        "formant": 1.00, "dsp_formant": 0.93,
        "inflection": 1.0, "tempo": 1.0,
        "eq": None,
        "comp": None,
        "saturate": None,
        "breath_db": None,
        "gain_db": 0.0,
    },
    "REI": {      # girl of fourteen, very soft, breathy, flat, close
        "method": "vc+dsp",
        "vc_ref": {"base": "turbo", "pitch": 1.04, "formant": 1.20, "exaggeration": 0.20, "cfg": 0.5,
                   "colour": {"eq": "highpass=f=150,lowpass=f=8500", "breath_db": -17.0},
                   "text": "I understand. I will do as I was told. It does not hurt, and there is nothing I need. "
                           "Please do not worry about me, I am only tired."},
        "f0": 240, "pitch_lock": 0.0,
        "formant": 1.00, "dsp_formant": 1.27,
        "inflection": 1.0, "tempo": 1.0,
        "eq": None,
        "comp": None,
        "saturate": None,
        "breath_db": None,
        "gain_db": -2.0,
    },
    "BASE": {     # the base computer / public address: monotone, machine-processed
        "method": "dsp",                                   # always a pure DSP voice; no conversion
        "f0": 128, "pitch_lock": 1.0,
        "formant": 1.00, "dsp_formant": 1.03,
        "inflection": 0.0, "tempo": 1.0,
        "eq": "highpass=f=120,equalizer=f=1200:t=q:w=1:g=2,equalizer=f=2800:t=q:w=1:g=2",
        "comp": "acompressor=threshold=-24dB:ratio=5:attack=3:release=90:makeup=3",
        "saturate": {"drive": 1.5, "mix": 0.15},
        "machine": {                                       # applied to BASE only
            "lo_hz": 280, "hi_hz": 4200,                    # band-limit
            "comb_ms": "auto", "comb_gain": 0.33,            # the hollow ring; "auto" = one pitch period (1000/f0 ms) so it rings on every harmonic
            "ring_hz": 52, "ring_depth": 0.16,              # slight ring modulation
            "crush_bits": 0,                                # 0 = off; 10..12 for a gritty 'old computer'
        },
        "default_fx": "pa",                                # when the line has no recognised direction
        "breath_db": None,
        "gain_db": 0.0,
    },
}

# ------------------------------------------------------------------------------------------ directions
# The *(direction)* at the end of a script line picks the effects.  Rules are tried in this order; every rule
# that matches is applied, in this order (space first, then the transmission, then muffling).
DIRECTION_RULES = [
    (r"above|booth", "above"),
    (r"telephone|phone|handset", "phone"),
    (r"radio", "radio"),
    (r"intercom", "intercom"),
    (r"street|loudspeaker", "street"),
    (r"public address|\bPA\b|tannoy", "pa"),
    (r"cockpit|entry plug", "cockpit"),
    (r"through the (hull|wall|door)|next room|muffled", "muffled"),
]

FX = {
    "phone":    {"lo": 330, "hi": 3300, "drive": 2.2, "mix": 0.45, "noise_db": -50, "hum_hz": 50,
                 "comp": "acompressor=threshold=-24dB:ratio=4:attack=3:release=60:makeup=4"},
    "radio":    {"lo": 380, "hi": 3000, "drive": 3.0, "mix": 0.55, "noise_db": -44, "squelch": True,
                 "squelch_ms": 70, "squelch_level": 0.05,
                 "comp": "acompressor=threshold=-28dB:ratio=6:attack=2:release=80:makeup=5"},
    "intercom": {"lo": 300, "hi": 4200, "drive": 1.8, "mix": 0.35, "comb_ms": 2.2, "comb_gain": 0.22,
                 "noise_db": -52, "hum_hz": 60},
    "pa":       {"lo": 260, "hi": 5200, "drive": 1.6, "mix": 0.25, "rt60": 1.9, "wet_db": -5.0, "predelay_ms": 30,
                 "dark_hz": 3200, "early": [(95, 0.5), (210, 0.35)], "tail_s": 1.5},
    "street":   {"lo": 300, "hi": 4800, "drive": 2.0, "mix": 0.35, "rt60": 2.6, "wet_db": -3.5, "predelay_ms": 90,
                 "dark_hz": 2800, "early": [(180, 0.8), (400, 0.55), (640, 0.3)], "tail_s": 2.0},
    "above":    {"lo": 90, "hi": 7500, "rt60": 1.5, "wet_db": -7.0, "predelay_ms": 35, "dark_hz": 3400,
                 "early": [(60, 0.3), (140, 0.2)], "tail_s": 1.0, "gain_db": 0.0},
    "cockpit":  {"lo": 220, "hi": 5200, "comb_ms": 1.7, "comb_gain": 0.22, "rt60": 0.28, "wet_db": -9.0,
                 "tail_s": 0.3, "noise_db": -52},
    "muffled":  {"hi": 1700, "gain_db": -2.0},
}

