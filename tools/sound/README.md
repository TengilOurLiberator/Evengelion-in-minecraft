# Sound design: ambience, effects and score, synthesised in Python

Everything the player hears apart from the spoken lines is generated here from oscillators, noise, FM, modal
resonators, Karplus-Strong delay loops and synthetic room impulse responses. Nothing is sampled, nothing is a recording,
and nothing imitates a known piece of music or a known sound effect: the score is generic dread-and-drive language
(drones, ostinatos, taiko-ish percussion, pads, bell tones) in my own notes, in D.

Python is the shared environment, nothing is installed into it: `D:\voice-assistant\.venv\Scripts\python.exe`
(numpy, scipy, soundfile, numba, pyloudnorm, Pillow). ffmpeg (libvorbis) is found the way
`tools/voices/common.py find_tool` does it. `matplotlib` is not available, so the previews are drawn with Pillow.

## Rebuild

From `D:\angel-attack\tools\sound`:

```powershell
$py = 'D:\voice-assistant\.venv\Scripts\python.exe'
& $py make_sound.py                       # everything, in parallel (about one minute on 16 cores)
& $py make_sound.py sfx.mine amb.hq       # just these
& $py make_sound.py music                 # a family (amb | sfx | music) or any name prefix (sfx.breaker, sfx.car)
& $py make_sound.py --list                # what exists, with loudness targets
& $py make_sound.py --table               # the manifest as a markdown table
& $py analyze.py                          # previews + report.md/json for every sound (add --sheet sfx music amb for contact sheets)
& $py check_seams.py                      # the long-file -> loop-file hand-offs
```

A rebuild is deterministic: every sound is seeded from its own name, so changing one never changes another.

| File | Role |
|---|---|
| `make_sound.py` | registry runner: render, loudness-set, limit, encode (libvorbis), verify the decoded ogg, write `sounds.json` and `manifest.json` |
| `reg.py` | `@sound("sfx.card", peak=-4, ...)` registry |
| `dsp.py` | toolkit: coloured noise, zero-phase `eq`, numba state-variable filter, band-limited additive oscillator, FM, modal bank, Karplus-Strong/comb, impulse responses (`SPACES`), circular convolution, limiter, loudness |
| `blocks.py` | reusable sound-design pieces: bell/bar/plate/drum/glass modal bodies, creaks, squeals, scrapes, engines, blast, debris, birds, vowel choir, brass, pad |
| `amb.py` | the 11 ambience beds |
| `sfx_world.py` / `sfx_base.py` / `sfx_fight.py` | effects: outside world and vehicles / fortress, cage, plug / launch, fight, cross, cues |
| `music.py` | the 12 cues (plus the two loop exports) |
| `analyze.py` | previews and automatic checks; `preview/` is regenerable and git-ignored (`tools/sound/.gitignore`) |
| `manifest.json` | per sound: seconds, ticks (x20), channels, loop flag, LUFS, true peak, markers (`bloom_s`, `loop_start_s`, ...) |

## What is written

* `pack/angel-resources/assets/angel/sounds/{sfx,amb,music}/*.ogg`, 44.1 kHz Vorbis (beds and music q4/q5 stereo, effects q6,
  mono unless the sound is non-positional and wants width).
* `pack/angel-resources/assets/angel/sounds.json`: only entries whose key starts `sfx.`, `amb.` or `music.`. The file is re-read
  immediately before writing, every other entry (the `line.*` voice events) is kept as is, the write is atomic, and the script
  asserts that the `line.*` count did not change. `tools/voices/pack_sounds.py` does the mirror image (it keeps everything that is
  not `line.*`), so the two can run in either order.
* Each event is `angel:<family>.<name>` and points at `angel:<family>/<name>`. Beds, music and the two long effects (siren, cross)
  are `"stream": true`; positional effects carry an `attenuation_distance` by role (12 for a phone handset up to 128 for a far blast).
  `sfx.bolt` is an event with three sounds (picked at random); `sfx.bolt_1..3` and `sfx.breaker_1..3` are also events of their own.

