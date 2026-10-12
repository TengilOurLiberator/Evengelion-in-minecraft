"""Scene 1, The empty city (outskirts, noon), staged to cue-sheet.md.

Over black the card A.D. 2015 with the cicadas coming in underneath; the boy wakes on the station platform (amb.cicadas + amb.town_empty,
a crossing bell far off) with the letter and the photograph in hand.  The note on the photograph now sends him to the payphone outside the
station: the handset says what it says (1.01, 1.02), the hang-up clicks and the cicadas STOP, and there is silence.  Out in the street, once
he looks down it, a girl in a school uniform stands in the middle of the road twenty blocks off, perfectly still, facing him, with nothing
behind her but empty street; the moment he looks away (or after six seconds) she is gone and the birds go up off the wires.  The ground
jumps, car alarms far off, the card ANGEL ATTACK for two seconds while the monster steps out between the hills, and the picture comes back
on the same view: five aircraft the size of houses circling it and firing, the dread, the siren, 1.03 from the loudspeakers, one of them
hit, trailing fire across the sky and coming down burning behind the boy (the wreck stays), and the blue roadster sliding out of the smoke.

Sound plan (everything is a library event; nothing vanilla is left in this scene):
    A.D. 2015 card ........ sfx.card, then amb.cicadas + amb.town_empty fading in under the held card
    the phone ............. sfx.phone_pickup, 1.01, 1.02, sfx.phone_hangup, then everything stops (the cicadas go, no bed at all)
    the girl, the birds ... sfx.birds_up in the silence, at the instant she is gone
    the jolt .............. sfx.jolt, sfx.car_alarms_far (still no bed: the alarms are all there is)
    ANGEL ATTACK card ..... sfx.card; behind it the monster and the aircraft begin and its own footfalls (tools/fight: angel:angel/walk plays them,
                            so this scene adds none: one source, not two)
    the street ............ music.dread, sfx.siren looped from the old town (it fades with distance as the car later drives away), amb.town_empty
                            in again, sfx.jet_pass (from the sky over the street), sfx.gunfire_far, sfx.explosion_far; 1.03
    the crash ............. sfx.crash and sfx.explosion_near (ride_air.py), the dread is cut under the blast
    the car ............... sfx.car_arrive, sfx.car_door (carfx.py)

Where things are (outskirts): the street runs east from outskirts.street (93.5, 128.5), z 128.5 its middle, with wires (iron chains) at z 121 and 135 and
parked cars at the kerbs; the girl stands at street.x + 20 (113.5), the monster walks in from x 228 along the same line, the wreck lies at
outskirts.crash (84.5, 142.5): behind the boy's right shoulder as he faces east (he hears it, then turns), and the car slides out of that smoke.

Beats: 10 until Misato arrives, then 11.
"""
import json
import random

import carfx
import fx
import paths
import ride_air
import worldgen_sky
from audio import sfx
from context import (actionbar, cast_look, cast_mount, cast_remove, cast_summon, play_at, play_player, ride_passenger, title,
                     tp_player)
from core import NS, OBJ, TAG, blind, P, PA, T, fn, local_to_world, num, qaxis, sadd, sset
from engine import C, Cond
from models import transformation_nbt
from motion import Path

N = 1
TITLE = "The empty city"

SIREN_AT = (70.0, 78.0, 118.0)      # the air-raid siren, on a roof in the old town west of the street (shared with scene 2: it fades as the car leaves)
SIREN_VOL = 1.8
ALARMS_AT = (112.0, 66.0, 168.0)    # the car alarms far off, south-east of the street
MON_H = 100                         # the Angel's height in blocks (angel:angel/summon snaps to 20, 30, 40, 50, 60, 80, 100, 150): at 135 blocks 100 fills 36 degrees of the view from outskirts.street, 60 only 24
WALK_SPEED = 0.15                   # blocks per tick: 3 a second, a hundred-block giant crossing the hills in slow, heavy strides
GIRL_AHEAD = 12.0                   # blocks east of the player (where he stands when she is called up), down the middle of the road: 20 was a figure of a few pixels
GIRL_SEEN_WITHIN = 0.68             # the vision starts when the gaze is within this chord of the unit circle round the girl (2 asin(0.34) = 40 degrees)
GIRL_AWAY_TICKS = 14                # she goes when he has looked away for 0.7 s
GIRL_MAX = 6.0                      # ... or six seconds after she appears
PHONE_FRONT = (65.5, 64.5, 118.0)   # just outside the open front of the booth (its doorway is at z 116, the telephone on the back wall at z 113)


