# characters_bridge

Two jobs, one process.

1. **Talk.** Shinji speaks aloud; whichever of Misato, Ritsuko, Gendo or Rei he means answers in their own voice.  A Python process listens on the
   microphone (Silero VAD, faster-whisper), asks Claude for the reply in character, speaks it with Chatterbox and talks to the Minecraft server over RCON.
2. **Perform the script.** When the story reaches a scripted line of one of the four, the game does not play a file: it *cues* the bridge over RCON, the
   bridge says the line in that character's TTS voice -- re-voiced a little by Claude where the script allows it, given what Shinji just said -- and
   the story waits until the bridge says it is finished.  With no bridge running the game plays the same lines from pre-rendered TTS files and everything
   still works (and still times the same).

Same approach and environment as `D:\genesis-vr\companion`.

## Run

```
$py = "D:\voice-assistant\.venv\Scripts\python.exe"
& $py bridge.py                     # live: microphone + voices + the real server; performs the scripted lines
& $py bridge.py --verbatim          # ... but every scripted line exactly as written (no Claude re-voicing; the pre-rendered take of each line is played)
& $py bridge.py --no-lines          # ... talk only; no heartbeat, so the game plays its own pre-rendered files (the same as not running the bridge for the lines)
& $py bridge.py --mute              # live but silent (replies print and appear in game chat; the scripted lines are claimed and timed, silently)
& $py bridge.py --text              # terminal only: typed lines, no mic, no TTS, fake server (try this first)
& $py bridge.py --text --live       # typed lines against the real server (the scripted lines are performed silently; add --synth to synthesise re-voiced ones)
& $py bridge.py --story-test        # scenes 1-6 through a fake game, real synthesis, a report per line (below)
& $py selftest.py                   # offline checks, no Claude/GPU/server needed (adapter rules, look-ahead, the handshake with a fake game)
& $py livetest.py                   # the handshake against a scratch server (own temp folder, ports 25605/25615, deleted afterwards)
```