## Playing it

Minecraft cannot loop a sound event, so loops are replayed by the datapack: `manifest.json` lists `ticks` for every file and every
loop length is a whole number of game ticks, so a replay scheduled every `ticks` ticks (or when the previous copy ends) is exact.
No loop needs a crossfade: the last sample runs straight into the first (see Loops).

```mcfunction
playsound angel:amb.cicadas ambient @a ~ ~ ~ 1 1 1       # repeat every 960 ticks
playsound angel:sfx.mine master @a ~ ~ ~ 4 1 1           # one-shot, stereo: plays at the player
playsound angel:music.descent music @a ~ ~ ~ 1 1 1       # one-shot; the bloom is at 8.0 s = tick 160
```

Stereo files are not spatialised by Minecraft (they play in the head); mono files are panned and attenuated. Stereo is used for
the beds, the music and these non-positional or "everywhere" effects: `card, mine, ears_ringing, launch*, beam_*, air_open,
door_boom, impact_above*, hand_rise, contact, sync_rise, fluid_fill, cross`. Everything else is mono and positional.
A 36 Hz sub is below what a headset speaker reproduces, so every low hit also carries 2nd/3rd harmonics (saturation) to be felt as pitch.

### Hand-offs and exact-time sounds

| Sound | What the datapack should know |
|---|---|
| `sfx.mine` | exactly 9.000 s. Whine 0.0-0.4 s, **digital silence 0.4-2.4 s** (verified on the decoded ogg: below -200 dBFS), blast onset at 2.400 s, tail to 9.0 s. Peak -1.2 dBTP |
| `music.descent` | 50 s one-shot, **bloom onset at 8.000 s** (energy +25 dB within 0.6 s; measured by `analyze.py`), a held-breath dip at 7.4-7.9 s before it |
| `music.decision` then `music.decision_loop` | the heartbeat tightens from 48 to 104 bpm over the first 90 s; the last 13.85 s of `music.decision` are the same audio as `music.decision_loop` (correlation 0.99); start the loop when the long file ends |
| `music.launch` then `music.launch_loop` | exactly 20.0 s of build (12 bars at 144 bpm), then the 26.65 s drive cycle twice; the loop file is the cycle (correlation 0.998) |
| `sfx.launch` then `sfx.launch_roar` | `sfx.launch` is the kick plus a rising turbine tone over the roar and ends in phase with the start of `sfx.launch_roar` (6.0 s, loops until cut) |
| `sfx.alarm_loop` / `sfx.alarm_cut` | the cue sheet's alarm: loop the first, play the second to stop it dead (same two tones, 700/940 Hz) |
| `sfx.breaker`, `_1.._3` | 1.2 s each; four slightly different contactors/hums (pitch, timing, flicker) for the five banks |

Extras that the cue sheet mentions but the event list did not: `sfx.alarm_loop`, `sfx.car_alarms_far` (cue 1), `sfx.chains` and
`sfx.lake_ring` (cue 5.21), `sfx.breathing` (cue 6, own breathing), `sfx.launch_roar` and the two music loop files.

## Loudness

Dialogue is -19 LUFS integrated. Targets here: ambience beds -34 to -31 LUFS, music -28 to -24 LUFS (loudest cues are the fight and
launch at -24.5/-24.2), effects by role: transients are set by sample peak (impacts -4 to -1.5 dBFS, doors and mechanisms -14 to -6,
quiet details such as the phone and the car door about -13), sustained ones by LUFS (breakers -20, siren -26, launch roar -17).
True peak is limited to -1.25 dBTP before encoding (-1.08 for the mine) and verified on the **decoded ogg**: every file is under -1.0.
`music.fight` etc. are gain-normalised only (no limiter), the effects use a look-ahead limiter.

## Loops

Seamless by construction, then checked on the decoded ogg:

* noise beds are generated in the frequency domain (periodic by definition) and shaped with zero-phase FFT equalisers; slow
  modulation is a periodic cubic spline or an integer-cycle LFO; steady tones are nudged to complete whole cycles (`lockf`);
  oscillators with moving pitch use `phase_of(..., loop=True)`; moving filters run on a tripled copy and the middle is kept;
