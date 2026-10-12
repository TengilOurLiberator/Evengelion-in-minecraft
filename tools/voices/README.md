# Voices

## The four characters are TTS now (`tts_lines.py`)

MISATO, RITSUKO, GENDO and REI are no longer the user's recordings: they are **Chatterbox text to speech, cloned from a short reference clip each**, and
the same four voices speak the scripted lines live in the character bridge (`characters_bridge`, which performs the lines when it is connected and
otherwise leaves the game to play the pre-rendered files made here).  BASE is unchanged (synthetic, DSP machine voice, `synth_base.py` + `transform.py`).
The user's own recordings are untouched but out of the pack: `voices\backup_user_recordings\` holds the old `final\<SPEAKER>` folders and the pack's
`sounds\line\<speaker>` oggs (and the old `sounds.json` / `durations.json` as `*.before`); `voices\raw` (the raw readings) was never moved.

```
$py = "D:\voice-assistant\.venv\Scripts\python.exe"
& $py tools\voices\tts_lines.py refs        # voices\tts_refs\<SPEAKER>.wav (+ refs.json) from the user's voice-converted recordings
& $py tools\voices\tts_lines.py tune        # measure settings on sample lines (voices\tts_tune.json); nothing else is written
& $py tools\voices\tts_lines.py render      # all 111 lines, dry, each transcribed back and re-rolled on a mismatch -> voices\tts_raw
& $py tools\voices\tts_lines.py rescore     # recompute the transcript similarities from the stored transcripts; lists what is still below 0.97
& $py tools\voices\tts_lines.py backup      # MOVE the old recordings (voices\final\<4>, the pack's four line folders) to voices\backup_user_recordings
& $py tools\voices\tts_lines.py install     # effects by direction + loudness -> voices\final, then pack_sounds.py (oggs, sounds.json, durations.json)
& $py tools\voices\tts_lines.py audition    # three varied lines per character -> voices\audition_tts\
& $py tools\voices\tts_lines.py report      # the measurements below -> voices\tts_report.json
```