PARKED_N = (104, 124, 158, 164)       # the parked cars of the street set (tools/world/sets/outskirts.py): x of the min corner, north kerb (z 123..124)
PARKED_S = (106, 126, 145, 162)       # ... and south kerb (z 132..133)
CA_STEPS = 33                         # half cycles of the alarm lamps (5 ticks each): 8.2 s, the length of sfx.car_alarms_far


def jolt_street(ctx, ground_y):
    """The ground jumps, felt all along the street: a strong low sound (sfx.jolt and a giant step from the east), dust and plaster shaken off the
    wires and the shop fronts for the whole length of the street in four bursts, the alarm lamps of the parked cars flashing for eight seconds,
    and a second flock off the wires behind him.  The camera is not shaken (VR).  (The shaking of the street furniture itself is not done: every
    lamp post and signal is a block of the set, and a display copy of each would be a rebuild of the street.)"""
    def reg(path, lines):
        ctx.extra_functions[path] = lines
        ctx.fx_scheduled.append(path)
        return f"function {NS}:{path}"
    wires = [(x, z) for x in range(62, 160, 8) for z in (121.0, 135.0)]
    fronts = [(x, z) for x in range(64, 160, 9) for z in (117.0, 139.0)]

    def burst(n):
        lines = []
        for (x, z) in wires:
            lines.append(f"particle minecraft:falling_dust{{block_state:\"minecraft:gray_concrete\"}} {num(x)} {num(ground_y + 11)} {num(z)} 3.5 0.5 0.6 0 {n} force")
        for (x, z) in fronts:
            lines.append(f"particle minecraft:falling_dust{{block_state:\"minecraft:stone\"}} {num(x)} {num(ground_y + 9)} {num(z)} 4 4 0.6 0 {n} force")
            lines.append(f"particle minecraft:dust_plume {num(x)} {num(ground_y + 0.4)} {num(z + (2.0 if z < 128 else -2.0))} 4 0.3 0.8 0.02 {n // 2 + 2} force")
        return lines
    b1 = reg("story/fx/jolt_s1", burst(6))
    b2 = reg("story/fx/jolt_s2", burst(5))
    b3 = reg("story/fx/jolt_s3", burst(4))
    # the parked cars' alarm lamps: two lamps on each car, flashing amber
    lamps = []
    for x in PARKED_N:
        for dx in (0.45, 4.55):
            lamps.append((x + dx, 123.95))
    for x in PARKED_S:
        for dx in (0.45, 4.55):
            lamps.append((x + dx, 133.05))
    spawn = [f'summon minecraft:block_display {num(x - 0.2)} {num(ground_y + 1.05)} {num(z - 0.2)} {{Tags:["{TAG}","angel.calamp"],block_state:"minecraft:gray_concrete",'
             f'brightness:{{sky:0,block:0}},view_range:3.0f,transformation:{{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[0.4f,0.4f,0.4f],right_rotation:[0f,0f,0f,1f]}}}}'
             for (x, z) in lamps]
    lit = 'execute as @e[tag=angel.calamp] run data merge entity @s {block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15}}'
    dark = 'execute as @e[tag=angel.calamp] run data merge entity @s {block_state:"minecraft:gray_concrete",brightness:{sky:0,block:0}}'
    ca_on = f"{NS}:story/fx/ca_on"
    ca_off = f"{NS}:story/fx/ca_off"
    for name, state, nxt in (("ca_on", lit, ca_off), ("ca_off", dark, ca_on)):
        ctx.extra_functions[f"story/fx/{name}"] = [
            state, sadd("#f.cn"),
            f"execute if score #f.cn {OBJ} matches ..{CA_STEPS - 1} run schedule function {nxt} 5t",
            f"execute if score #f.cn {OBJ} matches {CA_STEPS}.. run kill @e[tag=angel.calamp]"]
        ctx.fx_scheduled.append(f"story/fx/{name}")
    # a second flock: off the wires behind him, west of the street's middle (the first flock, at the girl, was east)
    rnd = random.Random(31)
    bspawn, bfly = [], []
    for i in range(22):
        x = rnd.uniform(62, 100)
        z = rnd.choice([121.0, 135.0]) + rnd.uniform(-0.2, 0.2)
        bspawn.append(f'summon minecraft:block_display {num(x)} {num(ground_y + 11)} {num(z)} {{Tags:["{TAG}","angel.pigeon","angel.pigeon_{i}"],block_state:"minecraft:black_concrete",'
                      f'view_range:2.0f,interpolation_duration:60,teleport_duration:0,{transformation_nbt((-0.25, 0, -0.14), (0, 0, 0, 1), (0.5, 0.12, 0.28))}}}')
        dx, dz, up = rnd.uniform(-18, 18), rnd.uniform(-18, 18), rnd.uniform(12, 26)
        bfly.append(f"data merge entity @e[tag=angel.pigeon_{i},limit=1] {{start_interpolation:0,interpolation_duration:60,"
                    f"{transformation_nbt((dx - 0.25, up, dz - 0.14), qaxis('y', rnd.uniform(-70, 70)), (0.5, 0.12, 0.28))}}}")
    ctx.extra_functions["story/fx/birds2_fly"] = bfly
    ctx.extra_functions["story/fx/birds2_kill"] = ["kill @e[tag=angel.pigeon]"]
    ctx.fx_scheduled += ["story/fx/birds2_fly", "story/fx/birds2_kill"]
    return [
        # the sound: a deep jolt under his feet, and the giant's step from the east (the ground tells him before the picture does)
        sfx("sfx.jolt", None, 4.0, 0.85), sfx("sfx.footfall_giant", at=(172.0, ground_y + 2, 128.5), vol=6.0, pitch=0.9, minvol=0.7),
        f"execute at {P()} run particle minecraft:dust_plume ~ ~0.5 ~ 4 0.5 4 0.03 80 force",
        f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:stone\"}} ~ ~4 ~ 5 1.5 5 0.0 70 force",
        b1, f"schedule function {NS}:story/fx/jolt_s2 8t", f"schedule function {NS}:story/fx/jolt_s3 18t",
        *spawn, *bspawn, sset("#f.cn", 0), f"function {ca_on}",
        f"schedule function {NS}:story/fx/birds2_fly 3t", f"schedule function {NS}:story/fx/birds2_kill 90t",
    ]


