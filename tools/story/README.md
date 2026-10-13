# tools/story: the story sequencer

Generates the datapack functions that run the story: every recorded line (`angel:say/<id>`), a tick-driven scene engine on the
scoreboard objective `angel.story`, the speak prompt, vehicles that drive smoothly with the player seated in them, and the scenes
(`scenes/sNN.py`; 1 to 5 here: the city, the road, the descent, the corridors and the lift, the cage). It writes only into
`datapack/angel/data/angel/function/story/` and `.../say/`, and lists what it wrote in `build_manifest.json`, so a later build deletes only
its own stale files.

```
$py = "D:\voice-assistant\.venv\Scripts\python.exe"
& $py tools\story\build_story.py            # write the datapack functions
& $py tools\story\build_story.py --check    # offline simulator and checker, writes nothing
& $py tools\story\build_story.py --dry      # test variant: a mannequin tagged angel.testplayer stands in for the player (use --out DIR)
& $py tools\story\build_story.py --scenes 1,2,3,4,5   # only these scenes (a scene module that is being written does not stop the others)
```

`/reload` (or restart) after a build. `data/minecraft/tags/function/load.json` and `tick.json` already call `angel:story/load` and
`angel:story/tick`.

## Playing and testing

| Command | What it does |
|---|---|
| `function angel:story/start` | fresh run from scene 1 (clears everything, sets adventure mode, gives the letter and photograph at the scene start; with the opening tutorial) |
| `function angel:story/start_no_tutorial` | the same without the 20-second tutorial (replays) |
| `function angel:story/controls_vr` / `_flat` / `_both` | which controls the directions name (default both) |
| `function angel:story/stuck {hint_s:60,skip_s:150}` / `stuck_off` | the safety net's thresholds (see Directions) |
| `function angel:story/scene {n:3}` | jump to the start of scene N with its state rebuilt: cast, car, positions, beat, presence flags (through a fade) |
| `function angel:story/stop` | stop; removes every entity the story made, the cast, the monster, timers and forceloads |
| `function angel:story/skip` | resume any wait (the bridge is not needed) |
| `function angel:story/next` | skip whatever step is current (cuts a line, ends a wait, jumps a sleep) |
| `function angel:story/timeout {s:45}` | every wait goes on by itself after 45 s (`function angel:story/timeout_off`; default off) |
| `function angel:story/subtitles_on` / `_off` | show every recorded line as chat text too (lines with no recording are always shown) |
| `function angel:story/status` | one line in chat: scene, step, beat, wait, talking, route frame |
| `function angel:say/1_04` | play any single line (cued to the bridge when one is connected) |
| `function angel:say/file/1_04` | play the pre-rendered file of a line, whatever the bridge is doing |
| `function angel:story/bridge_off` / `bridge_on` / `bridge_status` | never / again let a connected bridge perform the lines; show the handshake scores |

The story waits while nobody is online. A line whose recording does not exist yet (7.17 and 7.18 at the time of writing) runs silently
with its text in chat. Everything the story summons carries the tag `angel.story`; `halt` (called by every scene start, `stop`, and
`start`) kills it, so a `/reload` or restart mid-scene leaves no ghosts (`load` sweeps the tag when no story is running, and a running
story simply carries on because all of its state is in the scoreboard).

## Pacing: `pace.py` (two presets, one table)

Every number that decides how long the film takes is in `pace.py` and nowhere else: the engine (`core.CFG`), `lead.py`, `objective.py`, the routes and the scenes read the
current preset (`pace.PACE.gap`, `PACE.s4_ride_black` ...).  Two presets: **`video`** (the default: a whole playthrough in about 14 to 16 minutes nominal) and **`full`**
(the original values; `--pace full` reproduces the earlier durations exactly: 139 / 132 / 151 / 292 / 371 / 121 / 468 s).

```
python build_story.py --pace video|full [--check] [--out DIR]     # the preset of a build (and of --check)
python build_story.py --table                                      # --check three times: the recorded estimator, full, video; every scene's nominal duration side by side
python build_story.py --check --est-overlap on|off                 # how a line said WHILE a character walks is counted (video: as part of the walk)
```

What the video preset cuts is AIR, never words: every scripted line is still said, in order, once.  The levers: the gap after a line (0.4 s to 0.1 s; none before the speak prompt), the
objectives' grace (2 s to 1 s) and repeat, the safety net (hint 30 s, skip 75 s), an ordinary answer wait goes on by itself after 20 s (`answer_timeout`: the countdown stands
still while the bridge speaks, so a reply is never cut) with the gentle nudge at 8 s and 16 s, the opening tutorial in two lines under 12 s (each ends the moment he does the thing), leaders
walk at 4 blocks a second (0.20 a tick, brisk but slower than a walking player), lines are said while a character walks (4.01, 4.02, 4.05, 4.13 to 4.17, 4.12 under the walk into the
lift), the panel and the page under 4.04, a fade from the top of the escalator to the lobby, the lift ride 4 s of black, the car rolls onto the wagon at 5 blocks a second, the
wagon's creep starts 22 blocks down the tunnel and after 3.10 a fade skips the quiet stretch to the last 8 s of the ride, the aircraft come down at 11 s instead of 15, the mine's
black is 0.7 s (its two seconds of digital silence are untouched), scene 5's lights come on in 3 s (the beat of nothing before them is 2.5 s, the hold on the father after the yes still
2 s), the fluid rises in 5 s, the pad's pause is 1.2 s, the dawn is 11 s (the sky clock is set to the deep twilight in the black), the cards are held a little less.
Rides keep their comfort limits: yaw rate under 45 deg/s (`pace.limit_yaw`; "full" 60), jerk 40.

What it cannot cut: the recorded lines and the waits for his answers.  `--check` prints, per scene, how much of the nominal duration is speech and answers (answers assumed 6 s) and how
much is air; with every line at its recorded length that floor is about 10.5 minutes, the fight and the ending (about 160 s) come on top.