* events (bells, drips, bird calls, rail clacks, alarms, kicks) are placed with `wrap=True` so their tails continue past the end
  onto the start; reverbs on loops are circular convolutions;
* music loops nudge every event 30 ms late so no hit sits exactly on the join.

`analyze.py` looks at the >2 kHz part of the signal within +-0.5 ms of the join, compares it with the 99.9th percentile of the same
quantity over the whole file (ratio <= 1 means the join is no more prominent than any other place) and flags loop lengths that are
not whole ticks. All 25 loops pass (ratio 0.01-1.07). Vorbis encoding adds a tiny edge artefact to near-silent, low-passed beds;
`amb.plug` and `amb.plug_flooded` carry a faint -54/-56 dBFS hiss floor for that reason.

## How each family is made

* **Ambience.** `cicadas`: 40 impulse-train voices (70-190 Hz pulse rate) through narrow resonances at 3.6-7.4 kHz, individually gated,
  some with "min-min" pitch wobble, under slow chorus swells. `town_empty`: gusting pink wind, a Q-30 whistle riding the gusts, a
  60 Hz hum, an aeolian wire, and a two-pitch crossing bell (modal bell, open-air echoes) twice. `car_interior`: a 4-cylinder
  harmonic engine with irregular firing at 2300 rpm, road and wind noise, joint thumps, all through a cabin EQ. `tunnel`: brown rumble,
  38 rail joints each four modal clacks (two bogies) in a tunnel IR, pressure whooshes. `geofront`: airy noise, a waterfall made of
  random-AM noise in a 9 s cavern IR, five synthesised bird phrases. `hq`: duct comb resonance, a 341 Hz fan tone, 60/120/180 Hz hum,
  a beating 3.9 kHz ballast pair. `lake`: beating sub-hum, lapping noise from two incommensurate cadences, bubble chirps, drips in a
  flooded-chamber IR. `cage`: sub room tone with a 41.2 Hz line, far bubble clusters and metal ticks in a 7.5 s hangar IR. `plug`: a
  capsule IR, a 1 Hz machine pulse (pitch-dropping sine plus filtered noise), a 3.1 kHz whine; `plug_flooded` is the same with everything low-passed to about 260 Hz and
  bubbles. `city_night`: gusting wind with moving canyon whistles, a far two-tone warble and a car alarm in a city IR with discrete echoes, one far thud.
* **Effects.** Impacts are layered: a noise crack, a falling-low-pass fireball, a pitch-dropping sub with saturation, hill echoes
  as delayed low-passed rumble, debris as Poisson ticks, and modal plates/bars for anything metal (`blocks.plate`, `steel_bar`,
  `bell`, `drum`). Creaks are stick-slip sawtooth buzzes with random pitch jitter through a moving resonance. Engines are band-limited
  harmonic stacks at the firing frequency. The Doppler pass of the jet is an analytic curve applied to oscillator pitch and filter cutoff.
  Rooms are synthetic IRs (`dsp.SPACES`: capsule, booth, room, corridor, tunnel, flooded, hangar, cavern, hall, cathedral, plate, city, open).
  The mine is the 0.4 s whine, exact zeros, then a 6.6 s blast (size 2.2) widened to stereo and put through the city IR.
  The groan in `hand_rise` and the grunt in `giant_hit` use the vowel choir: detuned harmonic voices through formant filters morphing between oh and ah.
