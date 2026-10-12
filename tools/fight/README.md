# The Angel and the boss fight

Generator for two things in the Angel Attack datapack (namespace `angel`): the monster (`angel:angel/...`) and the scene-7
boss fight in the night city (`angel:fight/...`).  Run with the voice-assistant Python (numpy, pillow):

    python build_fight.py            # writes functions + a block tag into datapack\angel, removes what the last build wrote
    python build_fight.py --check    # only the checks (command tree check of every line, every called function exists)
    python build_fight.py --previews # also renders preview\*.png
    python selftest.py               # live test on a scratch copy of the server (ports 25603/25613), about 4 minutes

Files: `model.py` (the skeleton of boxes and the poses), `preview.py` (a z-buffer renderer of the same boxes),
`gen_angel.py`, `gen_fight.py` (the functions; all fight numbers are in `CFG` at the top of gen_fight.py),
`build_fight.py`, `selftest.py`, `build_manifest.json` (what the last build wrote; the next build removes exactly that).

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
| `function angel:angel/walk {x:..,y:..,z:..,speed:0.15}` | walks (blocks per tick) to the point, turning at 60 degrees/s, one stride animation per step, a footfall (sound, dust, smoke) when each foot lands. `scoreboard players get #arrived angel.walk` is 0 while walking and 1 on arrival; it then settles into `idle` |
| `function angel:angel/pose {pose:"idle"}` | `idle` (breathing loop), `regenerating` (hunched, pulsing loop), `charging` (eyes glow, chest out, jaw open), `dying` (about 4 s: knees buckle, folds back, core goes dark). Also: `windup`, `thrust`, `stagger`, `wrap_open`, `wrapping` |
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

Night look (changed after the first in-game screenshots): `warped_planks` skin (a dark teal, a bit lighter and more saturated than dark_prismarine)
at display brightness 8/10, bone-white parts at 15, thin pale `white_concrete` rim strips on the upper edges (chest, hump, hips, outer edge of arms
and thighs), emissive red strips around the core socket and a soft red `red_stained_glass` veil over the chest and the inner side of
the upper arms (they go dark / vanish when the core dies). Torso pose angles: **negative = leaning forward** (positive leans back).
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
   orange octagon of light (bars + glass squares, flashes and fades); a faint dotted octagon hangs in front of it while the
   giant is too far to cancel it.  Inside 12.5 the hit lands.  Hits on the body box only spark.  Hit boxes: core 4.5 blocks,
   body 7.2 x 16.8; the core box sits in front of the body box so it wins the ray.
3. Attacks (each telegraphed): eye beam (pose `charging`, eyes glow, warden sonic-charge sound, three rising beacon notes, a thin
   red sighting line along the locked path for the last 12 ticks, then a 1-block-step ray: stops at the first block that is not
   air/replaceable, so a tall building saves you; hit = cross-shaped flash + 25; it carves a 3x3x3 hole at its impact only above
   y = 70, so the street, plaza and lift are never touched); arm thrust (pose `windup` for 26 ticks, red ring on the ground where
   the arm will land, then the arm drives out 18.6 blocks: standing in the 9-block-wide zone costs 15 and slows you for 2 s; backing
   away avoids it; a core hit during the windup staggers it); advance along the avenue toward the plaza (the giant itself when
   within 75 blocks; kept on x 1152..1168, never farther south than z 140), stopping 17 blocks away.
4. Stages: whole core -> at 20 hits left it cracks (magma texture, roar, 80 ticks hunched and pulsing = `regenerating`: a window
   to hit it; phase B is faster) -> at 8 hits left it runs at the giant (0.9 blocks/tick), wraps (8 blocks in front of the giant,
   arms folded round, the giant is slowed) and the self-destruct countdown starts (14 s, bar, bell beeps that speed up in the
   last 5 s).  The remaining 8 core hits in that time break it; at 0 -> `won`.
5. `angel:fight/lost` (`lost_start`): giant health 0 or the countdown at 0 -> blindness fade, lines 7.19/7.20, then back
   to the launch at human size and a fresh `start` (barks reset, attempt counter +1).  `won`: the Angel dies (three-stage fold), a
   white cross-shaped pillar of light (190 tall, 60 across) with thunder, the body is removed, the lines 7.15-7.18 play, the
   giant is put back at human size on the lift at (1160.5, 64, 160.5) facing north, the fight is cleaned up and the story is told.

