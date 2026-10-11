# characters_bridge

Shinji speaks aloud; whichever of Misato, Ritsuko, Gendo or Rei he means answers in their own voice. A Python process
listens on the microphone (Silero VAD, faster-whisper), asks Claude for the reply in character, speaks it with
Chatterbox and talks to the Minecraft server over RCON. Same approach and environment as `D:\genesis-vr\companion`.

## Run

```
$py = "D:\voice-assistant\.venv\Scripts\python.exe"
& $py bridge.py --text              # terminal only: typed lines, no mic, no TTS, fake server (try this first)
& $py bridge.py                     # live: microphone + voices + the real server (needs the server running)
& $py bridge.py --mute              # live but silent (replies print and appear in game chat)
& $py bridge.py --text --live       # typed lines against the real server
& $py selftest.py                   # offline checks, no Claude/GPU/server needed
```

Useful flags: `--output Oculus` (speakers by name part or index; default is the Windows default device, so pick the
headset explicitly if that is where he listens), `--input`, `--list-devices`, `--model`, `--fresh` (forget earlier
conversations), `--no-subtitles`, `--verbose` (show every RCON command), `--script "line|/beat 52|line"` (with `--text`).

Text mode shows a small simulated world. Type what Shinji says; lines starting with `/` change the world:
`/beat N`, `/wait 0|1|2`, `/speaker misato`, `/present misato 0|1|2` (or `all`), `/talking 0|1`, `/look misato|away`,
`/place misato DIST [DEG]`, `/line gendo Some words` (a recorded line was heard), `/state`, `/forget`, `/help`, `/quit`.

## What it reads

* `D:\angel-attack\characters\<id>.md` : system-prompt core (a tiny built-in placeholder if missing).
* `D:\angel-attack\characters\beats.md` : parsed leniently (table rows, `## Beat N`, `N.`, `- N:`). Each character is told
  the current beat's entry and the two before it. Later beats are never shown, except that while the story is holding
  for an answer the single next entry is given as "do not reveal or hint, only do not contradict".
* `D:\angel-attack\voices\final\<SPEAKER>\*.wav` : the user's own processed recordings, used as the Chatterbox voice
  reference for that character (one 7-16 s clip, or several joined, is built into `cache\refs`). **Never use recordings
  of real actors or of the TV show; the code only ever reads from that folder.** Until it exists a character uses
  Chatterbox's built-in voice shaped by `VOICE_PROFILES` in `config.py` (pitch, pace, temperature, level; exaggeration and
  cfg_weight only take effect with `--tts standard`, because Turbo ignores them). Voice-only characters get a radio filter.
* `D:\angel-attack\server\server.properties` : RCON port and password (override: `ANGEL_RCON_HOST/PORT/PASSWORD`).

## Files

| File | Role |
|---|---|
| `rcon_commands.py` | **Every game command string, the scoreboard names, and the parsing of replies.** The datapack contract. |
| `bridge.py` | Entry point, text-mode console, live loop |
| `director.py` | Addressing, story gating, reply generation, memory |
| `addressing.py` | Who is Shinji talking to (pure functions) |
| `characters.py` | Sheets, beats, rolling memory, shared log, prompt building |
| `brain.py` | Claude Code processes (streamed replies, warm at start, recycled), consent classifier |
| `voice.py`, `output.py`, `ears.py` | Chatterbox voices and playback, sentence-by-sentence pipeline, microphone |
| `world.py`, `rcon_client.py`, `fake_rcon.py` | Game state reader, RCON client, text-mode stand-in server |
| `config.py` | Model (`claude-haiku-5-5`, or `ANGEL_MODEL`/`--model`), ranges, voices, aliases; optional `config.json` overrides |

`state.json` (rolling memory, so a restart does not make them forget; reset automatically if `#beat` goes backwards) and
`cache\` are created at run time.