Live voices: nothing in the tightened timing assumes a line's exact length.  The gaps are sleeps after a line's reported end; what a scene schedules against a line's length is
limited to the verbatim lines (`sim.check_timing_bound`); `characters_bridge/config.py` `adapt_bounds()` keeps an adapted line no longer than the script line in the video preset.

## The companion guarantee (`lead.py`)

`lead(..., companion=("misato", back, side))` sends a second character along with the leader (scene 4's crossing: Ritsuko leads, Misato trails the player; scene 5's
walk through the cage door).  **What went wrong:** her place at each stop was a point 2 blocks to the side of the leader's line and 3 behind, and she was sent there in a straight
line from her last place.  The catwalk over the lake is 3 blocks wide (z 159..161 from x 3022 to 3096): the point was in the railing and the line from the wide dock to it crossed the
railing at the neck of the catwalk, at about (3023.1, 54, 158.6).  She walked into it (arrival score 0), the leader's monitor then paused her because the player was more than
9 blocks from her (`cast/stop`), and nothing ever resumed her: she stayed there until she was teleported by hand.  **Now:**

* her path is planned on the built set (`lead.Nav`: a cell is standable with floor under it and under a 0.4-radius body and two blocks of headroom all round; an A* over half-block
  cells, string-pulled into straight walkable segments).  Her place is the standable cell nearest to the wish (beside the leader, else nearer her line, else farther back in single
  file, +2.5 blocks so she walks behind the player, not on him) that she can walk to from where she stood.  A door the story has opened counts as air (`nav_open=`).
* she follows the path as a queue (storage `angel:story cq.<who>`, one waypoint after another, walked by `story/lead/cq_<who>` while `#f.cq_<who>` is 1), and she never pauses to
  wait for the player (only a leader does).
* the keeper (every second, `story/lead/ck_<who>`): not moved for 3 s, her walk unfinished, farther than 6 blocks from the player: she is put (no sound, no particle) on the nearest of
  the reachable cells of her path (markers `angel.cp_<who>`, every 2 blocks) that lies 3.5 to 6.5 blocks from him and out of his view (not within 9 of the point 8 blocks straight ahead of
  him; failing that, any such cell 3.5 to 10 blocks away), and walks on from the next waypoint of her path.  At the end of a lead she must have reached her place within 10 s or is put near him the same way.
* `--check` (`sim.check_companions`) proves every leg again at 0.2-block steps, her place standable and 1.8 to 8 blocks from the leader, every rescue cell standable, the keeper
  functions present.  `livetest_companion.py` runs the real compiled crossing of scene 4 on a scratch server (25605 / 25615) with a stand-in boy walking the route at 4.2 blocks a
  second and reads her position every second; `--jam` holds her in place from 8 s to prove the keeper.

## The contract with the character bridge

Fake players on `angel.story`, exactly as `characters_bridge/rcon_commands.py` expects:

| name | meaning |
|---|---|
| `#beat` | story beat (characters/beats.md); set by the scenes |
| `#wait` | 0 nothing, 1 the story holds for any spoken answer, 2 it holds until the boy agrees |
| `#speaker` | who is being answered: 1 Misato, 2 Ritsuko, 3 Gendo, 4 Rei (the character of the last line, or what the wait says) |
| `#talking` | 1 for exactly the duration of a recorded line, then 0 |
| `#present_misato/_ritsuko/_gendo/_rei` | 0 absent, 1 in person, 2 voice only (phone, radio) |
| `#lastspoke` | id of the character whose recorded line played last (BASE leaves it alone) |
| `#bridge_speaking` | written by the bridge; while it is non-zero the speak prompt is hidden |

`angel:story/answered` clears `#wait` 1; `angel:story/consented` clears any wait and sets `#consent` 1.

### The voice bridge performs the lines (`lines.py`, `system.py` `t_line`)

The four characters' lines (MISATO, RITSUKO, GENDO, REI) are TTS now (`tools/voices/tts_lines.py`), pre-rendered into the pack as before, **and**
performed live by the bridge when it is connected.  A `say` step runs `angel:say/<key>`; what that does depends on one score, `#bridge_hb`:

| score (all `angel.story`) | who writes it | meaning |
|---|---|---|
| `#bridge_hb` | the bridge: `set 20` every 0.25 s; the game counts it down each tick (`t_line`) | above 0 = a bridge is connected (it spoke in the last second) |
| `#live_ok` | `story/bridge_on` / `story/bridge_off` (default 1) | 0 = the pre-rendered files always play |
| `#cue` | the game, in `say/cue` | `cue number * 1000 + #line` (`#line` = scene * 100 + number): ONE number the bridge reads per poll |
| `#cue_n`, `#cue_t` | the game | the cue counter, and the game tick of the cue |
| `#cue_ack`, `#ack_t` | `function angel:say/claim {n:..,ticks:..}` | the cue the bridge has taken, the tick it took it |
| `#live` | the game | 1 from a cue until it is claimed or taken over; 0 for a file |
| `#cue_fb` | the game | 1 when the game took the cue over and played the file itself |
| `#line_left` | the game's `say/<key>`, then the bridge's claim | ticks until `#talking` is released |

* **Bridge connected** (`#bridge_hb` above 0, `#live_ok` 1): `say/<key>` sets `#cue`, `#talking 1`, `#lastspoke`, `#speaker` and `#line_left` = the
  file's length + 3 s (**the watchdog**), and plays nothing.  The bridge claims the cue within a few tens of milliseconds and writes the REAL length of
  what it will say into `#line_left`.  **The engine counts the line down and releases `#talking` itself**, so a bridge that dies mid-line cannot hold
  the story: the clock ends the line when the reported length is up.  A cue that is not claimed within 14 ticks (0.7 s), or whose heartbeat has
  stopped, is **taken over by the game**: `say/fallback` plays the pre-rendered file at once (`say/fb/root` dispatches on `#line` to `say/file/<key>`) and
  the bridge, finding its claim refused, stays silent.