* **Score.** Hand-composed note and rhythm data in `music.py`, rendered by additive/FM/modal instruments into a stereo bus with a reverb send.
  `dread`: D1 sub heartbeat every 4 s, a six-voice cluster (D Eb A Ab) swelling once per loop, reversed plate swells, a thin 1975 Hz pair.
  `road`: 3+3+2 FM-mallet ostinato over plucked bass, chord roots Dm - Bb - Gm - A every 8 bars. `descent`: out of silence with an
  overtone ladder and rising noise, a held breath, then the bloom (wide D chord, choir, bell, sub) and D-lydian bells. `cage`: a cold open-fifth pad
  with a ninth and E5 -> D5 glass bells. `father`: D2 over a D1 floor and an A6 pair, breathing over 20 s. `decision`: heartbeat accelerating
  with a creeping semitone ladder, a growing cluster and noise. `resolve`: the cluster resolves by semitones into D major add9. `launch`: taiko density doubling,
  rising noise and tone, brass-like swells, then a 16-bar low-brass ostinato drive. `fight` / `fight_final`: 152 / 172 bpm, kicks, tom
  accents, cannon-snare, chromatic low-brass ostinatos, minor-second and tritone stabs, a break-down section, a high mallet 16th ostinato and a rising siren-like tone in the final one.
  `victory`: wind, slow bells, a D major add9 chord blooming from nothing, shimmer. `defeat`: a blow, a detuned cluster falling as its filter closes.

## Checking by eye

`analyze.py` writes `preview/<name>.png` for every sound: waveform (L blue, R orange), short-term level in dB, a log-frequency
spectrogram (30 Hz-20 kHz, 80 dB), and for loops a zoom of the join. `report.md` lists LUFS, true peak, loop-join ratio and flags
(clipping, DC, true peak > -1, truncated tails, wrong durations, `mine` silence window and onset, `descent` bloom time, loop ticks).
Currently 0 flags. **None of this has been auditioned by ear**; see "least confident" in the hand-over notes.

## Event table (from `manifest.json`)

