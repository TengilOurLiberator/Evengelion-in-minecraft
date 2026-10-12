# Generated score, ambience and effects (ACE-Step and Stable Audio Open through ComfyUI)

The procedural sounds in `tools/sound/` pass every numeric check but nobody has heard them. This folder replaces the ones their
author trusted least with audio from the same local models the Genesis project used for its score and effects
(`D:\genesis-vr\tools\make_audio.py`): **ACE-Step 1.5 turbo** (`ace_step_1.5_turbo_aio.safetensors`) for music and
**Stable Audio Open 1.0** (`stable-audio-open-1.0.safetensors` + `t5_base.safetensors`) for effects and ambience, driven through the
ComfyUI install at `D:\godtree-tools\ComfyUI_windows_portable` (same workflows, sampler settings and model paths; `comfy.py`).
Nothing was downloaded or installed. Python is `D:\voice-assistant\.venv\Scripts\python.exe`.

> **make_sound.py rebuilds overwrite these files.** The generated `.ogg`s sit at exactly the same paths as the procedural ones,
> and `make_sound.py` rewrites the procedural ones in place. After any rebuild run `python switch.py all generated`
> (the generated files are kept in `work/sound_candidates/<event>/cand<k>.ogg`). Nothing here edits `make_sound.py`, and
> `sounds.json` is never touched (same event names, same file names).

## Flip an event by ear

```powershell
$py = 'D:\voice-assistant\.venv\Scripts\python.exe'
cd D:\angel-attack\tools\sound\generate
& $py switch.py status                    # which version each replaced event plays now
& $py switch.py sfx.crash procedural      # one event back to the synthesised version
& $py switch.py sfx.crash generated
& $py switch.py music. procedural         # a prefix: music. / sfx. / amb. / music.launch ...
& $py switch.py all procedural            # everything back; `all generated` puts it all forward again
```

Switch `music.decision` + `music.decision_loop` together and `music.launch` + `music.launch_loop` together (a prefix such as
`music.launch` catches both) so the hand-off between the long file and its loop file stays seamless.
Reload resources in game (F3+T) or restart after switching.

## What is where

| Path | What |
|---|---|
| `prompts.json` | every prompt (ACE tags + bpm + key; Stable Audio text + negative text), lengths, per-event processing options and the profile each brief expects. `variants` hold the second-round prompts (candidates 4-6) |
| `gen.py` | generates the raw candidates, three seeds per prompt, one generation at a time |
| `finish.py` | raw audio to a candidate that meets the event's contract (below) |
| `evaluate.py` | speech check with `tools/voices/asr.py`, contract and profile checks, ranking, contact sheets |
| `choices.json` | which candidate was chosen per event and why; which events stayed procedural and why |
| `install.py` | backs up the procedural file, installs the chosen candidate, writes `installed.json` |
| `installed.json` | per installed event: candidate, seed(s), prompt, engine, processing log, hashes, sizes; plus `kept_procedural` |
| `switch.py` | procedural / generated switch |
| `comfy.py` | finds the ComfyUI install, checks the models, starts and stops it (only a ComfyUI that it started itself is ever stopped) |
| `D:\angel-attack\work\sound_candidates\` (git-ignored) | `raw/` (every generation with `gen.json`), `<event>/cand<k>.ogg/.json` (every finished candidate with its metrics and verdict), `contact_sheets/`, `procedural_backup/` (the replaced procedural files under their repo-relative paths) |

## The contract a candidate must meet (checked on the decoded .ogg)

* the same channel layout as the procedural file (mono stays mono) and exactly the same number of samples, so loop lengths are still
  whole game ticks and the datapack's recording-length lookup (`tools/story/audio.py`) is unchanged;
* integrated loudness within 0.5 LU of the procedural file (the project's own `dsp.lufs`), true peak below -1.0 dBTP (the finishing
  limiter works to -1.3 before Vorbis), no clipping, no DC;
* one-shots: leading silence trimmed (audible within 30 ms, measured at -60 dBFS), the event cut to its length, a short fade in
  and a fade out;
* loops: built circularly - the natural continuation of the tail is crossfaded into the head, so the last sample runs straight into
  the first (beds: equal-power crossfades of pieces from separate generations, spectrum and level matched first; pulsed music:
  tempo measured, Rubber Band time-stretch so the loop is a whole number of bars, loop cut on the beat grid, crossfade of 2-4 beats,
  start nudged 30 ms off the hit like the procedural loops). The join is verified with the same hf-ratio method as `analyze.py`;
* `music.decision` / `music.decision_loop` and `music.launch` / `music.launch_loop` share one gain, the loop is the tail of the long
  file, and `check_seams.py` correlation of long tail vs loop is 0.995-0.997;
* `music.launch`: the build is exactly 20.000 s and ends on the climax; the drive cycle is rolled (a circular roll cannot break a
  seamless loop) so its loudest kick starts on the first sample, i.e. at 20.0 s.

## Selection (cannot hear, so by evidence)

Rejected outright: contract failure, **words found by the project's faster-whisper helper** (once with its voice-activity filter, once
without; any word from the filtered pass rejects, which also catches hallucinated "Thanks for watching"-type text on music; three
music and four effects candidates fell to this), clipping, long silences. Scored down: a beat in a cue meant to have none, big level
swings or drift in a loop, steady narrow tone lines in sounds that should not be tonal (hum), profile outside the brief. Among the
survivors the choice was made by looking at the spectrogram of every candidate next to the procedural one
(`contact_sheets/<event>.png`, `_overview_*.png`; the chosen one is marked in green after `evaluate.py --sheets-only`).
Where no candidate matched the brief the procedural sound stays (`installed.json` -> `kept_procedural`).

## Reproduce

```powershell
& $py comfy.py start                 # no-op if ComfyUI already answers on 8188
& $py gen.py [event ...]             # raw candidates (skips ones that exist)
& $py finish.py [event ...]          # contract-matched candidates
& $py evaluate.py [event ...]        # ASR, verdicts, sheets
& $py install.py                     # backs up procedural files first, then installs choices.json
& $py comfy.py stop                  # stops ComfyUI only if comfy.py started it
```

GPU use is one generation at a time; ASR runs only after generation.