* **No bridge:** `say/<key>` runs `say/file/<key>` -- the sound positioned at the speaker, `#talking` for the file's length -- exactly as it always
  did.  `build_story.py` also writes `say/file/<key>` for every line, and the fight's bark wrapper (`fight/say/7_NN`) calls THAT: barks are pre-rendered,
  instant, played by the game, never cued.  BASE lines are never cued.
* The story's timing needs no change for a live line: a `say` step waits for `#talking 0`, the nudge clock counts silent ticks, the gap after a line
  is a sleep.  What a scene schedules *against a line's length at build time* (`ctx.lines[..].ticks`) is another matter: those lines must be played at
  their pre-rendered length, so they are **VERBATIM** in `characters_bridge/line_policy.py` and the bridge plays the pre-rendered take of them
  (the checker finds such lines by watching which `Line.seconds` the scenes read while they build: `sim.check_timing_bound`).
* Controls: `function angel:story/bridge_off` / `bridge_on` / `bridge_status`.  `--check` drives the handshake tick by tick on the generated
  functions (`sim.check_handshake`: no bridge, a claim, no claim, a bridge dead before / after its claim, the switch, barks and BASE, the takeover
  table for all 111 lines).
* `build_story.py --steps FILE [--steps-only]` writes every scene's steps as JSON (kind, line, wait speaker / mode / nudges, branch targets and
  conditions, hand-over targets, `_meta.setup_end`); the bridge reads it to look ahead.

## The speak prompt

