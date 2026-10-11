# Voices: one reader, five characters

The user reads every line in their own voice; this pipeline cuts the reading into lines and turns that one voice
into MISATO, RITSUKO, GENDO, REI and BASE. Same approach as Genesis (`D:\genesis-vr\work`): cut per line, keep the
best take, clean it, process it, encode to ogg for the resource pack.

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