| event | seconds | ticks | ch | LUFS | true peak | loop | notes |
|---|---|---|---|---|---|---|---|
| `amb.cage` | 60.00 | 1200 | 2 | -33.5 | -15.1 | loop |  |
| `amb.car_interior` | 40.00 | 800 | 2 | -32.1 | -18.0 | loop |  |
| `amb.cicadas` | 48.00 | 960 | 2 | -32.2 | -18.3 | loop |  |
| `amb.city_night` | 56.00 | 1120 | 2 | -32.1 | -15.2 | loop |  |
| `amb.geofront` | 56.00 | 1120 | 2 | -33.7 | -20.4 | loop |  |
| `amb.hq` | 40.00 | 800 | 2 | -33.1 | -21.5 | loop |  |
| `amb.lake` | 48.00 | 960 | 2 | -32.1 | -14.8 | loop |  |
| `amb.plug` | 32.00 | 640 | 2 | -33.1 | -21.2 | loop |  |
| `amb.plug_flooded` | 32.00 | 640 | 2 | -33.0 | -17.2 | loop |  |
| `amb.town_empty` | 50.00 | 1000 | 2 | -33.1 | -14.2 | loop |  |
| `amb.tunnel` | 40.00 | 800 | 2 | -31.0 | -16.9 | loop |  |
| `music.cage` | 80.00 | 1600 | 2 | -27.0 | -13.2 | loop |  |
| `music.decision` | 103.85 | 2077 | 2 | -26.0 | -10.2 |  | loop_start_s=90.0, loop_seconds=13.85 |
| `music.decision_loop` | 13.85 | 277 | 2 | -26.0 | -14.1 | loop |  |
| `music.defeat` | 8.00 | 160 | 2 | -25.0 | -9.1 |  |  |
| `music.descent` | 50.00 | 1000 | 2 | -26.0 | -10.9 |  | bloom_s=8.0 |
| `music.dread` | 72.00 | 1440 | 2 | -26.0 | -12.9 | loop |  |
| `music.father` | 60.00 | 1200 | 2 | -28.0 | -18.6 | loop |  |
| `music.fight` | 63.15 | 1263 | 2 | -24.5 | -10.3 | loop |  |
| `music.fight_final` | 67.00 | 1340 | 2 | -24.2 | -8.8 | loop |  |
| `music.launch` | 73.30 | 1466 | 2 | -24.5 | -8.4 |  | buildup_s=20.0, loop_start_s=20.0, loop_seconds=26.65 |
| `music.launch_loop` | 26.65 | 533 | 2 | -24.5 | -10.9 | loop |  |
| `music.resolve` | 12.00 | 240 | 2 | -26.0 | -13.5 |  |  |
| `music.road` | 68.55 | 1371 | 2 | -25.0 | -10.7 | loop |  |
| `music.victory` | 40.00 | 800 | 2 | -27.0 | -15.7 |  |  |
| `sfx.air_open` | 3.00 | 60 | 2 | -24.1 | -10.7 |  |  |
| `sfx.alarm_cut` | 2.40 | 48 | 1 | -17.7 | -8.0 |  |  |
| `sfx.alarm_loop` | 3.20 | 64 | 1 | -20.0 | -10.0 | loop |  |
| `sfx.barrier` | 3.60 | 72 | 1 | -23.4 | -8.0 |  |  |
| `sfx.beam_charge` | 2.00 | 40 | 2 | -22.1 | -13.3 |  |  |
| `sfx.beam_fire` | 5.00 | 100 | 2 | -14.3 | -1.9 |  |  |
| `sfx.birds_up` | 4.50 | 90 | 1 | -31.3 | -15.8 |  |  |
| `sfx.bolt_1` | 3.60 | 72 | 1 | -24.7 | -2.0 |  |  |
| `sfx.bolt_2` | 3.60 | 72 | 1 | -26.2 | -2.0 |  |  |
| `sfx.bolt_3` | 3.60 | 72 | 1 | -23.7 | -2.2 |  |  |
| `sfx.booth_light` | 1.40 | 28 | 1 | -28.7 | -14.5 |  |  |
| `sfx.breaker` | 1.20 | 24 | 1 | -20.6 | -1.4 |  |  |
| `sfx.breaker_1` | 1.20 | 24 | 1 | -20.4 | -1.2 |  |  |
| `sfx.breaker_2` | 1.20 | 24 | 1 | -20.6 | -1.3 |  |  |
| `sfx.breaker_3` | 1.20 | 24 | 1 | -20.6 | -1.3 |  |  |
| `sfx.breathing` | 8.00 | 160 | 1 | -34.0 | -18.5 | loop |  |
| `sfx.bridge_slide` | 6.50 | 130 | 1 | -31.2 | -10.0 |  |  |
| `sfx.car_alarms_far` | 9.00 | 180 | 1 | -34.0 | -20.1 |  |  |
| `sfx.car_arrive` | 6.50 | 130 | 1 | -26.7 | -10.0 |  |  |
| `sfx.car_door` | 1.20 | 24 | 1 | -32.5 | -12.1 |  |  |
| `sfx.car_drop` | 3.00 | 60 | 1 | -29.3 | -3.9 |  |  |
| `sfx.car_roll` | 5.00 | 100 | 1 | -25.9 | -3.8 |  |  |
| `sfx.car_start` | 3.50 | 70 | 1 | -29.2 | -12.0 |  |  |
| `sfx.card` | 5.00 | 100 | 2 | -19.2 | -3.9 |  |  |
| `sfx.chains` | 5.00 | 100 | 1 | -28.8 | -12.1 |  |  |
| `sfx.contact` | 6.00 | 120 | 2 | -26.0 | -17.0 |  |  |
| `sfx.core_crack` | 3.00 | 60 | 1 | -22.5 | -2.6 |  |  |
| `sfx.crash` | 8.00 | 160 | 1 | -22.3 | -2.9 |  |  |
| `sfx.cross` | 13.00 | 260 | 2 | -26.0 | -15.9 |  |  |
| `sfx.door_boom` | 8.00 | 160 | 2 | -20.5 | -3.0 |  |  |
| `sfx.door_heavy` | 3.20 | 64 | 1 | -28.1 | -5.9 |  |  |
| `sfx.dust_fall` | 5.00 | 100 | 1 | -34.1 | -16.8 |  |  |
| `sfx.ears_ringing` | 8.00 | 160 | 2 | -32.9 | -25.7 |  |  |
| `sfx.elevator_arrive` | 3.00 | 60 | 1 | -23.9 | -11.9 |  |  |
| `sfx.elevator_doors` | 3.00 | 60 | 1 | -29.1 | -12.1 |  |  |
| `sfx.explosion_far` | 9.00 | 180 | 1 | -25.1 | -5.9 |  |  |
| `sfx.explosion_near` | 10.00 | 200 | 1 | -20.6 | -1.4 |  |  |
| `sfx.eyes_on` | 4.80 | 96 | 1 | -28.0 | -14.4 |  |  |
| `sfx.fluid_fill` | 8.00 | 160 | 2 | -28.1 | -15.2 |  |  |
| `sfx.footfall_giant` | 6.00 | 120 | 1 | -22.6 | -3.9 |  |  |
| `sfx.gate_close` | 9.00 | 180 | 1 | -22.4 | -3.0 |  |  |
| `sfx.giant_hit` | 3.00 | 60 | 1 | -22.0 | -2.8 |  |  |
| `sfx.giant_punch` | 3.00 | 60 | 1 | -19.5 | -1.8 |  |  |
| `sfx.gunfire_far` | 6.00 | 120 | 1 | -25.6 | -10.1 |  |  |
| `sfx.gurney` | 6.00 | 120 | 1 | -30.0 | -16.3 | loop |  |
| `sfx.hand_rise` | 9.00 | 180 | 2 | -24.2 | -11.0 |  |  |
| `sfx.hatch_close` | 4.50 | 90 | 1 | -33.9 | -5.9 |  |  |
| `sfx.heartbeat` | 10.00 | 200 | 1 | -26.4 | -8.0 | loop |  |
| `sfx.impact_above` | 7.00 | 140 | 2 | -21.9 | -4.1 |  |  |
| `sfx.impact_above_hard` | 9.00 | 180 | 2 | -19.6 | -1.9 |  |  |
| `sfx.jet_pass` | 7.00 | 140 | 1 | -22.2 | -8.5 |  |  |
| `sfx.jolt` | 3.00 | 60 | 1 | -22.7 | -3.9 |  |  |
| `sfx.klaxon` | 4.00 | 80 | 1 | -22.0 | -8.0 |  |  |
| `sfx.lake_ring` | 7.00 | 140 | 1 | -32.7 | -15.9 |  |  |
| `sfx.launch` | 6.80 | 136 | 2 | -16.0 | -2.4 |  |  |
| `sfx.launch_arrive` | 5.50 | 110 | 1 | -24.5 | -3.1 |  |  |
| `sfx.launch_charge` | 3.00 | 60 | 2 | -24.0 | -12.8 |  |  |
| `sfx.launch_roar` | 6.00 | 120 | 2 | -17.1 | -8.9 | loop |  |
| `sfx.lights_flicker` | 2.00 | 40 | 1 | -32.1 | -16.5 |  |  |
| `sfx.mine` | 9.00 | 180 | 2 | -16.9 | -1.2 |  | blast_s=2.4, silence_start_s=0.4, silence_end_s=2.4 |
| `sfx.pa_chime` | 3.20 | 64 | 1 | -18.0 | -8.8 |  |  |
| `sfx.phone_hangup` | 0.70 | 14 | 1 | -33.3 | -13.0 |  |  |
| `sfx.phone_pickup` | 0.90 | 18 | 1 | -39.7 | -14.1 |  |  |
| `sfx.rig_crash` | 5.00 | 100 | 1 | -22.3 | -1.6 |  |  |
| `sfx.rig_tear` | 4.20 | 84 | 1 | -28.6 | -5.7 |  |  |
| `sfx.siren` | 20.00 | 400 | 1 | -25.9 | -12.9 | loop |  |
| `sfx.speak_chime` | 1.40 | 28 | 1 | -27.5 | -15.8 |  |  |
| `sfx.sync_rise` | 9.50 | 190 | 2 | -26.0 | -14.4 |  |  |
| `sfx.train_start` | 6.50 | 130 | 1 | -23.9 | -7.9 |  |  |
| `sfx.train_stop` | 6.50 | 130 | 1 | -22.9 | -8.3 |  |  |