Useful flags: `--output Oculus` (speakers by name part or index; default is the Windows default device, so pick the headset explicitly if that is where he
listens; the mixer opens WASAPI shared so a line starts about 20 ms after the bridge asks), `--input`, `--list-devices`, `--model`, `--fresh` (forget earlier
conversations), `--no-subtitles`, `--verbose` (every RCON command and every cue), `--steps FILE` (the story's step listing), `--no-asr-check`, `--one-model`
(one Chatterbox for replies and look-ahead: less GPU memory, but a reply can wait behind a look-ahead line), `--dry` (scratch-server variant of the story: a
mannequin is the player), `--script "line|/beat 52|line"` (with `--text`).

`start.ps1` starts the bridge without options: set `$env:ANGEL_BRIDGE_ARGS = "--verbatim"` (or `--no-lines`, `--output Oculus` ...) before running it and they are added.

Text mode shows a small simulated world. Type what Shinji says; lines starting with `/` change the world:
`/beat N`, `/wait 0|1|2`, `/speaker misato`, `/present misato 0|1|2` (or `all`), `/talking 0|1`, `/look misato|away`,
`/place misato DIST [DEG]`, `/line gendo Some words` (a scripted line was heard), `/state`, `/forget`, `/help`, `/quit`.

## The handshake with the game

Everything is on the scoreboard objective `angel.story`; the commands are in `rcon_commands.py`, the datapack side in `tools\story\lines.py` and `system.py`
(and `tools\story\README.md`).

| score | written by | meaning |
|---|---|---|
| `#bridge_hb` | the bridge, `set 20` every 0.25 s; the game counts it down every tick | the heartbeat: above 0 = a bridge spoke in the last second |
| `#cue` | the game | `cue number * 1000 + #line` (`#line` = scene * 100 + number, so `2207` is cue 2, line 2.07): one number, one RCON read |
| `#cue_ack`, `#line_left` | the bridge, with `function angel:say/claim {n:<cue>,ticks:<real length>}` | the claim: the cue taken, and the REAL length of what will be said |
| `#talking` | the game | 1 from the cue until `#line_left` has counted down to 0 |
| `#cue_fb` | the game | 1 if the game took the cue over and played the file |

1. The story reaches a `say` step.  **Heartbeat alive:** the game sets `#cue`, `#talking 1`, `#line_left` = the file's length + 3 s, and plays nothing.
   **No heartbeat:** it plays the file (`say/file/<key>`) -- the whole old behaviour, including the sound being positioned at the speaker.
2. The bridge polls `#cue` every 20 ms on its own RCON connection (`conductor.py`).  A new number: it takes the audio for that line (below), runs the
   claim (atomic in the game: refused if the cue was taken over or is over), reads `#cue_ack` back, and only then starts the sound (`playback.Mixer`, one
   always-open output, so a start is one audio block).  Measured: the bridge's part is ~1 ms in the fake game; against the scratch server see `livetest.py`'s report.
3. **Who ends the line: the engine.**  The claim wrote the real length (+ the 4-tick tail every line has + 1) into `#line_left`; `t_line` counts it down and
   releases `#talking`.  I chose this over "the bridge sets `#talking 0` when it finishes" because it cannot hang: kill the bridge in the middle of a line and
   the clock releases the story when the reported length is up; the audio just stops.
4. **The watchdog.**  Before the claim `#line_left` holds the file's length + 3 s.  A cue not claimed within 14 ticks (0.7 s) or whose heartbeat has stopped is **taken over
   by the game**, which plays the pre-rendered file at once; the bridge then finds its claim refused and says nothing.  So: no gap if the bridge is slow, no double
   line, and a dead bridge is noticed within a second.
5. If the story cuts a line (`angel:story/next`, a scene jump, `stop`) `#talking` falls to 0 early; the bridge sees it within 150 ms and stops the audio.
6. A scripted line that starts while the bridge is voicing a live reply cuts the reply (as a recorded line always did); an utterance that arrives while a
   scripted line plays is held until it ends, then dropped after `talk_wait` (as before).  The consent classifier, addressing, the `#bridge_speaking` signal
   (which hides the speak prompt) and the live replies at waits are exactly as they were.
7. Fight barks (`7.01`-`7.20`) are never cued: the fight plays the pre-rendered files itself (`say/file/7_NN`).
8. **One RCON connection.**  The vanilla server keeps ONE response buffer for all RCON clients, so two clients running a command at the same moment get each
   other's text back (found the hard way in `livetest.py`).  The bridge therefore shares a single connection between the Director, the cue loop and the look-ahead
   (the connection object serialises them) and `rcon_commands.parse_score(reply, name)` accepts a score reply only if it names the score asked for.  Another
   client (`tools\rcon.py`, `tools\live_guide.py`) is safe in between but should not hammer the server while the bridge plays.
9. The step listing (`cache\steps.json`) is the story as it was when the bridge started: rebuild the story and restart the bridge together.

## Verbatim or adapted: `line_policy.py`

The script text is the **intent** of a line.  `line_policy.py` lists the 61 lines that must be spoken as written (and so are the pre-rendered take, with exactly
`durations.json`'s length) and the 50 that Claude may lightly re-voice.  `build_story.py --check` fails if a line is in neither table, in both, or if a scene schedules
anything against the length of an adaptable line (it finds those by watching which lengths the scenes read while they build: 11 lines, all verbatim).

| why verbatim | lines |
|---|---|
| a cue: something happens on the line | 1.04, 2.06, 5.06, 5.25, 5.26, 5.27, 6.10, 6.12 |
| the count / the launch / the reveal | 2.09 "One. Two. Three!", 6.19 "Evangelion Unit One: launch!", 3.08 "look out of your window" |
| timed: a scene schedules effects against the length | 2.12, 2.13, 2.14, 2.16 (the call), 5.28, 5.29 (the gurney), 6.16, 6.17, 6.18 (the launch) |
| the consent nudges | 1.06, 5.39, 5.41 |
| staging built around the exact beat | 2.05, 5.31 (a breath, no words), 5.33 |
| call and response / callbacks | 4.15, 4.16, 4.17, 4.18, 5.10 ("One" = a pilot; re-voiced out of context it became "Unit One") |
| single words and lines of five words or fewer | 2.07, 4.07, 4.08, 5.04, 5.11, 5.15, 5.17, 5.22, 5.23, 5.35, 5.38, 5.42, 5.44 |
| fight barks (played by the game) | 7.01-7.09, 7.11-7.14, 7.16-7.18, 7.20 |

Everything else is adaptable (the BASE computer is never performed by the bridge).

## How a line gets re-voiced (`conductor.py`, `adapter.py`, `prepare.py`)

* **Look-ahead.**  A watcher reads `#scene`, `#step`, `#wait` every 0.25 s.  `storybook.py` holds the step listing (`build_story.py --steps`, rebuilt when the story's
  sources are newer) and walks it forward from the current step -- through both ways of a branch, across hand-overs -- to find the lines the story will cue next.  The
  pre-rendered take of each is loaded at once (a cue is then a memory read).  Lines *before the next wait* have a known context and are adapted now (at the start of
  a scene, or when the previous wait ended); lines *after* a wait are adapted the moment the player's answer is known -- the Director hands the words over before the
  character has begun her own reply.  A wait that ends with no answer (the safety net, a skip) is context too.
* **The ask.**  One Claude (a dedicated "adapter" Brain with all four character sheets in its system prompt, never the minds that answer the player) gets the group of
  adaptable lines of the stretch with the fixed lines between them and the next three fixed lines, plus: what has been said recently (scripted and live), what Shinji said at the
  wait and how long he took, or that he said nothing.  Rules in the prompt: keep the meaning, the facts, the job in the conversation (a question stays a question) and who
  is addressed; **within 20 % of the words**; keep every name and number and the policy's `keep` words; a light touch -- change only where what he said or did makes it
  natural, otherwise return the line unchanged; never add plot, never contradict or pre-empt the later lines, never answer for whoever was asked; the character's register
  (Gendo states, Rei is brief); spoken words only.
* **The checks** (`adapter.validate`), all in code, before anything is voiced: word count in `[ceil(0.8 n), floor(1.2 n)]`; every digit, number word, capitalised
  non-initial word and `keep` word still present; no brackets, markup, quotation marks, no mention of an AI, a script, a game; no new digits; an unchanged line is simply
  not adapted.  After synthesis: the take is transcribed back (Whisper large-v3; up to three seeds; similarity >= 0.9), has no pause over 1.4 s, and is between 0.55 and 1.45
  times the length of the pre-rendered take.  Anything that fails leaves the line as written.
* **Synthesis** runs on its own Chatterbox (a second copy, so a live reply is never queued behind it, and it steps aside while a reply is being synthesised),
  with the character's settings, then `tts_lib.master`: the effect of the line's direction (radio, telephone, from above, intercom, cockpit, public address -- transform.py's rules,
  so an adapted radio line still sounds placed) and the shared -19 LUFS.
* **Never late, never gapped.**  At the cue the bridge takes the adapted take if it is *ready*, else the verbatim take; there is no waiting.  `--verbatim` switches all
  of it off (no adapter Claude, no second Chatterbox).

## The voices

`voice.py` is a thin wrapper of `tools\voices\tts_lib.py`: the SAME four voices as the pre-rendered lines (`tools\voices\tts_config.py`: reference clip, exaggeration, cfg
weight, temperature, tempo), so a live reply, an adapted line and a pre-rendered one are one person.  A reply to someone who is only a voice on the radio (presence 2)
gets the `radio` effect.  **Hard rule: a voice reference is only ever the user's own (voice-converted) recording; never a recording of a real actor or of the TV series.**
`tools\voices\README.md` has how the references were chosen and the measurements.

## What it reads

* `D:\angel-attack\characters\<id>.md` : system-prompt core (a tiny built-in placeholder if missing).
* `D:\angel-attack\characters\beats.md` : parsed leniently (table rows, `## Beat N`, `N.`, `- N:`). Each character is told the current beat's entry and the two before
  it. Later beats are never shown, except that while the story is holding for an answer the single next entry is given as "do not reveal or hint, only do not contradict".
* `D:\angel-attack\voices\tts_refs\<SPEAKER>.wav` : the reference clips; `voices\final\<SPEAKER>\<id>.wav` : the pre-rendered takes (played for verbatim lines and as the fallback).
* `D:\angel-attack\script.md`, `line_policy.py`, `cache\steps.json` (the step listing).
* `D:\angel-attack\server\server.properties` : RCON port and password (override: `ANGEL_RCON_HOST/PORT/PASSWORD`).

## Files

| File | Role |
|---|---|
| `rcon_commands.py` | **Every game command string, the scoreboard names, and the parsing of replies.** The datapack contract. |
| `bridge.py` | Entry point, text-mode console, live loop, `Performance` (builds the look-ahead and the conductor) |
| `conductor.py` | The cue loop (heartbeat, poll, claim, play, cut), the watcher and the look-ahead / planning |
| `prepare.py`, `adapter.py`, `line_policy.py`, `storybook.py` | Having lines ready (verbatim takes, re-voiced + synthesised ones), the Claude re-voicing and its checks, the verbatim / adaptable table, the script and the step listing |
| `playback.py` | The always-open audio output with a line slot and a reply slot; a null version for tests |
| `director.py` | Addressing, story gating, reply generation, memory |
| `addressing.py` | Who is Shinji talking to (pure functions) |
| `characters.py` | Sheets, beats, rolling memory, shared log, prompt building |
| `brain.py` | Claude Code processes (streamed replies, warm at start, recycled), consent classifier |
| `voice.py`, `output.py`, `ears.py` | Chatterbox voices (tools\voices\tts_lib), sentence-by-sentence reply pipeline, microphone |
| `world.py`, `rcon_client.py`, `fake_rcon.py` | Game state reader, RCON client, text-mode stand-in server |
| `storysim.py`, `story_test.py`, `livetest.py`, `selftest.py` | The fake game and walker, the `--story-test` report, the scratch-server test, the offline checks |
| `config.py` | Model (`claude-haiku-5-5`, or `ANGEL_MODEL`/`--model`), ranges, aliases; optional `config.json` overrides |

`state.json` (rolling memory, so a restart does not make them forget; reset automatically if `#beat` goes backwards) and `cache\` are created at run time.
