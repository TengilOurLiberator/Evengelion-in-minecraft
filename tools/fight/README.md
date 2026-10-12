# The Angel and the boss fight

Generator for two things in the Angel Attack datapack (namespace `angel`): the monster (`angel:angel/...`) and the scene-7
boss fight in the night city (`angel:fight/...`).  Run with the voice-assistant Python (numpy, pillow):

    python build_fight.py            # writes functions + a block tag into datapack\angel, removes what the last build wrote
    python build_fight.py --check    # only the checks (command tree check of every line, every called function exists)
    python build_fight.py --previews # also renders preview\*.png
    python selftest.py               # live test on a scratch copy of the server (ports 25608/25618), about 10 minutes (also checks the model geometry: model.eye_clearance_table())
    python estimate.py               # how long the fight takes, from CFG, for a scripted attacker and a first-time player

Files: `model.py` (the skeleton of boxes and the poses), `preview.py` (a z-buffer renderer of the same boxes),
`gen_angel.py`, `gen_fight.py` (the functions; all fight numbers are in `CFG` at the top of gen_fight.py),
`build_fight.py`, `selftest.py`, `estimate.py`, `build_manifest.json` (what the last build wrote; the next build removes exactly that).

Output (all under `data\angel\`): `function\angel\**`, `function\fight\**` (including `say\7_NN`), `tags\block\fight\beam_pass.json`.
It does not touch `minecraft:load` / `minecraft:tick` tags (they already list `angel:fight/load` and `angel:fight/tick`).
Rebuild after the story engine has written `function\say\7_NN.mcfunction` and `function\story\fight_done.mcfunction`: the build
looks for those files (see "Guards").

## A. The monster

Public functions (all at the executor's position/rotation where position matters):

| Function | What |
|---|---|
| `function angel:angel/summon {height:60}` | builds it (removes any earlier one first). `height` is snapped to the nearest generated height: 20, 30, 40, 50, 60, 80, 100, 150 |
| `function angel:angel/remove` | kills every entity of it, stops its loops |
| `function angel:angel/walk {x:..,y:..,z:..,speed:0.15}` | walks (blocks per tick) to the point, turning at 80 degrees/s (8 per 2 ticks; it turns on the spot while more than 16 degrees off the target, so it never circles one), one stride animation per step, a footfall (sound, dust, smoke) when each foot lands. `scoreboard players get #arrived angel.walk` is 0 while walking and 1 on arrival; it then settles into `idle` |
| `function angel:angel/pose {pose:"idle"}` | `idle` (breathing loop), `regenerating` (hunched, pulsing loop), `charging` (eyes glow, chest out, jaw open), `dying` (about 4 s: knees buckle, folds back, core goes dark). Also: `windup`, `thrust`, `stagger`, `wrap_open`, `wrapping`, `wrap_tight`, `wrap_hit` |
| `function angel:angel/core_stage {stage:0}` | core look: 0 whole, 1 cracked (magma texture), 2 dead |

Entities: 133 `block_display` parts (tag `angel.part`, `angel.p<N>`; plus `angel.eye`, `angel.corebody`, `angel.jaw`), a `marker`
`angel.root` (position + yaw of the whole monster), markers `angel.aim`, `angel.target`, `angel.aimpt`, and two `interaction`
hit boxes (`angel.core`, `angel.body`).  Everything has the tag `angel.mon`.  Scoreboards: `angel.mon` (internal), `angel.walk`
(`#arrived`).  Storage `angel:mon`.

How it works: every part stands at one point (the foot position) and carries its offset in its `transformation`, so the whole
monster moves and turns by teleporting the parts to the root (`teleport_duration` 2 smooths it).  A pose is one function per
(pose, height) that rewrites the transformation of all parts with `start_interpolation:0` and `interpolation_duration` taken
from `#dur angel.mon`, so the client animates between two key poses.  Walking alternates two key poses (planted-forward
leg / trailing leg with bent knee) and sets the step time to stride / speed, so the planted foot stays put.
The 26.3 detail that bites: `block_state` is a plain string (`"minecraft:red_concrete"`); `{Name:..}` and
`minecraft:x[prop=..]` decode to air.  A summon's `transformation` needs all four keys; a `data merge` may give fewer.
Another one: a relative `rotate @s ~8 ~` is relative to the *execute context*, not to the entity, so `as @e[...] run rotate @s ~8 ~` set the yaw to 8 every time and the
monster never turned more than 8 degrees (found by the back-off test, fixed in `angel:angel/turn` with `at @s`; `tp @s ~ ~ ~ ~8 ~` behaves the same way).

Night look (changed after the first in-game screenshots): `warped_planks` skin (a dark teal, a bit lighter and more saturated than dark_prismarine)
at display brightness 8/10, bone-white parts at 15, thin pale `white_concrete` rim strips on the upper edges (chest, hump, hips, outer edge of arms
and thighs), emissive red strips around the core socket and a soft red `red_stained_glass` veil over the chest and the inner side of
the upper arms (they go dark / vanish when the core dies). Torso pose angles: **negative = leaning forward** (positive leans back).
**Eye clearance** (added after the first in-game playthrough, where the camera ended up inside the staggering monster's arm): `model.eye_clearance_table()`
measures, for every pose family, the distance from the giant's eye (25.9 up, straight ahead of the monster; the stagger also 0 to 6 blocks to the side) to
the nearest visible box, over the distances at which the pose is seen and over the in-between frames of each interpolation (the client lerps translation and
scale and slerps rotation; `model.boxes_between` does the same).  The selftest requires 2.75 blocks ("about 3") everywhere:

| Pose (distance of the eye from the monster's feet) | Before | After |
|---|---|---|
| idle (9 to 17, the close range: from where the core is hit to the AI's stand-off) | 2.81 (the beak hook) | 2.98 |
| walk / windup (9 to 17) | 3.13 / 5.14 | 3.13 / 5.14 |
| stagger of the back-off (9 to 17; and 4 to 17, up to 6 blocks to the side) | 2.80 (0.0 at 4 blocks: inside its skull/pauldron) | 9.68 (4.8 at 4 blocks), and 4.67 on the worst in-between frame |
| regenerating, the crack's pause (9 to 17) | 0.40 (the crest of the hump) | 3.00 |
| arm thrust (14.1 to 23.1: where its zone reaches the giant) | 3.12, the hand at head height (25.7 up) | 5.56, the hand strikes the chest (17.9 up, 14.7 ahead) |
| charging (24 and more: the beam is only chosen beyond the thrust range) | 11.7 | 11.7 |
| wrapped (10 blocks; 8 before) | 8.9 (it leaned away, the arms folded across itself) | 4.0 close, 3.05 tight, 6.6 hit; 3.2 on the worst in-between frame |

`charging` is three stages (0, 10, 24 ticks in): the eye holes blaze (extra glowstone boxes + orange glass that grow with the key `eyeg`, tags
`angel.eyeglow`), the body leans forward, the arms are drawn back and out and a glow gathers in front of the mask (key `gather`, tag
`angel.gather`, on the hips frame). `regenerating` is an 8-frame loop of 10 ticks (slow breathing, flickering core, plates askew:
`regen_0..7`). `dying` kneels, then slumps forward over its knees with the arms trailing on the ground.

Look (previews in `preview\`, `sheet_<pose>.png` = front, side, three-quarter, close-up of the chest; `sheet_poses.png` = six
poses): dark_prismarine skin shown dim so it reads dark green-black, black_concrete joints/hands/feet, bone_block plates, ribs,
mask and toes; a bird-skull mask in the middle of the upper chest with two black eye holes (they turn glowstone when it
charges), a beak and a hinged jaw; the core (four turned red cubes, a glass halo) in a dark socket under the mask; no neck, a dark
hump behind; three-fingered hands on arms that hang to the knees.

## B. The fight

`angel:fight/start` (as the player, who has just arrived at `city.launch_top`) -> `become_giant`, summons the Angel (height 30)
at (1160, 64, 50) facing south, bossbars, barks 7.01/7.02; `stop` cleans everything and returns to human size; `load` and `tick`
are the hooked ones (`tick` is one score check when no fight runs).  `become_giant` / `become_human` run as the player.

### The player as the giant (what is set, and why)

| Attribute | Giant | Default | Why |
|---|---|---|---|
| `scale` | 16 | 1 | 16 is the attribute's maximum (RangedAttribute 0.0625..16, `server-26.3.jar` class `Attributes`; confirmed live: setting 20 reads back 16). Eye height 1.62 x 16 = 25.9 blocks; hitbox 9.6 wide, 28.8 tall: fits the 16-wide streets |
| `step_height` | 2.6 | 0.6 | `LivingEntity.maxUpStep()` returns the attribute unscaled, so the 16x giant would still stumble on a 1-block step. 2.6 walks over clutter, kerbs and half-block plates but not onto the 8-block shops |
| `movement_speed` | 0.30 | 0.10 | not scaled either; 0.3 is about 13 blocks/s: crossing the 96-block plaza in 7 s, looks like a slow stride at 29 blocks tall |
| `jump_strength` / `gravity` | 1.0 / 0.12 | 0.42 / 0.08 | heavier fall, jump of 4.3 blocks (simulated: vanilla comes out 1.25) in 0.9 s |
| `safe_fall_distance`, `fall_damage_multiplier` | 48, 0 | 3, 1 | no fall damage |
| `entity_interaction_range` / `block_interaction_range` | 18 / 20 | 3 / 4.5 | long arms (range maximum 64) |
| `attack_damage` / `attack_knockback` | 20 / 2 | 2 / 0 | |
| `knockback_resistance` | 0.6 | 0 | |

Vivecraft (read from `vivecraft-26.3-1.3.17-fabric.jar`): the client's world scale is
`VRPlayer.worldScale = rawWorldScale (the VR "World Scale" setting) x ScaleHelper.getEntityEyeHeightScale(player)`, which is
`LivingEntity.getScale()` (the `scale` attribute), clamped to 0.025..100.  So a `scale` of 16 makes the room, the head and the
controllers 16 times bigger in the world with no client setting: one metre of arm swing is 16 blocks of reach, the eye height
is the real height x 16 (22 to 29 for most adults, not exactly 25.9).  The client sends that total to the server
(`ClientNetworking`, `WorldScalePayloadC2S`) and the server multiplies the hand offsets by it (`ServerVivePlayer`).
The server config `vivecraft-server-config.toml` has `[worldScale] limitRange = false`, so 16 is allowed; if somebody turns
the range limit on (the stored max is 2.0) the client will refuse the connection ("Total VR world scale out of range").
Keep the player's own VR World Scale setting at 1: it multiplies.

### Mechanics

1. Bossbars `angel:fight/giant` (UNIT-01, green/yellow/red) and `angel:fight/angel` (core hits left, notched), and
   `angel:fight/wrap` (the self-destruct countdown).  The real player also takes a 1-point `minecraft:magic` hit followed at
   once by instant health (for the hurt flash and haptics); the true health is the score `#gh`.
2. The barrier: a click on the core box from more than 12.5 blocks (core centre to the giant's shoulders, 22 up) stops on an
   orange octagon of light (bars + glass squares, flashes and fades, `angel:sfx.barrier`); a faint dotted octagon hangs in front of it
   while the giant is too far to cancel it.  Inside 12.5 the hit lands.  Hits on the body box only spark.  Hit boxes: core 4.5 blocks,
   body 7.2 x 16.8; the core box sits in front of the body box so it wins the ray.
   **Three outcomes of a click on the core** (`core_hit`): *landed* (in reach, core not guarded: flash, crits, red dust,
   `angel:sfx.giant_punch`, counter -1; this is the only thing that arms the guard `#hitcd` for `hit_cd` = 24 ticks and counts toward the
   back-off), *guarded* (in reach, inside the guard: a small burst of electric sparks and smoke at the core and a dull clank,
   `block.iron_trapdoor.close` at pitch 0.5; nothing else happens, the guard keeps running down; the test counter `#guarded` goes up) and
   *blocked* (beyond reach, or the barrier is raised: the octagon, rate-limited to one per 6 ticks, its 3.6 s tone to one per 2 s; does not touch the guard).  A body hit
   only sparks (crit + electric spark + anvil tap) and never touches the guard.
   Why the clank is a vanilla sound: the server only sends a `playsound` to players within 16 x volume blocks of the origin, measured from
   the player's feet, and the core is about 22 blocks above a giant's feet, so the volume must be at least 1.4; a 3.6 s tone such as
   `sfx.barrier` would turn a click into a note.  (Volume above 1 does not make a sound louder, only audible from farther: the client clamps
   the gain at 1 and fades it linearly to the edge of volume x attenuation distance.)
3. Attacks (each telegraphed): eye beam (pose `charging`, eyes glow, `angel:sfx.beam_charge`, a thin
   red sighting line along the locked path for the last 12 ticks, then a 1-block-step ray: stops at the first block that is not
   air/replaceable, so a tall building saves you; hit = cross-shaped flash + 25; it carves a 3x3x3 hole at its impact only above
   y = 70, so the street, plaza and lift are never touched); arm thrust (pose `windup` for 26 ticks, red ring on the ground where
   the arm will land, then the arm drives out 18.6 blocks: standing in the 9-block-wide zone costs 15 and slows you for 2 s; backing
   away avoids it; a core hit during the windup staggers it); advance along the avenue toward the plaza (the giant itself when
   within 75 blocks; kept on x 1152..1168, never farther south than z 140), stopping 17 blocks away.
4. **Back-off** (`backoff_*` in CFG): after every `backoff_hits` (8) LANDED core hits in phases 1 and 2 (the wrap phase is not counted) the monster
   disengages.  `backoff_start`: it is shoved 4.8 blocks (`shove` 0.8 x `shove_ticks` 6, interpolated: the parts teleport with duration 2) straight back
   toward the retreat point (along the avenue, away from the giant) in the first 6 ticks, while the `stagger` pose RECOILS (torso thrown back, arms flung up
   and out and behind, a step back; see the eye clearance table: nothing comes toward the giant) for 30 ticks, the barrier goes up (`#bar` = 1: every click on the core is blocked,
   even in reach; the octagon flares, then pulses every 1.2 s), it turns its back (8 degrees per tick) and walks `backoff_dist` (30) blocks
   along the avenue **away from the giant** at 0.45 blocks/tick, never past the avenue's far end (z 50 = `city.angel_start`, or z 140 the
   other way).  With less than `backoff_min` (10) blocks of room it steps to the other side of the avenue instead (x 1153 if it is on the
   east half, x 1167 if on the west half), still retreating what room there is.  Then it turns to face the giant, **holds its ground** (`#hold`: it
   does not advance, barrier still up) and after `backoff_cd` (50 ticks) its normal cycle resumes: the giant being far, `choose` picks the eye
   beam, which is the point at which cover matters.  The end of its first attack (beam or arm thrust) lets the barrier down (a lowered tone,
   a burst of light) and releases the hold; `backoff_hold` (300 ticks) is the fallback.  The back-off does not fire on the hit that cracks the core
   nor during the pause after it (the player's window): it follows on the next landed hit.  States 9 (stagger) and 10 (retreat); scores
   `#bo` (landed hits since the last back-off), `#bar`, `#hold`.
5. Stages: whole core -> at 30 hits left it cracks (magma texture, roar + `sfx.core_crack`, 80 ticks hunched and pulsing = `regenerating`: a window
   to hit it; phase B is faster; **this is the checkpoint**, see 6) -> at 10 hits left it runs at the giant (0.9 blocks/tick) and wraps itself round it.
   **The wrap (phase 3; `wrap_*` in CFG)**, designed so that a first-time player who keeps swinging wins it on the first or second try:
   * **No guard, no reach, no barrier.** While phase 3 runs every click that connects counts (`wrap_hit`; `core_hit` and `body_hit` both route there before any
     other test).  The body box is made the big target while the monster runs in and is wrapped (14 x 30 blocks, the monster's root 10 blocks in front of the
     giant): any swing within 30 degrees to the side and from 10 above to 60 below the line to it hits (checked by the selftest with a slab test, reach 18), the eye
     is outside the box.  (A click on the core box counts as well, of course.)
   * **The numbers**: 10 hits, a 16 s bar (`wrap_ticks` 320), +0.5 s on the bar for every landed hit (`wrap_bonus` 10, never above the start).  One hit per 1.5 s:
     the last of the ten lands at 15 s with 5.5 s on the bar (needs at least 5); a player who stops swinging for 6 s in all loses (-0.5 s); the scripted clicker
     (0.95 s) wins with 11 s to spare; one hit every 2 s wins with 0.5 s (the edge of "fair").
   * **The tell and the wait**: on wrapping, the title "BREAK LOOSE / hit the core - keep swinging", the action bar, the core flares and the bark 7.14 goes to
     the FRONT of the queue.  The countdown (`#wgo` 0 -> 1) does not run until 7.14 has begun (`bark_play` sets `#began_7_14`), or `wrap_wait` (100 ticks) if the line
     is stuck behind another one; hits count during the wait.
   * **Feedback per hit**: flash, crits, sparks, red dust and `sfx.giant_punch` at the core, the wrap shudders (pose `wrap_hit`, 4 ticks), the bar jumps back, the hits left
     on the action bar, and the core shows crack 1, 2, 3, 4 (white slivers of light across it, `angel:angel/core_crack_N`) at 8, 6, 4, 2 hits left.
   * **Pressure**: a heartbeat (`entity.warden.heartbeat`, pitch and volume rise) whose pause shrinks from 26 ticks to 6 as the bar runs down, a ring of red light that closes
     round the giant (radius 9 / 7 / 5 / 3.5), the monster squeezes (pose `wrap_tight`) in the last 8 s, bell beeps and a white bar in the last 5 s.
   The remaining hits break it; at 0 -> `won`.
6. `angel:fight/lost` (`lost_start`): giant health 0 or the countdown at 0 -> blindness fade, lines 7.19/7.20, then `restart`.  **Before the core has cracked** (`#ck` 0):
   back to the launch at human size and a fresh `start` (barks reset, attempt counter +1).  **Once it has cracked** (`core_crack` -> `ck_save` sets `#ck` 1 and stores
   where the monster and the giant stood): `restart_ck` keeps the giant giant and the screen black, and 3 s later `start_ck` puts the giant back where it stood (healed,
   100), rebuilds the monster where it stood, with the core at its crack health (30), phase 2 and the hunched pause (it calls `core_crack` again), the intro lines
   (7.01 to 7.08) not repeated, attempt +1.  A loss in the cracked phase or the wrap both come back to this point.  Phase sequence seen from outside: 5 (lost) -> 0 (`#run` 0, 60 ticks)
   -> 2 (-> 3 ...); the launch restart is 5 -> 0 -> 1.  The story's polling (`s07.py`: beat 81 on phase 5 and back to 70 with `#run` 1 and phase 0..3; music re-armed on phase 0,
   `fight_final` on phase 2 or 3) copes with both; the selftest runs that polling line for line (`StoryModel`).  `won`: the Angel dies (three-stage fold), a
   white cross-shaped pillar of light (190 tall, 60 across) with `angel:sfx.cross`, the body is removed, the lines 7.15-7.18 play, the
   giant is put back at human size on the lift at (1160.5, 64, 160.5) facing north, the fight is cleaned up and the story is told.

| Number | Value | Where (CFG key) |
|---|---|---|
| giant health / monster core hits | 100 / 60 | giant_hp, core_hp |
| beam, thrust damage | 25, 15 | beam_dmg, thrust_dmg |
| beam charge (A / B) | 40 / 34 ticks (2.0 / 1.7 s) | beam_charge, beam_charge_b |
| thrust windup, recovery | 26, 44 ticks | thrust_windup, thrust_recover |
| cooldown after beam (A / B), after thrust (A / B) | 150 / 105, 100 / 70 ticks | cd_* |
| cracks at / wraps at / countdown | 30 / 10 hits left / 320 ticks (16 s) | crack_at, wrap_at, wrap_ticks |
| wrap: time back per landed hit / guard / squeeze at / distance / most wait for 7.14 | +10 ticks (0.5 s) / none / 160 ticks left / 10 blocks / 100 ticks | wrap_bonus, (hit_cd does not apply), wrap_tight_at, wrap_dist, wrap_wait |
| wrap: cracks of the core at hits left | 8, 6, 4, 2 | wrap_crack_hits |
| back-off: thrown back | 0.8 x 6 ticks = 4.8 blocks | shove, shove_ticks |
| arm's length (barrier) | 12.5 blocks | near |
| invulnerability after a hit, regen | 20 ticks; +2 per second after 8 s unhurt | giant_inv, regen_* |
| core guard after a LANDED hit (phases 1 and 2 only) | 24 ticks (1.2 s) | hit_cd |
| back-off: after this many landed hits (not the wrap) | 8 | backoff_hits |
| back-off: retreat distance / least room before it sidesteps | 30 / 10 blocks | backoff_dist, backoff_min |
| back-off: stagger, retreat speed, wait before its next attack, longest hold | 30 ticks, 0.45 blocks/tick, 50 ticks, 300 ticks | backoff_stagger, backoff_speed, backoff_cd, backoff_hold |
| walk speed A / B / wrap | 0.30 / 0.42 / 0.90 blocks per tick | speed_a, speed_b, wrap_speed |
| intro | the Angel waits until 6 s after the first steps (or 25 s) | intro_* |

### How long it takes

`python estimate.py` accounts for the phases from CFG (it is arithmetic, not a simulation; the assumptions are in the file):
50 landed hits before the wrap, 6 back-offs (after hits 8, 16, 24, 32, 40, 48), the 10-hit wrap.

* (a) the scripted attacker of the earlier test (a click every 0.95 s, never dodges, runs at 13 blocks/s): the guard swallows every other
  click, so one landed hit per 1.9 s; at each back-off it can only wait for the barrier, which stays up for stagger + retreat + 50 ticks +
  the first beam (219 ticks = 11 s): **about 180 s = 3.0 minutes** by the arithmetic (the wrap, with no guard, takes it 9.5 s with 11 s to spare;
  with the old guard it needed 19 s and lost twice with one hit left, the first playthrough's finding).  Measured live earlier (scratch server, the giant kept 9
  blocks in front of the monster, a click every 0.95 s, never dodging): **won in 150 s = 2.5 minutes**, 5 back-offs (the 3 hits landed during the intro
  do not count), the giant undamaged (it was 63 s with 40 hits and a 7-tick guard).
* (b) a plausible first-time player: a landed hit every 2.0 s while free to hit (swing, aim at a 4.5-block target, the guard), 2.5 s lost to
  each arm thrust (the cycle is 8.5 s, 7 s after the crack), 24 s from the start to the first hit (about 85 blocks at 6 blocks/s, the first
  beam's cover), after each retreat 8 s to close the 30 blocks and 4 s to take cover from its beam (so 17 s per back-off), a hit every 1.5 s in
  the wrap (5.5 s to spare on its bar): **about 290 s = 4.9 minutes**.  A slower player (2.6 s per hit, 3 s per thrust, 10 s + 5 s per back-off) comes out at 6.4 minutes,
  a quick one (1.5 s per hit) at 3.6.  Not modelled: the player dying (giant health 100: four thrusts or four beams, regenerating 2 per second
  after 8 s unhurt) and restarting.  Not verified with a human: only the stand-in test drives it.

### Sounds

Every `playsound` / `stopsound` id in the generated functions is checked at build time (`build_fight.py`, also `--check`) against
`pack\angel-resources\assets\angel\sounds.json` (ours) and the installed client's `sounds.json` (vanilla, found through the asset index under
`%APPDATA%\.minecraft\assets`), and again by `selftest.py`.  Library events used: `sfx.barrier` (blocked hit, the barrier going up and down),
`sfx.core_crack` (the crack), `sfx.beam_charge`, `sfx.beam_fire`, `sfx.giant_hit` (the giant is hurt), `sfx.giant_punch` (a landed core
hit), `sfx.cross` (the pillar when it dies), `sfx.heartbeat` (the giant's health at 25 or less: replayed every 10 s, cut when health comes
back or the fight ends), `sfx.footfall_giant` (the monster's steps).  Vanilla ones that remain have no library counterpart: the warden's
roars, hurt and thrust sounds, the bell beeps of the countdown, the explosions and lightning where the beam lands.  The `playsound` volumes
are mostly above 1 on purpose (server range = 16 x volume blocks from the player's feet; the client clamps the gain to 1 and fades by distance).

### Barks

`function angel:fight/bark {id:"7_04"}` queues a line (once per attempt); `pump` (in the tick) plays the next one when
`#talking angel.story` is not 1 and 10 ticks have passed since the last one.  7.09 (`bark_beam`) repeats every 20 s if nothing is
queued or playing.  When: 7.01-02 at start, 7.03 at the first steps (8 blocks from the lift), 7.04-05 the first time you are hit,
7.06-08 the first blocked click, 7.08 the first core/body hit, 7.09 beam charge, 7.10-11 giant health at 25 or less,
7.12-13 the core cracking, 7.14 the wrap, 7.15-18 victory, 7.19-20 defeat.  Played lines are logged in storage
`angel:fight played`.

### Guards (build-time)

`function\fight\say\7_NN` is `function angel:say/file/7_NN` (the pre-rendered file, played by the game itself: a bark is never cued to the voice
bridge, see tools/story/lines.py) if `data\angel\function\say\7_NN.mcfunction` existed when the pack was built,
otherwise a `tellraw` of the line from script.md that also sets `#talking angel.story` to 1 for a while.  `fight\hand_won` calls
`function angel:story/fight_done {result:"won"}` only if `function\story\fight_done.mcfunction` existed, otherwise it writes
`"won"` to storage `angel:fight handoff`.  Rebuild once the story engine's files are in.  (A `function` of a missing id is a runtime error
that is silent, but the lead asked for no errors.)

### Test mode

`function angel:fight/test/start` makes an armor stand tagged `angel.giant` at the lift and starts the fight with it as the player.
`test/giant_at {x:..,y:..,z:..}` moves it, `test/hit_core` and `test/hit_body` simulate a left click, `test/set {name:"cd",value:0}`
sets any `#name angel.fight` score (`#guarded` counts the hits that sparked on the guard), `test/hurt {dmg:30}`, `test/status`, `test/off`.

## Function list

angel: `summon remove walk walk_go walk_tick turn step sync pose pose_* core_stage stop_walking` and the generated `s/<h>`,
`p/<pose>_<h>`, `pp/<pose>`, `fx_foot*`.
fight: `load tick start stop stop_quiet become_giant become_human leave_giant bark bark_beam pump say/7_NN hurt core_hit core_land
core_blocked core_guarded body_hit wall_draw bar_pulse heartbeat heartbeat_stop ai_tick st_* begin_beam beam_fire beam_step wall_flash cross_flash pillar begin_thrust thrust_strike backoff_check backoff_start backoff_aim backoff_side st_bo_stagger st_bo_retreat bo_turn bo_go bo_end hold_tick bo_release core_crack
bo_shove wrap_start wrap_clamp wrap_follow wrap_wait wrap_count wrap_hit wrap_hit_fx wrap_flare wrap_squeeze wrap_loosen wrap_restore wrap_beat wrap_ring(_N) wrap_beep self_destruct ck_save start_ck restart_ck restart_ck_go bark_front won_start won_tick won_final lost_start lost_tick restart hand_won test/*`.
angel: also `pose_wrap_tight pose_wrap_hit core_crack_1..4` (the wrap's crack slivers; hidden again by `core_stage_0/1/2`).

## Risks only a human in a headset can check

* VR camera at 16x: near-clip and depth precision at a 26-block eye height, how the HUD and bossbars sit, comfort of 13 blocks/s
  smooth locomotion, whether roomscale arm swing reaches the 12.5-block barrier distance comfortably, whether the controller hit on
  the core box registers (it uses the same interaction path as a mouse click, but the Vivecraft swing tracker was not run).
* The hurt flash on the real player (`damage` 1 + instant health), blindness fade for the defeat.
* The look of the display entities at night: brightness overrides are 4 to 12; the glow and the halo glass.
* Sound mix: the warden sounds at volume 6 to 12.
* Beam hit height assumes the giant's chest is 18 blocks up; the aim line is not drawn through walls.