Whenever `#wait` is 1 or 2, no recorded line is playing and the bridge is not speaking, a small two-line panel appears (two billboarded,
full-brightness `text_display`s, tags `angel.prompt` + `angel.prompt_main` / `angel.prompt_sub`): a gold speech-bubble glyph and **Your turn** in
bold white on the first line (letters about 12 cm tall: readable at 2 to 3 m in a headset), and in smaller grey letters beneath it what to do
("answer Misato"; for the consent wait "will you pilot it?"). A soft amethyst chime plays. The glyph is U+1F4AC, a 16 x 16 glyph of the default
font's Unifont layer (looked up in the 26.3 asset index: `unifont.zip`, 114432 code points); it is written to the function files as the escape
`💬`, because **every generated file is plain ASCII** (`core.ascii_only`: whatever is above U+007F becomes a `\uXXXX` escape, so what the
game shows can never depend on the encoding a file is read in; `--check` fails on a non-ASCII generated file and on mojibake in any story source).
Placement (never over the speaker's face): near the player it hangs between him and her, 0.5 to 0.7 below his line of sight to her eyes (1.0 m from his eyes when she is closer than 2.2 m, else 1.5 m); farther away
(across the room, the commander in the booth) it hangs 2.1 m from his eyes in her direction, 0.8 below that line; for a voice only (telephone) it hangs
2 m ahead of where he looks; in a vehicle it is fixed in the vehicle's frame, ahead of the passenger seat, and travels with it. The same words go on
the action bar **only when no panel could be placed**. `function angel:story/prompt/pulse` swells the panel and plays the chime again (the nudge of a
silent player, below). It disappears the moment the wait ends or the bridge starts to voice a reply.

## Writing a scene

A scene is one module `tools/story/scenes/sNN.py`; the builder finds it by name. It defines:

```python
N = 7
TITLE = "The fight"
def build(s, ctx): ...
```

`s` records steps (all methods return `s`), `ctx` gives anchors, rigs, routes, probes of the built voxel worlds:

| call | meaning |
|---|---|
| `s.do(*commands)` | run commands (flat lists are fine) and go on at once |
| `s.beat(n)`, `s.present(misato=1, ritsuko=2, ...)`, `s.flag(name)` | state; flags are `#f.<name>` and are cleared by `halt` |
| `s.say("4.01", gap=None)` | play the line; go on when it has finished plus the gap (0.4 s; `gap=0` for none) |
| `s.sleep(sec)` | wait |
| `s.wait_answer(speaker="misato", prompt="answer Misato", timeout=None)` | `#wait` 1 |
| `s.wait_consent(speaker="rei", prompt="will you pilot it?")` | `#wait` 2 |
| `s.until(cond, timeout=, on_timeout=[], hint=("text", [cmds]), hint_after=40, nag=(first_s, repeat_s, [cmds]), on_done=[], tick=[])` | wait for a condition; a list of conditions means "any of them". Nothing may soft-lock: give a `timeout` unless the condition is certain to come (a route frame, a flag a timer sets) |
| `s.after(sec, *commands)` | run commands `sec` seconds from now WITHOUT waiting (a timed effect beside the story; scheduled functions are cleared by `halt`) |
| `s.fade(cmds, black=1.5)` | blindness (dark at once, back over the last second); `cmds` run in the dark. Takes `black + 1` seconds. Nothing rotates the head |
| `s.label("x")`, `s.goto("x")`, `s.branch(cond, "x")` | jumps (e.g. on `#consent`) |
| `s.setup_done()` | marks the end of the steps that rebuild the starting state (see below) |
| `s.next_scene(n, jump=False)` | hand over to scene n: `jump=False` carries the state on (`angel:story/sN/cont`, no rebuild, no flicker); `jump=True` is `angel:story/scene {n:N}` (rebuild with a fade; use when the next scene is elsewhere) |
| `s.move_player(x, y, z, yaw=None, pitch=None, r=4, settle=0.8, before=())` | **the guarded move**, for any teleport that crosses sets (2000+ blocks, unloaded chunks, perhaps still on a seat): dismount (`ride dismount`, `#ride 0`), forceload the destination, `before`, wait `settle` s, dismount again and `tp` (turning the head only if `yaw` is given), then WAIT until he is within `r` blocks, re-issuing the dismount and the teleport every second (12 s limit: one more teleport, then on). Every scene's first teleport and every cross-set move goes through it (`sim.check_relocations`) |
| `s.hush(what)` / `s.unhush()` | a span in which nothing may START to sound but the recorded voices (the checker follows every step in it; lead.py's footsteps are muted by `#hush`) |
| `s.function(name, lines)` | a reusable function of the scene; returns the call |

Conditions (`engine.C`): `C.near(x, y, z, r)`, `C.score("#name", "1..")`, `C.flag("name")`, `C.entity(selector)`,
`C.data(selector, "interaction")`, `C.not_talking()`, `C.raw("if ...")`; combine with `&`. A route condition comes from
`route.cond_at("station_or_mark_or_frame")` / `route.cond_done()`. `est=` on a condition is how long the offline simulator assumes it takes.

Useful helpers: `context.cast_summon/cast_remove/cast_look/cast_mount/cast_pose`, `tp_player` (never turns the head), `ride_passenger()`,
`play_at`, `title`, `actionbar`; `core.P()` is the player selector, `core.blind(seconds)`.

### Beginning a scene

The first steps rebuild the state the scene expects (a jump runs them; a hand-over from the previous scene skips them with
`setup_done()`): fade, put the player and the cast where they belong, set `#beat` and the `#present_*` flags. Always teleport the player with
`tp_player` (no rotation) and `forceload` (`ctx.preload(x, z)`) the destination before spawning anything there; wait about a second.

### Vehicles

```python
car = ctx.rig("car")                                 # models.py: display-entity rigs; `cartrain_rig(...)` is a wagon with the car on it
ctx.rig_spawn(car, "closed", (x, y, z, yaw, pitch))  # -> commands that put it there; the variant name is yours ("dooropen", "side" ...)
route = ctx.new_route("name", car)                   # motion.py / paths.py build the frames
route.add_leg("drive", Path(points), vmax=8.0, a_acc=1.2, a_dec=1.8, a_lat=2.4, station="stop1", marks={"bend": 42.0})
s.do(*route.start_cmds(limit="stop1"))               # the counter may advance up to the frame of that station
s.do(*route.limit_cmds("end"))                       # ... later let it go on
s.until(route.cond_at("bend"))                       # wait for a mark; route.cond_done() for the end
```

A rig is a set of display entities all at one position (the rig's), each holding its place in the model through its `transformation`, so one
`tp` with the route's yaw and pitch moves the lot; seats are `item_display` entities tagged `angel.seat_driver` / `angel.seat_passenger`
(the rider's feet end up 0.6 below the seat entity: measured). The player is `ride`n onto the seat once and never teleported while it moves.
The route table is played from `#mv.n` (one frame per tick); legs start and end at rest, so holding at a station is natural.

**The car** (`models.py`) is an open-top blue roadster, right-hand drive, 60 display parts: 3.0 wide over the body (3.6 over the wheels), 6.65 long,
door tops at 0.75, a raked windscreen (glass and two posts, no top rail) that ends at 1.11, a bonnet falling 11 degrees to the nose, two seats with
headrests and humps, wing mirrors, head and tail lights, and a dash, column and steering wheel in front of the DRIVER only.  Model space is +x LEFT:
the boy (passenger, the player) sits on the LEFT at (0.72, 0.17, -0.12) (feet), Misato on the RIGHT at (-0.72, 0.17, 0.12): 1.44 apart across the
car, 1.46 centre to centre, her seat a quarter of a block ahead of his; the seat entity is 0.6 above the feet.  The passenger door is the left one
(`carfx.door_world`): on the street the car stops with its left flank to the boy.  A rider's eye is 1.5 to 1.8 above his feet (1.62 flat-screen):
at every such height nothing of the car is above the horizon in the forward 160 degrees or overhead, and about 80 % of a 100-degree forward frame is
clear (the scuttle takes the lower tenth, the bonnet the next); `ride_view.py` ray-casts it (below).  Lying on its side it rests on its right wheels
(`ROLL_PIVOT`), open top to the right.  `cartrain_rig(..., reversed_car=True, low_side="R")` turns the car end for end on the wagon (seats and their
yaw with it) and takes the railing and posts off the wagon's right side (a 0.22-high kerb stays): the Geofront's cavern is on the right of the
direction of travel, so the passenger's window faces it.  Misato's head: `carfx.look_boy()` (the cast turns her to the boy, 12 degrees a tick),
`carfx.look_road(rig)` (the rig holds her facing the way the car goes), `carfx.say_glancing(s, rig, "2.01", glance=3.6)` (she looks at him as the line
begins and at the road again `glance` seconds in).  Every rig part is tagged `angel.rpart`, never `angel.part` (that is the Angel's: `angel:angel/sync` teleports every block display carrying it to the monster each tick, which is why the aircraft of the first playthrough were never seen).  `Rig(driver_face=0.0)` hides the "driver" seat key from system.py's own facing line (it only zeroes
the pitch), and puts the facing in the rig's follow function, switched off while `#look_misato` is 1.

`ride_view.py` is the first-person ray-caster used to design the car and the wagon's open side: `python ride_view.py car` renders forward / left /
right / up / back / down and the conversation view from the passenger's eye over the car's boxes and a box model of Misato, and prints the obstruction
numbers (opaque parts, glass counted apart, highest part in the forward 160 degrees, Misato's azimuths) for eyes 1.5 / 1.62 / 1.8 above the feet and
a seated-low 1.15; `python ride_view.py wagon` casts rays through the built Geofront from the passenger's eye at `geofront.wall_opens`, `geofront.reveal`
and 2 s after, for the pyramid, the lake and the hanging towers, and renders looking out of the window; `ride_view_old.py` keeps the first (closed)
coupe for the before / after numbers.  `ride_air.py` is scene 1's air attack (five VTOLs 13 blocks long circling the walking Angel at different heights,
tracers flying to it and bursting in flashes, one hit and falling burning to `outskirts.crash`, the wreck, the birds on the wires).  A route that rides
above the ground on purpose declares `route.deck_lift = [..]` (planned height per frame) and the checker subtracts it.

### A worked example

```python
# scenes/s05.py
from context import cast_summon, tp_player
from core import blind, sset
from engine import C
import worldgen_sky

N = 5
TITLE = "The cage"

def build(s, ctx):
    a = ctx.anchor("hq.cage_door")
    s.do(blind(3))                                   # setup: fade, place, state
    s.sleep(0.4)
    s.do(*ctx.preload(a["x"], a["z"]), tp_player(a["x"], a["y"], a["z"]), *worldgen_sky.sky("hq"))
    s.sleep(1.0)
    s.do(cast_summon("ritsuko", a["x"] + 2, a["y"], a["z"], 180.0), sset("#beat", 50), sset("#present_ritsuko", 1))
    s.sleep(1.0)
    s.setup_done()                                   # a hand-over from scene 4 starts here

    s.say("5.01")
    s.until(C.near(a["x"], a["y"], a["z"] - 20, 3.0), timeout=60, hint=("Walk on, across the bridge.", []))
    s.say("5.02"); s.say("5.03")
    s.wait_answer(speaker="ritsuko")                 # Your turn - answer Ritsuko
    s.say("5.04")
    s.wait_consent(speaker="rei", prompt="will you pilot it?")
    s.branch(C.score("#consent", "1"), "agreed")     # jump when he said yes
    s.say("5.39"); s.goto("end")
    s.label("agreed"); s.say("5.42")
    s.label("end")
    s.next_scene(6, jump=True)
```

Run `build_story.py --check`: it prints the scene's timeline, verifies that its lines are said once in script order (for the scene
numbers that have lines), that waits can be reached, that every anchor and called function exists, and replays every route frame against the
built voxel worlds.

## Testing without a player

`build_story.py --dry --out DIR` writes a variant in which a mannequin tagged `angel.testplayer` is "the player" (every `@a[limit=1]`
becomes that mannequin; `title`, `playsound`, `effect` and `give` still address `@a` and so do nothing). Copy the result over the
datapack of a scratch server, `forceload` the sets, summon the mannequin, `function angel:story/start`, and drive the waits with
`angel:story/answered` / `consented`, interaction data (`data merge entity <interaction> {interaction:{player:[I;1,2,3,4],timestamp:100L}}`)
and `tp`. `--extra DIR` adds scene modules from another folder (to try a scene without putting it in the repo). Never put the dry variant in
`datapack/`.

## What the checker verifies

* each scene's duration with answers assumed to take 6 s, with every line and wait placed in time;
* every script line of each scene said exactly once, in order (conditional lines said only by a nag are listed apart);
* no deadlock: a wait on a route frame beyond the current limit is an error; open-ended waits without a timeout are listed;
* all anchors exist; all called functions exist (cast / monster / world functions are the known external ones);
* every frame of every route sits on a surface with room above it in the built sets, with accelerations, jerk and turn rates reported.
* **presence** (`sim.check_presence`, fed by `ctx.presence`; scene 2's Misato): at every place she is put she stands on solid ground with room for a body, within
  3 blocks of the player when the picture comes back (6 later), inside his forward 120 degrees but 25 degrees or more off the line he looks along, clear of the
  car's hull and turned to him; and in the commands from the blast's `after` to the drive-off every `cast/remove` of her is followed in the same tick by a
  `cast/summon` (no gap, never two), nothing makes her invisible, and the cast's own `cast/mount` (invisible for 12 ticks) is not used on her.
* **leftovers** (`sim.check_leftovers`, fed by `ctx.removals`): what a scene spawns and says must go (scene 2's mushroom cloud: gone within 25 s of the blast) has
  a timed kill beside its spawn and another when the scene ends; the aircraft that break away on the ridge (`ride_air.leave_setup`: peel off 4 ticks apart, turn
  away at 6 degrees a tick, nose up, accelerate to 8.5 blocks a tick) are 200 blocks out and removed before 2.05 has ended.

## Scenes 4 and 5: what was added to the engine

All additive; scenes 1 to 3 are untouched.

**Waits.** `s.wait_consent(..., answer_ends=True)` is a consent-capable wait (`#wait` 2: the bridge classifies the player's answer, a yes
runs `angel:story/consented`) that ALSO ends, without consent (`#consent` stays 0), as soon as the bridge has voiced a reply to something
that was not a yes. It uses only what the bridge already writes: `#bridge_speaking` going from 0 to a character id and back to 0 (the
bridge's `_pilot` speaks the addressed character's reply on a non-yes and leaves `#wait` alone). Give it a `timeout`: if the answer is not
addressed to anyone the bridge says nothing, and the wait would hold. `s.wait_consent/wait_answer(..., nudges=Nudges(first, repeat, cmds,
loop_from=1, lines=[...]))` runs reminders while it waits: the first after `first` seconds of SILENCE, then one every `repeat` seconds of silence,
in the order `cmds[0], cmds[1], ..., cmds[n-1], cmds[loop_from], ...` (scene 5: 5.39, 5.40, 5.41, 5.40, 5.41 ...). Silence is the clock: the nudge
counter `#nagt` only counts ticks in which no recorded line plays and the bridge is not speaking, so **the gap between the END of one nudge line and the
START of the next is exactly `repeat`**. (What was wrong before: when the counter reached `first` the body started a line, and the gate that followed
it in the same function saw `#talking` already 1 and "tried again in a second", over and over: each nudge came one second after the previous line ended.
The same ordering bug was in the `until` nags; both are fixed, and `sim.check_nudge_cadence` runs every compiled nudge series through 3 minutes of
silence on the generated functions and fails the build on any other gap.) A wait with **no** `nudges` gets the engine's gentle default
(`Nudges.gentle_for`): after 12 s of silence the asking character turns to look at the player (when she is there in person) and the prompt pulses with
its chime again, repeated every 15 s; no spoken lines. `lines` is what the checker records as said on a path where the player agrees after the first
pass. `s.branch(...)` plus
`s.sim_path("early_yes", take=["label"], skip=("5.25", "5.41"))` makes the checker walk a second route and verify its lines.

**Sound** (`audio.py`): `s.bed("hq")` / `s.bed(None)` an ambience bed that restarts itself every N seconds (the length of its .ogg, read
from sounds.json; 60 s while the file does not exist: REBUILD when the sounds arrive), `s.music("father")` / `s.music(None)` a music cue
(`decision`, `dread`, `road`, `fight`, `fight_final` loop; `MUSIC_LOOP` in audio.py), `s.loop("klaxon")` an alarm layer (its own length, or
`LOOP_PERIOD`), `s.sfx("sfx.door_boom", at=(x, y, z), vol=, pitch=, minvol=)` a one-shot effect (`at=None`: at the player). Starting a bed or a
cue stops the one of its kind in play; `stopsound` is sent for each event, the timers are cleared, and `angel:story/halt` does it all. A sound
event that does not exist yet is silent. Added with scenes 1 to 3 (all additive; what scenes 4 to 7 use is generated as before):

| call | meaning |
|---|---|
| `s.bed("cicadas+town_empty")` | two beds layered as one: they start and stop together |
| `s.bed("tunnel", fade=3.0)` | the bed comes in over 3 s. Minecraft cannot change the volume of a sound that is playing, so a fade is a staircase of restarts, a notch louder every 0.8 s, the last step being the ordinary loop. Beds only, never music |
| `s.bed("geofront", fade=2.5, out="tunnel", out_fade=1.2)` | crossfade: the bed in play (`out`) is ramped down while the new one comes in |
| `s.bed_out("car_interior", 1.5)` | ramp the bed in play down to nothing |
| `s.loop("siren", at=(x, y, z), vol=1.8)` | the layer from a place in the world (it fades with distance as the car drives away); `name=` gives a second cue of the same sound a name of its own |
| `s.silence()` | every bed, cue and layer stopped and their timers cleared, then `stopsound @a` for whatever else is sounding |
| `s.quiet(0.4, 2.4)` | declares a window (seconds from here) in which NOTHING may sound; `sim.check_quiet` follows every command and scheduled function that can run in it and fails the build on a `playsound` (scene 2's mine) |

`--check` also verifies that every `angel:` sound event the story plays or stops is in the pack's sounds.json, that the card font exists and covers
the cards' characters, and that music.descent's bloom lands on geofront.reveal (scene 3: see its docstring).

**Cards** (`cards.py`, typeface `cardfont.py`): `s.card("EVANGELION  UNIT 01")`, `s.card("TO BE CONTINUED", small="an unofficial fan work", hold=3.5)`,
`s.card("ANGEL ATTACK", hold=2.0, back=2, back_wait=0.2, under=[(0.05, [cmds])])`: `under` runs commands beside the card (that many seconds after
its hit), `back` is the seconds of blindness that bring the world back (3 = a slow fade, 1 or 2 = a quick return to the same view). The text is
set in the resource pack's font `angel:card`, a bitmap font that `cardfont.py` builds from KaTeX_Main-Bold / -Regular (Computer Modern Roman, SIL
Open Font License 1.1; the TTFs and the licence notice are in `fonts/`): bold, condensed (84 %), widely spaced capitals and a lighter lower case for
the small line, drawn into `assets/angel/textures/font/card.png` (16 x 5 cells of 144 px) with `assets/angel/font/card.json` (`height` 18,
`ascent` 15, the `chars` rows, a `space` provider). `python cardfont.py --preview card.png` draws the cards the way the game lays glyphs out; a
plain `build_story.py` writes the font beside the datapack. See `cards.py` for why a card is built in the world (a black room of six slabs round
the player and four billboarded text displays, nothing following the head) and not with `title` (Vivecraft draws titles on the HUD quad, whose
place and visibility are the player's own setting).

**Leading** (`lead.py`): `lead(s, ctx, "misato", [Stop(x, y, z, say_at=["4.01"]), (x, y, z), ...], speed=0.15, companion=("misato", back, side))`
makes a character walk a route and never leave the player behind (waits at each stop for him within 6 blocks, stops and turns back to look
for him if he is more than 9 away while she walks, footsteps, a time limit that brings him). `face(ctx, who, x, y, z)` turns a character
smoothly (at most 14 degrees a tick) to a point; `face_player(who)` is the cast's own player-tracking look.

**Blocks** (`hq_cage.py`): `cage(ctx)` generates, from the set module, the functions `angel:story/hq/...` that switch the cage lights in
8 banks (`bank_on_<k>`, `bank_off_<k>`, `lights_on/off`), the booth (`booth_on/off`), the hospital vestibule lamp (`vest_on/off`), the
eyes (`eyes_on/off`), the cage door (`door_open/close`, staged), the hospital side door (`side_open`), the lift door (`lift_opened/closed`),
the lobby strips (`strips_red/on`), the giant's hand cell by cell (`hand_up/down`; what stands behind it comes from a second build of the
set without the hand), the pipe rack that falls (`rack_tear`, `rig_fall`), dust, rings, impacts. `cage(ctx).flicker(name, banks, pattern)`
builds a flicker. `angel:story/hq/reset_all` puts the whole set back as built; `angel:story/stop`, `story/start` and `story/load` call it
when the story has been in the set (`#hq.dirty`). A scene that wants the cage lit after scene 5 must switch the lights on itself
(`angel:story/hq/lights_on`, `booth_on`).

## Staging added after the second playthrough (scenes 1, 2, 5, 6, 7)

* **Scene 5, the second impact** (`s05.py`, `hq_cage.py`): impact 0 -> every light out -> 20 stutter back -> 36 the rig tears loose over the player
  (`rig2_place` puts a marker 2.5 blocks ahead of him, clamped over the raised hand, or over the hand when he is more than 11 blocks from the shield;
  `rig2_start`: rig-tear sound from there, sparks, dust and fragments past his face, a swinging shadow on the deck, a sway for 44 ticks) -> 64 the hand
  surges up in 8 steps (`hand_surge`) -> 80 the rig falls on the palm (landing 111, debris to the far side) -> 118 the eyes -> 121 everyone looks up
  at the face -> 130 5.32 -> 150 the aftershock and Rei is thrown.  Gendo: the cage dips, one hard light snaps on him, both women look up, 2 s, then 5.04.
  The gurney is timed to arrive as 5.30 ends.  `booth_anchor(ctx)` reads the commander's stand from the set module, not from anchors.json.
* **Scene 6**: the plug is turned to the front on entry (through the black); `launch_plug.py` builds the capsule interior and the status strip / HUD
  (rewritten as the BASE lines are said; the sync rate counts to 41.3 with the rising tone); `launch_pad.py` the pad: dark shaft, ring lights from
  below, beacons, four restraint arms, all-green wave, the charge chase.  The real capsule lamps and the shaft rings are restored by
  `story/launch/restore`.
* **Scene 2**: the white holds to the blast, then a real black room (six opaque slabs) that moves with him; he is put beside the car turned to it, and
  Misato stands 2 to 3 blocks from him in his forward cone, turned to him (she used to be 2.4 blocks behind his shoulder: nobody found her); she walks to the
  car's open top for the push and round to the driver's side to get in (a plain `ride`, no teleport, no 12-tick invisibility).  The aircraft peel off and
  leave over the horizon during 2.05 (`ride_air.leave_setup`; the first version slid them 90 blocks once and left them hanging, with their tracers, in the sky);
  the mushroom cloud thins, greys, rises and is removed in stages (`cloud_dissipation`), gone 24 s after the blast; the town's wreck burns on until the gate.
* **Scene 1**: the girl is 12 blocks ahead of him; a street-wide jolt (`jolt_street`); bigger tracers; the wreck column.  **Scene 7**: the ending is a
  curtain call (`launch_cage.ending_spots`).

## Directions: the objective system (`objective.py`)

Every place where the story waits for the PLAYER to do something (walk somewhere, touch something, look somewhere) has an **objective**: in-world
directions that cannot be missed in a headset.  The speak prompt covers the waits for speech; this covers everything else.

```python
from objective import objective, Objective, follow_objective, Ahead
s.until(C.near(x, y, z, 2.6), objective=objective("Pick up the phone", at=(x, y, z), line="Walk up to the phone - it picks up by itself", how="walk"), ...)
s.objective_on(objective("Follow Misato", at="@e[type=minecraft:mannequin,tag=angel.misato,limit=1]", far=8, still=10))   # a block of steps ...
s.objective_off()                                                                                                         # ... until here
s.until(..., no_objective="a vision of six seconds at most")      # a player-dependent step that needs none says so; the checker lists them
```

`objective(text, at=None, line=None, how=None, grace=2.0, waypoint=True, lines=True, bearing=True, giant=1, repeat=15, secs=5, sound=True, far=None,
still=None, lift=0, first_how=False)`.  `text` is the waypoint label, `line` the direction-line sentence (str or `(both, vr, flat)`), `how` the controls line
(a key of `objective.HOW` or text; shown on the repeat, always with `first_how`), `at` a point, an entity selector (the waypoint follows it) or
`Ahead(dist, side, up)` (a point made relative to the player's view when it begins).  `far` / `still` gate it ("Follow Misato" shows only when he is more
than 8 blocks behind her or has stood still 10 s).  `giant=16` scales the panel for the 16x giant.  Only one objective is current at a time; a new one,
a speak prompt, a title card and the step's exit remove the previous one.

What the player sees, after the grace (2 s; a step he completes at once never flashes it):

* **Waypoint** (entities tagged `angel.story` + `angel.objective`): a label (`text_display`, `angel.ob_label`: the text in pale yellow, a gold triangle under it,
  billboard, `see_through`, 25 % black behind) and a thin beam (`block_display`, `angel.ob_beam`: white stained glass, 70 blocks tall, so it stands over
  the roofs), a marker `angel.ob_target` at the target (it follows an entity every tick), a spark of light at its foot.  Re-scaled every 5 ticks in 17 distance
  bands (1.5 .. 120 blocks): the label stays about one degree of visual angle (scale 0.1 x distance, clamped to 0.5 .. 12), the beam widens with distance
  (0.03 + 0.006 x distance).  Two entities + the marker per waypoint, one more for the line.
* **Direction line** (`angel.ob_line`, one `text_display`): the sentence 2 m ahead of where he looks at that moment, 0.4 below the eyes (lowered to 1.0 if a
  character is within 1.5 blocks of that spot), letters 9 cm tall, line width 170 px, the speak prompt's 40 % black background.  It begins with a gold arrow
  (up ahead, right, left, "behind you:") computed from his yaw and the target's.  It stays 5 s and comes back (with `how` on a second line) when the distance
  has not got smaller for 15 s.  On a flat screen the sentence is on the action bar too (not after `angel:story/controls_vr`).
* **Chime**: `angel:sfx.speak_chime` at pitch 0.62, volume 0.35 (the prompt's is 1.0 / 0.6); 0.22 on a repeat; silent inside a hush.

Controls wording.  The server cannot tell whether a player is in VR: Vivecraft's server mod keeps that in Java (`ServerVivePlayer.isVR/isSeated`, reachable only
through its API) and sets no tag, team, score or attribute, and its server config has no such switch.  So the text names both ("Walk: left thumbstick
(keyboard: W A S D)") and `function angel:story/controls_vr` / `controls_flat` / `controls_both` (score `#ctl` 1 / 2 / 0) narrow it (the launcher
can call one).  Controls named (Oculus Touch defaults, `assets/vivecraft/input/oculus_defaults.json` in the Vivecraft jar): left thumbstick = move
(`vivecraft.key.freeMoveStrafe`), right thumbstick = turn (`rotateAxis`), right trigger = attack / left click (`key.attack`), A (right hand) = use / right click
(`key.use`), left trigger = teleport / walk forward when teleport is off, left stick click = jump, right stick click = sneak.  The reversed file swaps the
hands.  Roomscale: `SwingTracker` hits with the controller without a button unless the player is in creative (Auto weapon collision; the story is adventure).

Wording rule: nothing needs a button.  The phone, the car (getting in, pushing it), the lift, Rei all work by walking up to them; the one button is hitting
the core (swing your hand at it, or the right trigger / left click).

The **opening tutorial** (`objective.tutorial`, scene 1, just after he wakes: the card stays the film's first image): "Look around" (60 degrees of yaw), "Move:
left thumbstick (keyboard: W A S D)" (3 blocks), "When you see Your turn, just speak aloud", "A light like this marks where to go" (a sample waypoint
beside him); each leaves when he does the thing or after 8 s (about 20 s in all).  `function angel:story/start_no_tutorial` starts a replay without it
(`#tut.off` 1; `story/start` sets it back to 0).  Then the note on the photograph's back hangs in front of him for 6 s (`objective.note_panel`).

**Safety net** (`CFG.stuck_hint_s` 60, `CFG.stuck_skip_s` 150; `build_story.py --stuck-hint S --stuck-skip S`; at run time
`function angel:story/stuck {hint_s:60,skip_s:150}` until the next reload, `stuck_off`): a step the player must act in (an `until` on a distance, a touch or a look,
and every speech wait) counts ticks without progress (`#stk`: an objective resets it when he gets closer to the target or, for "Follow", moves; a
speech wait counts only silent ticks).  At the hint threshold a step with no objective gets a generic direction line from its `hint` text; at the skip
threshold the step is let go with a 2 s fade (`sk<i>`: the step's `on_timeout` if it has a timeout, else its `on_done`, so the player is brought to the place
or put in the car; a speech wait simply ends).  Not watched (time-driven, or with their own recovery): route / flag / score waits, `move_player`'s guard,
leaders' `arrived` waits, the fight (scene 7) and the girl's vision; `until(..., no_skip=True)` / `wait_*(..., no_skip=True)` excludes a step.
`--check` prints every objective with its target, the `until` steps marked as needing none, and the watched / unwatched lists; it fails on a player-dependent
`until` with neither an objective nor a `no_objective=` reason.

Scene 7's directions (`s07.py`, from the fight's scoreboard, the fight untouched): "Walk toward the Angel" -> within 24 blocks of the core "Hit the red core"
with a waypoint on it and the controls named (stays until a hit lands: `#ch` below 60; the controls come again after 20 s in range without a hit) -> then
only the waypoint ("Keep hitting the core") until three hits -> the first time `#st` is 1 (the beam is charging) "Get behind a building" -> after each
back-off (`#hold` 1, up to 3 times) "Close the distance again".  Nothing in the wrap (phase 3 and up), after a loss it starts again.

## What the engine keeps out of the picture

* **Vanilla toasts**: `datapack/angel/pack.mcmeta` has a `filter` block that hides every vanilla advancement and recipe from the packs below ours
  (`{"namespace": "minecraft", "path": "^(advancement|recipe)/.*"}`), so that giving an item can never unlock a recipe and the shaft can never
  complete "Great View From Up Here"; our own namespace is not touched.
* **"Press Left Shift to dismount"**: the client shows it on the action bar when it learns that it is a passenger. A seat the engine has not seen
  yet (`angel.rd_seen` tag) arms `#rd`, and for 80 ticks an empty action bar goes out every tick (`story/t_ride`).
* **Props in the hand**: written books and paper (the letter, the photograph, the booklet) that land in the hotbar are moved to the same slot of the
  main inventory every 5 ticks (`story/t_inv`), so nothing sits in the selected slot as a big block in the lower right of the view; they are cleared by
  `story/start` and when scene 4 is entered (`ctx.enter_hooks`).

## Files

| file | role |
|---|---|
| `objective.py` | the objective system: waypoints, direction lines, the tutorial, the note panel |
| `audio.py`, `cards.py`, `cardfont.py`, `lead.py`, `hq_cage.py` | beds / music / sfx, title cards and their typeface, characters that lead, the cage's block lists |
| `pace.py` | the pacing table: presets `video` (default) and `full`; everything that decides the film's length |
| `livetest_companion.py` | live test of the companion guarantee on a scratch server (scene 4's crossing; `--jam`) |
| `build_story.py` | entry point (`--pace`, `--table`) |
| `core.py` | constants, writer + manifest, selectors, tree dispatch, quaternion helpers |
| `lines.py` | script.md + durations.json + sounds.json -> `angel:say/<key>`, `say/file/<key>` and the bridge handshake (`say/cue`, `claim`, `fallback`, `fb/*`) |
| `engine.py` | `Scene` (the step API), `Cond`/`C`, the compiler |
| `system.py` | load, tick, halt, entry points, ride lock, look check, the speak prompt, rig functions |
| `models.py`, `movers.py`, `motion.py`, `paths.py`, `carfx.py`, `fx.py` | display models, routes, speed profiles, drivable paths, effects |
| `ride_view.py`, `ride_view_old.py`, `ride_air.py` | the passenger's-eye ray-caster and the before / after numbers; scene 1's aircraft, wreck and birds |
| `world_probe.py` | read-only access to the built voxel worlds |
| `sim.py` | the offline simulator / checker |
| `scenes/` | one module per scene |

## Known issues in the sets (not touched: tools/world is not ours)

* `outskirts` tunnel: the passage through the portal wall is carved below the platform (its floor is 1 block lower than the anchors'
  level for z 12..20 and has a 4-block pit at the wall line z 21..22). The car on the wagon floats at the anchors' level.
* `outskirts` hill road: the lookout's bench (x 172..174, z 47..48) and map board (x 176..178, z 46..47) stand on the road line, and the
  road reaches the portal forecourt over a 2-block step at x 176..178 (the wing wall). The car clips them and pitches about 25 degrees
  there.