def build(s, ctx):
    A = ctx.anchor
    start, phone, use, street = A("outskirts.start"), A("outskirts.phone"), A("outskirts.phone_use"), A("outskirts.street")
    crash, arrive = A("outskirts.crash"), A("outskirts.car_arrive")
    spawn = A("outskirts.angel_spawn")
    walks = [A(f"outskirts.angel_walk_{i}") for i in range(1, 5)]
    A("outskirts.vision")                     # kept as the far mark of the street (the girl stands nearer: GIRL_AHEAD)
    car = ctx.rig("car")
    probe = ctx.probe("outskirts")
    phone_at = (phone["x"], phone["y"], phone["z"])
    girl = (street["x"] + GIRL_AHEAD, street["y"], street["z"])        # (the mark moves with him: she is always GIRL_AHEAD east of where he stands)

    # ---------------------------------------------------------------- the car's way in: out of the smoke, sliding sideways to a stop
    pts, warns = paths.grounded(probe, paths.slide_in_xz(ctx), arrive["y"])
    for w in warns:
        ctx.warn("scene 1 slide-in: " + w)
    SLIDE_T = 2.7
    route = ctx.new_route("slide_in", car)
    route.add_leg("slide", Path(pts), vmax=11.0, a_acc=1.0, a_dec=3.4, v0=11.0, v1=0.0, smooth=0.25, yaw_half=1.0,
                  yaw_fn=lambda t, base: base + 38.0 * max(0.0, 1.0 - t / SLIDE_T) ** 2, yaw_end=(arrive["yaw"], 0.8))
    f0 = route.pose(0)
    end_pose = (arrive["x"], arrive["y"], arrive["z"], arrive["yaw"], 0.0)

    # ---------------------------------------------------------------- setup: wake on the platform
    s.beat(10)
    s.present(misato=0, ritsuko=0, gendo=0, rei=0)
    s.do(blind(4), note="open from black")
    s.move_player(start["x"], start["y"], start["z"], before=worldgen_sky.sky("outskirts"), settle=0.8, note="the player to outskirts.start, noon, clear (head not turned)")
    s.do(f"gamemode adventure {PA()}",
         f"clear {PA()} minecraft:written_book", f"clear {PA()} minecraft:paper",
         f"give {PA()} minecraft:written_book[written_book_content={{title:\"Letter\",author:\"Gendo Ikari\",pages:[{{raw:\"Come.\"}}]}}]",
         f"give {PA()} minecraft:paper[custom_name={{text:\"Photograph\",italic:false}},max_stack_size=1,"
         f"lore=[{{text:\"A woman, smiling. On the back:\",italic:false,color:\"gray\"}},"
         f"{{text:\"If I'm late, ring me from the phone outside the station. M.K.\",italic:true,color:\"gray\"}}]]",
         note="the letter (one word) and the photograph (the note sends him to the phone)")
    # the touch box covers the telephone, the booth's floor and its doorway: a right-click from the pavement outside reaches it too
    s.do(f'summon minecraft:interaction {num(phone["x"])} {num(phone["y"] - 1.0)} {num(phone["z"] + 1.5)} '
         f'{{Tags:["angel.story","angel.ia_phone"],width:3.0f,height:2.4f,response:1b}}', note="the payphone can be touched (from the booth or from just outside it)")
    s.sleep(1.5)
    s.setup_done()

    # ---------------------------------------------------------------- the card, over black, the cicadas starting underneath
    s.card("A.D. 2015", hold=3.2, under=[(0.9, ctx.audio.start("bed", "cicadas+town_empty", fade=3.2))])

    # ---------------------------------------------------------------- the payphone
    # The telephone is on the booth's back wall (z 113); the old trigger stood him 2 blocks from it with the green slab filling his eyes.  Now being
    # anywhere in front of the open booth (up to 2.6 blocks beyond its doorway), at the telephone itself, or touching it is enough.
    ia_phone = "@e[tag=angel.ia_phone,limit=1]"
    s.until([C.near(*PHONE_FRONT, 2.6, est=15), C.near(use["x"], use["y"], use["z"], 1.8, est=15), C.data(ia_phone, "interaction", est=15)],
            hint=("Right-click the phone, or step closer, to pick it up.",
                  [f"particle minecraft:end_rod {num(phone['x'])} {num(phone['y'] + 0.8)} {num(phone['z'] + 1.0)} 0.2 0.8 0.2 0.01 24 force"]),
            hint_after=20, timeout=150, on_timeout=[tp_player(PHONE_FRONT[0], PHONE_FRONT[1], PHONE_FRONT[2])], note="walk to the payphone (to the booth's front is enough)")
    s.do(f"kill {ia_phone}", sfx("sfx.phone_pickup", at=phone_at, vol=1.2), note="he lifts the handset")
    s.sleep(0.9)
    s.say("1.01")
    s.say("1.02")
    s.do(sfx("sfx.phone_hangup", at=phone_at, vol=1.2), note="the hang-up click")
    s.sleep(0.35)
    s.do(*ctx.audio.stop("bed"), note="the cicadas stop (and the town with them): silence")
    s.sleep(0.8)

    # ---------------------------------------------------------------- the street: the girl (in silence), the birds
    s.until(C.near(street["x"], street["y"], street["z"], 3.0, est=14),
            hint=("The street runs east.", [f"particle minecraft:end_rod {num(street['x'])} {num(street['y'] + 1)} {num(street['z'])} 0.2 1.2 0.2 0.01 30 force"]),
            hint_after=45, timeout=150, on_timeout=[tp_player(street["x"], street["y"], street["z"])], note="walk out into the street (no sound at all)")
    birds_spawn, birds_go = ride_air.birds(ctx)
    # the birds sit on the wires; an unseen mark where the girl will stand tells when he is looking that way (within 40 degrees)
    s.do(*birds_spawn, f'summon minecraft:marker {num(girl[0])} {num(girl[1] + 1.2)} {num(girl[2])} {{Tags:["angel.story","angel.look_target","angel.girl_mark"]}}',
         sset("#f.seen", 0), sset("#v.away", 0), note="the birds sit on the wires; a mark where she will stand")
    look40 = s.function("look40", [
        sset("#looking", 0),
        # the mark where she will stand is carried along with him: twelve blocks east of him, in the middle of the road (the street runs east)
        f"execute as {P()} at @s positioned ~{num(GIRL_AHEAD)} {num(girl[1] + 1.2)} {num(girl[2])} run tp @e[tag=angel.girl_mark,limit=1] ~ ~ ~",
        f"execute unless entity @e[tag=angel.gaze,limit=1] at {P()} run summon minecraft:marker ~ ~ ~ {{Tags:[\"angel.gaze\",\"angel.story\"]}}",
        f"execute as {P()} at @s anchored eyes positioned ^ ^ ^1 run tp @e[tag=angel.gaze,limit=1] ~ ~ ~",
        f"execute as {P()} at @s anchored eyes facing entity @e[tag=angel.look_target,limit=1] eyes positioned ^ ^ ^1 "
        f"if entity @e[tag=angel.gaze,distance=..{GIRL_SEEN_WITHIN}] run " + sset("#looking", 1)])
    s.until(Cond(["if score #looking angel.story matches 1"], 3.0, "he looks down the street"), tick=[look40], timeout=45,
            hint=("The street runs east.", [f"particle minecraft:end_rod {num(girl[0])} {num(girl[1] + 1.0)} {num(girl[2])} 0.2 1.2 0.2 0.01 30 force"]),
            hint_after=12, est=3.0, note="he looks down the street (within 40 degrees of where she will stand); after 45 s she comes anyway")
    s.do(f"execute as {P()} at @s positioned ~{num(GIRL_AHEAD)} {num(girl[1])} {num(girl[2])} rotated 90 0 run function {NS}:cast/summon {{id:\"rei_uniform\"}}",
         cast_look("rei_uniform", "player"),
         "kill @e[tag=angel.girl_mark]",
         "tag @e[tag=angel.rei_uniform,tag=angel.char,limit=1] add angel.look_target",
         sset("#f.seen", 0), sset("#v.away", 0),
         note="a girl in a school uniform, 12 blocks down the middle of the road (east of where he stands), perfectly still, facing him")
    vanish = [f"execute at @e[tag=angel.rei_uniform,tag=angel.char,limit=1] run particle minecraft:poof ~ ~1 ~ 0.25 0.6 0.25 0.02 10 force",
              cast_remove("rei_uniform"), "kill @e[tag=angel.look_target]", "kill @e[tag=angel.gaze]", *birds_go]
    s.until(Cond([f"if score #v.away angel.story matches {GIRL_AWAY_TICKS}.."], 3.0, "looked, then looked away for a moment"),
            timeout=GIRL_MAX,
            tick=[look40, "execute if score #looking angel.story matches 1 run scoreboard players set #f.seen angel.story 1",
                  "execute if score #looking angel.story matches 1 run scoreboard players set #v.away angel.story 0",
                  "execute if score #f.seen angel.story matches 1 if score #looking angel.story matches 0 run scoreboard players add #v.away angel.story 1"],
            on_done=vanish, est=4.0,
            note="she is gone when he has looked away for 0.7 s (or six seconds after she appeared): the birds go up at that instant (sfx.birds_up)")
    s.sleep(1.4)

    # ---------------------------------------------------------------- the ground jumps; car alarms far off
    s.do(*jolt_street(ctx, street["y"]), sfx("sfx.car_alarms_far", at=ALARMS_AT, vol=2.0),
         note="the ground jumps: a deep jolt and a giant's step, dust and plaster off the wires and shop fronts all along the street, the parked cars' alarm lamps flashing, a flock off the wires; car alarms")
    s.sleep(1.6)

    # ---------------------------------------------------------------- ANGEL ATTACK: the monster steps out behind the card
    air_start, frames, orbit = ride_air.setup(ctx, spawn, walks, WALK_SPEED, (crash["x"], crash["y"], crash["z"]))
    # ---- tracers that read against a daytime sky: ride_air's were 0.6 x 7 yellow boxes flying 6 blocks a tick (gone in a third of a second); these
    # are 1.3 x 11, orange-white, fly 3.5 blocks a tick (about 0.6 s to the monster) and leave a trail of smoke and sparks
    ctx.extra_functions["story/fx/tr_spawn"] = [
        f'summon minecraft:block_display ~ ~ ~ {{Tags:["{TAG}","angel.trc","angel.trnew"],block_state:"minecraft:orange_concrete",'
        f'brightness:{{sky:15,block:15}},view_range:8.0f,teleport_duration:1,'
        f'{transformation_nbt((-0.65, -0.65, -5.5), (0, 0, 0, 1), (1.3, 1.3, 11.0))}}}',
        f'summon minecraft:block_display ~ ~ ~ {{Tags:["{TAG}","angel.trc","angel.trnew"],block_state:"minecraft:white_concrete",'
        f'brightness:{{sky:15,block:15}},view_range:8.0f,teleport_duration:1,'
        f'{transformation_nbt((-0.3, -0.3, -5.6), (0, 0, 0, 1), (0.6, 0.6, 11.2))}}}',
        "tp @e[tag=angel.trnew] ^ ^-1.2 ^7 ~ ~",
        "tag @e[tag=angel.trnew] remove angel.trnew",
        "particle minecraft:flame ^ ^-1.0 ^6 0.5 0.5 0.5 0.03 12 force",
        "particle minecraft:large_smoke ^ ^-1.0 ^6 0.5 0.5 0.5 0.02 6 force"]
    ctx.extra_functions["story/fx/tr_tick"] = [
        "execute as @e[tag=angel.trc] at @s run tp @s ^ ^ ^3.5",
        "execute as @e[tag=angel.trc] at @s run particle minecraft:large_smoke ~ ~ ~ 0.4 0.4 0.4 0.0 2 force",
        "execute as @e[tag=angel.trc] at @s run particle minecraft:flame ~ ~ ~ 0.25 0.25 0.25 0.01 2 force",
        f"execute as @e[tag=angel.trc] at @s if entity @e[tag=angel.cmark,distance=..{num(ride_air.HIT_RADIUS)}] run function {NS}:story/fx/tr_hit",
        sadd("@e[tag=angel.trc]"),
        f"kill @e[tag=angel.trc,scores={{{OBJ}=70..}}]"]
    # ---- the wreck's smoke column: ride_air's wreck_tick puffs a few white wisps a couple of blocks up; this adds a dark column 40 blocks high that can
    # be seen over the roofs from the street while the wreck burns (the wreck itself, its flames and smoke, run for as long as the flag #fx.wreck is set:
    # it is set at the crash and cleared only on the ridge in scene 2, long after the car has come in)
    wx, wy, wz = crash["x"], crash["y"], crash["z"]
    ctx.extra_functions["story/fx/wreck_column"] = [
        f"particle minecraft:dust{{color:[0.08,0.08,0.09],scale:4.0}} {num(wx)} {num(wy + 22)} {num(wz)} 1.6 18 1.6 0 6 force",
        f"particle minecraft:campfire_signal_smoke {num(wx)} {num(wy + 2)} {num(wz)} 1.0 0.3 1.0 0.01 3 force",
        f"particle minecraft:large_smoke {num(wx)} {num(wy + 6)} {num(wz)} 1.4 3 1.4 0.01 3 force",
        f"particle minecraft:flame {num(wx)} {num(wy + 1.2)} {num(wz)} 2.4 0.5 2.4 0.02 3 force"]
    ctx.fx_tick.append(f"execute if score #fx.wreck {OBJ} matches 1 run function {NS}:story/fx/wreck_column")
    under = [(0.05, [f"execute positioned {num(spawn['x'])} {num(spawn['y'])} {num(spawn['z'])} rotated {num(spawn['yaw'])} 0 run function angel:angel/summon {{height:{MON_H}}}",
                     *air_start])]
    # it walks angel_walk_1..4 at WALK_SPEED blocks per tick: 16 + 16 + 12 + 10 blocks, 18 s (its footfalls are its own: tools/fight, angel:angel/walk)
    t_acc = 0
    prev = (spawn["x"], spawn["z"])
    for i, w in enumerate(walks):
        under.append((max(0.1, t_acc / 20.0), [f"function angel:angel/walk {{x:{num(w['x'])},y:{num(w['y'])},z:{num(w['z'])},speed:{num(WALK_SPEED)}}}"]))
        t_acc += int(round(((w["x"] - prev[0]) ** 2 + (w["z"] - prev[1]) ** 2) ** 0.5 / WALK_SPEED))
        prev = (w["x"], w["z"])
    # two seconds on the card, then a quick return to the same view, which is down the street: the monster is dead ahead at 135 blocks
    s.card("ANGEL ATTACK", hold=2.0, back=2, back_wait=0.2, under=under)

    # ---------------------------------------------------------------- back on the street: the dread, the siren, the aircraft
    # times below are from here (about 2.2 s after the card's hit); the aircraft began 0.05 s after the hit and the hit one crashes in 15 s
    cmark = "execute at @e[tag=angel.cmark,limit=1] run playsound"
    s.after(0.8, *ctx.audio.start("music", "dread"), *ctx.audio.start("loop", "siren", at=SIREN_AT, vol=SIREN_VOL),
            *ctx.audio.start("bed", "town_empty", fade=4.0), note="the picture is back: music.dread, the siren from the old town, the town's air creeping in")
    s.after(1.4, sfx("sfx.jet_pass", at=(128.0, 112.0, 120.0), vol=4.0, pitch=1.0, minvol=0.3), note="a jet goes over the street (from the sky ahead)")
    s.after(2.3, f"{cmark} angel:sfx.gunfire_far master {PA()} ~ ~ ~ 2.5 1.0 0.0", note="aircraft guns, far off")
    s.after(4.3, f"{cmark} angel:sfx.explosion_far master {PA()} ~ ~ ~ 2.0 1.0 0.0", note="a hit on the monster, far off")
    s.after(5.4, sfx("sfx.jet_pass", at=(112.0, 104.0, 138.0), vol=4.0, pitch=0.95, minvol=0.3), note="a jet banks across the sky")
    s.after(6.8, f"{cmark} angel:sfx.gunfire_far master {PA()} ~ ~ ~ 2.5 0.95 0.0", note="more guns")
    s.after(7.8, sfx("sfx.jet_pass", at=(120.0, 120.0, 112.0), vol=4.0, pitch=0.93, minvol=0.3), note="a second jet")
    s.after(8.3, f"{cmark} angel:sfx.explosion_far master {PA()} ~ ~ ~ 2.0 0.9 0.0", note="another hit")
    s.after(11.3, f"{cmark} angel:sfx.gunfire_far master {PA()} ~ ~ ~ 2.5 1.05 0.0", note="guns again, before the crash")
    s.sleep(2.8, note="the aircraft circle and fire")
    s.say("1.03")
    s.until(C.flag("crash", est=5), timeout=40, est=4.0, note="one of the aircraft comes down burning, across the sky to the right of his view (sfx.crash, sfx.explosion_near)")
    s.do(*ctx.audio.stop("music"), note="the dread is cut under the blast")
    s.sleep(1.4)

    # ---------------------------------------------------------------- the blue car
    s.do(*ctx.rig_spawn(car, "closed", f0),
         cast_summon("misato", f0[0], f0[1], f0[2], f0[3]), cast_mount("misato", "driver"), *carfx.look_road(car),
         *route.start_cmds(), sfx("sfx.car_arrive", at=(87.0, 64.0, 135.0), vol=1.5), note="the blue car out of the smoke, with Misato at the wheel (sfx.car_arrive: it stops on the thump at 3.9 s)")
    s.until(route.cond_done(), est=route.seconds(), note="the car slides sideways and stops")
    pose_end = route.pose(route.end)
    s.do(*carfx.door_cmds(car, pose_end, True, 10), sset("#beat", 11), sset("#present_misato", 1), *carfx.look_boy(),
         f"summon minecraft:interaction {num(pose_end[0])} {num(pose_end[1])} {num(pose_end[2])} "
         f'{{Tags:["angel.story","angel.ia_car"],width:6f,height:2.6f,response:1b}}', note="the door opens (the passenger door, on his side: the car's left flank is to the street)")
    s.sleep(0.5)
    s.say("1.04")
    s.say("1.05")

    # ---------------------------------------------------------------- get in
    dx, dy, dz = carfx.door_world(pose_end)
    ia_car = "@e[tag=angel.ia_car,limit=1]"
    board = [f"kill {ia_car}", *carfx.board_player_cmds()]
    s.until([C.near(dx, dy, dz, 2.2, est=6), C.data(ia_car, "interaction", est=6), C.data(ia_car, "attack", est=6)],
            nag=(8.0, 25.0, [fn("say/1_06")]), timeout=70, on_done=board, est=6.0,
            hint=("The blue car is waiting for you.", []), hint_after=30, note="get in (door, or touch the car); Misato nags at 8 s")
    s.sleep(0.6)
    s.do("kill @e[tag=angel.gaze]", "kill @e[tag=angel.look_target]", "kill @e[tag=angel.girl_mark]", note="the look-check marker's use ended with the girl: nothing of it goes on into scene 2")
    s.next_scene(2)