| Number | Value | Where (CFG key) |
|---|---|---|
| giant health / monster core hits | 100 / 40 | giant_hp, core_hp |
| beam, thrust damage | 25, 15 | beam_dmg, thrust_dmg |
| beam charge (A / B) | 40 / 34 ticks (2.0 / 1.7 s) | beam_charge, beam_charge_b |
| thrust windup, recovery | 26, 44 ticks | thrust_windup, thrust_recover |
| cooldown after beam (A / B), after thrust (A / B) | 150 / 105, 100 / 70 ticks | cd_* |
| cracks at / wraps at / countdown | 20 / 8 hits left / 280 ticks | crack_at, wrap_at, wrap_ticks |
| arm's length (barrier) | 12.5 blocks | near |
| invulnerability after a hit, regen | 20 ticks; +2 per second after 8 s unhurt | giant_inv, regen_* |
| core hit repeat limit | 7 ticks | hit_cd |
| walk speed A / B / wrap | 0.30 / 0.42 / 0.90 blocks per tick | speed_a, speed_b, wrap_speed |
| intro | the Angel waits until 6 s after the first steps (or 25 s) | intro_* |

Estimated length for a first-time player: 5 to 8 minutes (about 40 landed hits, three or four beams to dodge).  Not verified with a
human: only the stand-in test drives it.

### Barks

`function angel:fight/bark {id:"7_04"}` queues a line (once per attempt); `pump` (in the tick) plays the next one when
`#talking angel.story` is not 1 and 10 ticks have passed since the last one.  7.09 (`bark_beam`) repeats every 20 s if nothing is
queued or playing.  When: 7.01-02 at start, 7.03 at the first steps (8 blocks from the lift), 7.04-05 the first time you are hit,
7.06-08 the first blocked click, 7.08 the first core/body hit, 7.09 beam charge, 7.10-11 giant health at 25 or less,
7.12-13 the core cracking, 7.14 the wrap, 7.15-18 victory, 7.19-20 defeat.  Played lines are logged in storage
`angel:fight played`.

### Guards (build-time)

`function\fight\say\7_NN` is `function angel:say/7_NN` if `data\angel\function\say\7_NN.mcfunction` existed when the pack was built,
otherwise a `tellraw` of the line from script.md that also sets `#talking angel.story` to 1 for a while.  `fight\hand_won` calls
`function angel:story/fight_done {result:"won"}` only if `function\story\fight_done.mcfunction` existed, otherwise it writes
`"won"` to storage `angel:fight handoff`.  Rebuild once the story engine's files are in.  (A `function` of a missing id is a runtime error
that is silent, but the lead asked for no errors.)

### Test mode

`function angel:fight/test/start` makes an armor stand tagged `angel.giant` at the lift and starts the fight with it as the player.
`test/giant_at {x:..,y:..,z:..}` moves it, `test/hit_core` and `test/hit_body` simulate a left click, `test/set {name:"cd",value:0}`
sets any `#name angel.fight` score, `test/hurt {dmg:30}`, `test/status`, `test/off`.

## Function list

angel: `summon remove walk walk_go walk_tick turn step sync pose pose_* core_stage stop_walking` and the generated `s/<h>`,
`p/<pose>_<h>`, `pp/<pose>`, `fx_foot*`.
fight: `load tick start stop stop_quiet become_giant become_human leave_giant bark bark_beam pump say/7_NN hurt core_hit core_land
core_blocked body_hit ai_tick st_* begin_beam beam_fire beam_step wall_flash cross_flash pillar begin_thrust thrust_strike core_crack
wrap_start wrap_clamp self_destruct won_start won_tick won_final lost_start lost_tick restart hand_won test/*`.

## Risks only a human in a headset can check

* VR camera at 16x: near-clip and depth precision at a 26-block eye height, how the HUD and bossbars sit, comfort of 13 blocks/s
  smooth locomotion, whether roomscale arm swing reaches the 12.5-block barrier distance comfortably, whether the controller hit on
  the core box registers (it uses the same interaction path as a mouse click, but the Vivecraft swing tracker was not run).
* The hurt flash on the real player (`damage` 1 + instant health), blindness fade for the defeat.
* The look of the display entities at night: brightness overrides are 4 to 12; the glow and the halo glass.
* Sound mix: the warden sounds at volume 6 to 12.
* Beam hit height assumes the giant's chest is 18 blocks up; the aim line is not drawn through walls.