* **References** (`voices\tts_refs\`, built by `refs`): the 2-4 cleanest, longest, effect-free lines of the user's voice-converted recordings
  (`voices\final`, or the backup) joined into one clip (`refs.json` names the lines).  Chosen by Whisper transcript match, calm pitch (p90/p10), no long
  pause, length.  GENDO has no effect-free line (all 13 are "from above" or "radio"), so his clip is re-rendered **dry** from his raw recording through the
  same voice conversion with no effect (`transform.render(..., direction="")`).  REI's clip is shaped (pitch 1.08, vocal tract 1.2, breath -12 dB: `tts_config.REF_SHAPE`):
  built from the same synthetic base as Misato's, the two cloned voices were 0.87 alike; shaped, 0.76.  **Hard rule: nothing but the user's own (converted)
  voice is ever a reference -- never a recording of a real actor or of the TV series.**
* **Settings** (`tts_config.py`, tuned by measuring, since a listener is not available): the standard Chatterbox model (Turbo ignores `exaggeration` and
  `cfg_weight`, the two knobs that make Rei breathe and Gendo drone) with per-character `exaggeration`, `cfg_weight`, `temperature` and a `tempo` (Rubber Band,
  pitch kept).  `tune` tried 3 x 3 of exaggeration x cfg weight on 6-8 lines per character; the numbers it printed (transcript match, words per second at tempo 1,
  median pitch, similarity to the reference, longest pause) decided: Misato 0.55 / 0.30 / temp 0.8 / tempo 1.10; Ritsuko 0.35 / 0.35 / 0.7 / 0.85; Gendo 0.10 / 0.45 / 0.6 / 0.82;
  Rei 0.20 / 0.40 / 0.6 / 0.80.  Higher exaggeration raised Misato's pitch and animation; lower kept Gendo at the reference's 88 Hz and made him slow; Rei needed some
  exaggeration to keep her voiced.
* **Rendering** (`render`): every line is spoken (up to 6 seeds, 24 for a single word), transcribed back with Whisper large-v3, and the best take kept;
  a take loses points for a stray whisper (no voiced speech), a pause over 1.3 s, a spike, a pace far outside the character's range.  Words are compared
  forgivingly (numbers spelled out, `ray` = Rei, `alright`).  `tts_config.RESPELL` can respell a word for the model without touching the script.
  REI's 5.31 has no words: it is a breath made from shaped noise (`tts_lib.breath_in`).
* **Finishing** (`install`): the effects are transform.py's, reused -- `transform.directions()` (the `DIRECTION_RULES` of `config.py`: radio, telephone, from
  above, intercom, cockpit, public address, ...), `fx.apply()` with `config.FX`, and `transform.finish()` (-19 LUFS, peaks under -1.5 dB, the same lead and tail) --
  but **not** its voice-conversion stage.  Rei keeps her `gain_db` of -2 (-21 LUFS: she is very soft).
* **Measured** (`report`, 111 lines): every take transcribes back at >= 0.97; median pitch REI 246 > MISATO 218 > RITSUKO 147 > GENDO 87 Hz; speech rate (words per
  second, silence at both ends trimmed) Misato 2.96, Ritsuko 2.82, Gendo 2.11, Rei 2.35; speaker similarity between two characters at most 0.77
  (Misato-Ritsuko), lowest 0.67; one character's lines are 0.93-0.95 alike on average (lowest line 0.80); finished lines at -19.0 LUFS median (Rei -21.0), highest peak
  -1.5 dB, no clipped sample, longest pause 1.3 s.
* After `install`, rebuild the story and the fight (`build_story.py`, `build_fight.py`): the scenes are timed from `voices\durations.json`, and `build_story.py --check`
  must still say 0 errors, 0 warnings.
* The modules: `tts_config.py` (all numbers), `tts_lib.py` (`Synth`, `master`, the word normaliser; imported by the bridge too), `tts_lines.py` (the commands).

## The older pipeline: one reader, five characters

The user reads every line in their own voice; this pipeline cuts the reading into lines and turns that one voice
into MISATO, RITSUKO, GENDO, REI and BASE. Same approach as Genesis (`D:\genesis-vr\work`): cut per line, keep the
best take, clean it, process it, encode to ogg for the resource pack.  (Used now for BASE and for the references of the TTS voices; the four human
voices are not made this way any more.)

Python is the shared environment, nothing is installed into it:
`D:\voice-assistant\.venv\Scripts\python.exe` (faster-whisper, chatterbox-tts, silero-vad, librosa, scipy, torchaudio,
pyloudnorm, soundfile). ffmpeg is found on PATH or in `D:\malmo-vr\tools\ffmpeg`. From the repo root,
`.\tools\voices\voices.ps1 <tool> <args>` runs a tool in the right Python; the commands below use that.

## Order of work

| Step | Command | Result |
|---|---|---|
| 1. Reading sheets | `voices.ps1 sheets` | `recording\<SPEAKER>.md`, one big-print sheet per character. Re-run whenever `script.md` changes. `voices.ps1 sheets --check` only parses. |
| 2. Hear the voices first | `voices.ps1 audition` (`--compare` adds the plain-DSP version of each, `--refs` rebuilds the conversion targets, `--no-verify` skips the Whisper and speaker checks) | `voices\audition\<SPEAKER>.wav` plus `BASE__radio`, `MISATO__radio`, `RITSUKO__phone`, `GENDO__above`, and `_report.json` |
| 3. Record | the user reads one sheet top to bottom, 2 s of quiet between lines, a flubbed line is simply read again | one long wav per character |
| 4. Cut | `voices.ps1 cut_takes D:\path\MISATO_reading.wav --speaker MISATO` | `voices\raw\<SPEAKER>\<id>.wav` and `_report.md` (missing, low-confidence, "check by ear") |
| 4b. Pick-ups | `voices.ps1 cut_takes pickups.wav --speaker MISATO --ids 2.01,5.07` | replaces just those lines, merges the report |
| 5. Transform | `voices.ps1 transform` (`--speaker`, `--ids`, `--force`, `--method dsp`) | `voices\final\<SPEAKER>\<id>.wav` (mono 48 kHz 24 bit, all at -19 LUFS) |
| 6. Pack | `voices.ps1 pack_sounds` | oggs in `pack\angel-resources\assets\angel\sounds\line\<speaker>\<id_>.ogg`, `assets\angel\sounds.json`, `voices\durations.json` |

Play a line in game with `/playsound angel:line.misato.2_01 voice @a`. `pack_sounds` keeps any `sounds.json`
entries that do not start with `line.` and does not touch `pack.mcmeta`.

`voices.ps1 selftest` runs the whole chain (cut, transform, pack) on a made-up session in a temp folder.
`voices.ps1 selftest --real GENDO,BASE,REI` reads the real sheets in `script.md` with Chatterbox's own synthetic
voice (flubs, repeats, a skipped line) and checks `cut_takes` against them.

## Tuning by ear: `config.py`

Everything per character lives in `config.py` (target pitch `f0`, `formant`, `inflection`, `tempo`, EQ, compression,
saturation, breath, loudness) with a comment block at the top explaining each number. After a change run `audition`
(a minute) to hear it, and `transform --force` to redo the recorded lines. `DIRECTION_RULES` and `FX` there map the
`*(direction)*` on each line to radio / telephone / intercom / public address / street loudspeakers / cockpit /
"from above" / muffled. BASE with no recognised direction gets the PA-reverb variant; `radio` gives the radio variant.

## How the voices are made

Human voices (default `vc+dsp`): clean up, then **Chatterbox voice conversion** re-speaks the line in a synthetic target
voice, then **PSOLA + Rubber Band** set the pitch, vocal-tract (formant) size and amount of inflection, then tempo, EQ,
compression, optional saturation / breath noise, then the transmission effect, then loudness. Plain `dsp`
(Rubber Band + PSOLA only) is available per character or with `--method dsp` for comparison.
BASE is always DSP: pitch flattened to a monotone, band-limited, short comb (rings on the pitch harmonics), slight ring
modulation, then PA reverb or radio.

Conversion targets (`voices\refs\*.wav`) are **synthetic**: Chatterbox's own built-in voices (the standard model's and the
Turbo model's defaults) speak a few sentences, DSP reshapes pitch and formants (and for some characters EQ / breath noise),
and Chatterbox re-speaks a passage in that shaped voice to get clean natural speech. No recording of any real person
other than the user, and nothing from the original show, is used as a target or reference. Chatterbox adds its own
inaudible watermark to converted audio; it is left in place.

## Files

`script_lines.py` parser and sheets | `cut_takes.py` | `transform.py` | `pack_sounds.py` | `audition.py` | `config.py` |
helpers: `common.py` (paths, audio, pitch measurement), `dsp.py` (PSOLA, breath, comb, ring, reverb), `fx.py` (named
transmission effects), `asr.py` (faster-whisper), `speaker_embed.py` (speaker-similarity check), `selftest.py`.

## Notes and limits

- `cut_takes` needs the GPU for Whisper large-v3 (CPU fallback is slow). It caches the transcription in `_words.json`.
- Lines are matched by fuzzy text; one-word lines are the weak spot (Whisper mishears "Why?"). Those that cannot be
  matched are taken by position and flagged `low`; always listen to anything the report lists.
- `transform` takes about 4 to 8 seconds per line (pitch tracking dominates); 135 lines is roughly ten minutes.
- Re-running `transform.py --make-refs` changes the synthetic targets (the voices shift slightly); only do it deliberately.
