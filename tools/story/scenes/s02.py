"""Scene 2, The road, staged to cue-sheet.md.

The blue car drives out of town and up the hill road to the ridge (2.01-2.04, a WAIT after 2.02): amb.car_interior, music.road, the siren
(from the old town, positional) falling behind as the distance grows.  On the ridge the engine stops, the music with it, and the wind comes
in (2.05, 2.06).  The mine, timed to sfx.mine (9.000 s: whine 0.0-0.4, DIGITAL SILENCE 0.4-2.4, blast at 2.4, tail to 9.0):

    tick   0   every sound stopped (beds, music, siren, whatever else is sounding), sfx.mine starts, the white-out begins with the whine
    tick   8   the whine has ended
    tick  8-48 TWO FULL SECONDS in which nothing plays: the view is white, thins to veil at tick 20, clears at tick 34 on the silent fireball;
               nothing is scheduled to make a sound in this window (the checker proves it)
    tick  48   the blast lands: black at once (the shock wave's dust at the player), the car goes over
    tick  50   in the dark the car lies on its side, the boy and Misato on their feet beside it, the cloud grows; sfx.car_roll starts
    tick 108   sfx.ears_ringing starts (8 s, under 2.07) as the picture comes back (blindness 4 s from tick 48: clear at tick 128)
    tick 180   the sfx.mine tail ends; the town's air (amb.town_empty) comes back slowly, over 6 s; no music until the drive resumes

Pushing the car is the first thing the boy does with his hands (2.09 counts them in): sfx.car_drop lands with the car on its wheels, then
the doors, sfx.car_start, amb.car_interior back and music.road again as the drive resumes (2.12-2.16, Ritsuko on the telephone).  In the
distance the Angel stands in the crater, glowing (an outline in orange, through the hill if the hill is in the way) and regrowing (pose
`regenerating`, a flame at the crater); the call is paced so that the car limps down to the gate as the call ends.

Beats: 20 on the road, 21 from the blast, 22 once back on the road.
"""
import math

import numpy as np

import carfx
import fx
import launch_shell as sh
import paths
import ride_air
from audio import sfx
from context import (cast_look, cast_mount, cast_remove, cast_summon, play_at, play_player, ride_passenger, tp_player)
from core import NS, OBJ, blind, P, PA, T, angdiff, fn, local_to_world, num, sset, QI
from engine import C, Cond
from motion import Path, leg_frames
from models import DOOR_OPEN_DEG
from objective import objective
from scenes.s01 import MON_H, SIREN_AT, SIREN_VOL

N = 2
TITLE = "The road"

LIE_YAW = 100.0
BLAST = 48                  # ticks from the start of sfx.mine to the blast (2.400 s)
WHITE_VEIL = 1.0            # seconds: the white thins to a veil (still silent); the veil holds until the blast (it is no longer taken away early)
YAW_BLEND = 6.0              # seconds the car takes to swing from the way it lay to the way the road goes
BLACK_HOLD = 24             # ticks of REAL black from the blast: a black room of six opaque slabs round his head (blindness alone leaves the near blocks
                            # visible: the first playthrough saw a bright grey room), moved with him when he is put beside the car
BLACK_FADE = 20             # ticks in which the black comes back: blindness for the last second (clear at tick 48 + 24 + 20 = 92)
MISATO_BACK = 2.4           # blocks further from the car than the boy, and behind him: she is not in his first view of the car on its side
GLOW_COLOUR = 16744448      # 0xFF7F00, the outline of the Angel in the crater


def smoothstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def build(s, ctx):
    A = ctx.anchor
    arrive, ridge, blast, gate = A("outskirts.car_arrive"), A("outskirts.ridge"), A("outskirts.ridge_blast"), A("outskirts.gate")
    walk4 = A("outskirts.angel_walk_4")
    car = ctx.rig("car")
    probe = ctx.probe("outskirts")
    arrive_pose = (arrive["x"], arrive["y"], arrive["z"], arrive["yaw"], 0.0)

    def span(lid, gap=True):
        return (ctx.lines[lid].ticks + (T(0.4) if gap else 0)) / 20.0

    # ---------------------------------------------------------------- route 1: town to the ridge, fast and a little wild
    pts, warns = paths.grounded(probe, paths.to_ridge_xz(ctx), arrive["y"])
    for w in warns:
        ctx.warn("scene 2 to_ridge: " + w)
    to_ridge = ctx.new_route("to_ridge", car)
    # On the ridge she pulls up with the car swung round so that the monster is 42 degrees to the LEFT of the way the car faces: in the passenger's
    # window, inside the forward 100 degrees (the road itself arrives heading ~115 degrees, which would leave it abeam: nearly behind the boy's shoulder).
    ridge_yaw = math.degrees(math.atan2(-(walk4["x"] - ridge["x"]), walk4["z"] - ridge["z"])) + 42.0
    to_ridge.add_leg("drive", Path(pts), vmax=9.0, a_acc=1.3, a_dec=2.0, a_lat=2.0, yaw_end=(ridge_yaw, 3.5))
    ridge_pose = to_ridge.pose(to_ridge.end)

    # ---------------------------------------------------------------- the car on its side at ridge_blast, and route 2: down to the gate
    by = probe.surface(blast["x"], blast["z"], blast["y"])
    lie_pose = (blast["x"], by, blast["z"], LIE_YAW, 0.0)
    pts2, warns2 = paths.grounded(probe, paths.ridge_to_gate_xz(ctx), by)
    for w in warns2:
        ctx.warn("scene 2 ridge_to_gate: " + w)
    base_yaw = Path(pts2).heading(0.0)
    # the car leaves the lying spot pointing LIE_YAW and swings round to the road over six seconds (a smoothstep, so the yaw rate never passes ~35 deg/s)
    limp_kw = dict(a_acc=0.6, a_dec=0.9, a_lat=1.0, smooth=0.6, yaw_fn=lambda t, b: b + angdiff(LIE_YAW, base_yaw) * (1.0 - smoothstep(t / YAW_BLEND)))
    # the call (2.12-2.16) is paced so that the car limps down to the gate as it ends: pick the speed that takes that long
    call_secs = 1.0 + sum(span(f"2.{n}") for n in range(12, 17)) - 0.4
    lo, hi = 1.2, 3.2
    for _ in range(14):
        mid = (lo + hi) / 2.0
        secs = len(leg_frames(Path(pts2), mid, **limp_kw)[0]) / 20.0
        lo, hi = (lo, mid) if secs < call_secs else (mid, hi)
    limp_v = max(2.3, min(3.2, round((lo + hi) / 2.0, 2)))   # never slower than 2.3 blocks/s: the last seconds of the call may be said at the gate
    to_gate = ctx.new_route("to_gate", car)
    to_gate.add_leg("limp", Path(pts2), vmax=limp_v, **limp_kw)
    gate_pose = to_gate.pose(to_gate.end)
    ctx.warn(f"scene 2: the call lasts {call_secs:.1f} s; the car limps down at {limp_v} blocks/s and takes {to_gate.seconds():.1f} s")

    player_spot, misato_spot = carfx.lie_stand_spots(lie_pose, side_blocks=6.3, fwd=(-0.8, 1.6))
    py_ = probe.surface(player_spot[0], player_spot[1], by) or by
    # Misato stands further out and a little behind the boy (when he is turned to the car she is behind his shoulder), where the ground is flat
    # and at the boy's height; if there is no such place she keeps her old spot
    cand = local_to_world((lie_pose[0], lie_pose[1], lie_pose[2]), lie_pose[3], 0.0, -(6.3 + MISATO_BACK), 0.0, -1.2)
    cand_y = probe.surface(cand[0], cand[2], by)
    if cand_y is not None and abs(cand_y - py_) <= 0.6:
        misato_spot = (cand[0], cand[2])
        ctx.warn(f"scene 2: Misato stands behind the boy at ({cand[0]:.1f}, {cand[2]:.1f}), ground {cand_y:.1f} (his {py_:.1f})")
    else:
        ctx.warn(f"scene 2: no flat ground for Misato behind the boy (ground {cand_y}): she keeps her old place beside him")
    my_ = probe.surface(misato_spot[0], misato_spot[1], by) or by
    cx_, cz_ = lie_pose[0], lie_pose[2]
    face_car = math.degrees(math.atan2(-(cx_ - misato_spot[0]), (cz_ - misato_spot[1])))
    roof = carfx.lie_top(lie_pose)                                               # the open top of the car lying on its right side (the side the boy is on)
    lie_centre = carfx.lie_centre(lie_pose)
    mine = (walk4["x"], walk4["y"], walk4["z"])

    # how much of the call the Angel's upper body is in line of sight from the car (it stands 70 to 100 blocks off, behind the ridge's shoulder)
    fr = np.array(to_gate.frames)
    seen = []
    for i in range(0, len(fr), 20):
        eye = fr[i, :3] + np.array([0.0, 1.6, 0.0])
        tgt = np.array([mine[0], mine[1] + 0.8 * MON_H, mine[2]])
        d = tgt - eye
        n = int(np.linalg.norm(d) / 0.5)
        seen.append(all(not probe.solid(*(eye + d * (k / n))) for k in range(1, n)))
    ctx.warn(f"scene 2: the Angel's upper body is in line of sight from the car for {100 * sum(seen) // max(1, len(seen))} % of the call "
             f"(the orange outline shows through the hill for the rest)")

    # ---------------------------------------------------------------- the Angel in the crater: glowing and regrowing, a flame at the crater
    glow_on = f"execute as @e[type=minecraft:block_display,tag=angel.mon] run data merge entity @s {{Glowing:1b,glow_color_override:{GLOW_COLOUR}}}"
    glow_off = "execute as @e[type=minecraft:block_display,tag=angel.mon] run data merge entity @s {Glowing:0b}"
    ctx.extra_functions["story/fx/crater_tick"] = [
        f"particle minecraft:flame {num(mine[0])} {num(mine[1] + 2.0)} {num(mine[2])} 7 2 7 0.02 3 force",
        f"particle minecraft:lava {num(mine[0])} {num(mine[1] + 1.0)} {num(mine[2])} 6 1 6 0.0 1 force",
        f"particle minecraft:campfire_signal_smoke {num(mine[0])} {num(mine[1] + 6.0)} {num(mine[2])} 4 3 4 0.01 1 force"]
    ctx.fx_tick.append(f"execute if score #fx.crater {OBJ} matches 1 run function {NS}:story/fx/crater_tick")
    ctx.fx_flags.add("crater")
    crater_on = [glow_on, sset("#fx.crater", 1)]
    crater_off = [glow_off, sset("#fx.crater", 0)]

    # ================================================================ setup (for a jump; a hand-over from scene 1 skips it)
    sx, sy, sz = carfx.seat_world(arrive_pose, "passenger")
    s.do(blind(3.5), note="fade out")
    s.sleep(0.4)
    s.move_player(sx, sy, sz, settle=0.9, note="the player to the car, in the dark")
    s.do(*ctx.rig_spawn(car, "dooropen", arrive_pose, carfx_door_open(car)),
         cast_summon("misato", arrive["x"], arrive["y"], arrive["z"], arrive["yaw"]), cast_mount("misato", "driver"),
         *ride_passenger(),
         f"execute positioned {num(walk4['x'])} {num(walk4['y'])} {num(walk4['z'])} rotated 90 0 run function angel:angel/summon {{height:{MON_H}}}",
         sset("#beat", 20), sset("#present_misato", 1), sset("#present_ritsuko", 0), sset("#present_gendo", 0), sset("#present_rei", 0),
         note="car, Misato at the wheel, the boy beside her, the monster inland")
    s.do(*ctx.audio.start("loop", "siren", at=SIREN_AT, vol=SIREN_VOL), *ctx.audio.start("bed", "town_empty"),
         note="(a jump only) the siren from the old town and the town's air, as scene 1 leaves them")
    s.sleep(1.4)
    s.setup_done()

    # ================================================================ the drive
    s.beat(20)
    s.do(*carfx.door_cmds(car, arrive_pose, False, 8), *carfx.look_road(car), note="the door shuts (sfx.car_door); she looks at the road")
    s.bed("car_interior", fade=2.0, note="the car's bed replaces the town's (the siren goes on, from behind)")
    s.sleep(0.8)
    s.do(*to_ridge.start_cmds(), *ctx.audio.start("music", "road"), note="she drives fast and badly, out of town and up into the hills; music.road")
    s.sleep(1.2)
    carfx.say_glancing(s, car, "2.01", glance=3.6)
    s.do(*carfx.look_boy(), note="2.02: she asks, looking at him, and goes on looking while he answers")
    s.say("2.02")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    carfx.say_glancing(s, car, "2.03", glance=2.2)
    s.say("2.04")
    s.until(to_ridge.cond_done(), est=to_ridge.seconds(), timeout=120, note="the car reaches the ridge and stops")
    s.do(*ctx.audio.stop("music"), *ctx.audio.start("bed", "town_empty", fade=3.0, out="car_interior", out_fade=1.6),
         note="engine off: the music stops with it, the engine bed ramps down and the wind on the ridge comes in")
    s.sleep(0.8)

    # ================================================================ the ridge: the planes pull back
    # the aircraft that circled the monster in scene 1 (if they still do) climb away to the east; the wreck in the town is let go (it is far behind)
    retreat = []
    for i in range(1, ride_air.N_AC + 1):
        retreat += [f"execute as @e[tag=angel.rig_ac{i},tag=angel.rpart] run data merge entity @s {{teleport_duration:59}}",
                    f"execute as @e[tag=angel.rig_ac{i},tag=angel.pt_fuselage,limit=1] at @s run tp @e[tag=angel.rig_ac{i},tag=angel.rpart] ^ ^28 ^90"]
    s.do(sset("#fx.air", 0), sset("#fx.wreck", 0), "kill @e[tag=angel.wreck]", *retreat, f"schedule function angel:story/s2/f_cleanup_air 140t", note="the planes pull back")
    ctx.fx_scheduled.append("story/s2/f_cleanup_air")
    s.function("cleanup_air", ride_air.stop_cmds())
    # she stops on the ridge and looks back at the monster through field glasses: it stands to the LEFT of the way the car faces, in the boy's window
    s.do(*carfx.look_road(car), f"rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing {num(walk4['x'])} {num(walk4['y'] + 0.55 * MON_H)} {num(walk4['z'])}",
         note="Misato looks back at the monster (it is ahead and to the left: the boy's side)")
    s.say("2.05")
    s.after(2.6, *carfx.look_boy(), note="2.06: 'Down!': she turns to the boy")
    s.say("2.06", gap=0)

    # ---------------------------------------------------------------- THE MINE (everything below is relative to this tick, T0)
    spawn_cloud, cloud_sched = fx.mushroom(ctx, (mine[0], mine[1], mine[2]), scale=MON_H / 60.0)
    ctx.extra_functions["story/s2/whiteout"] = sh.box_shell("angel.mwhite", "white_concrete", None, (4.0, 4.0, 4.0), bright=15)
    ctx.extra_functions["story/s2/blackout"] = sh.box_shell("angel.mblack", "black_concrete", None, (4.0, 4.0, 4.0), bright=0)
    at_eyes = f"execute at {P()} anchored eyes positioned ^ ^ ^ run "
    # put beside the car, in the black, and turned to it (a teleport through black: the one place his head may be turned): the car on its side is
    # what he sees when the picture comes back, Misato is behind his shoulder.  The black room is built again round his eyes where he now is.
    to_spot = f"tp {P()} {num(player_spot[0])} {num(py_)} {num(player_spot[1])} facing {num(lie_centre[0])} {num(py_)} {num(lie_centre[2])}"       # (tp ... facing aims from the FEET: the car's middle at feet level is a level gaze)
    lie_cmds = [sset("#ride", 0), f"ride {P()} dismount", cast_remove("misato"), "kill @e[tag=angel.rig_car]",
                *ctx.rig_spawn(car, "side", lie_pose, carfx.roll_motions(car, 90.0)),
                "kill @e[tag=angel.mblack]", to_spot, at_eyes + fn("story/s2/blackout"),
                cast_summon("misato", misato_spot[0], my_, misato_spot[1], face_car), cast_look("misato", "player"),
                sset("#beat", 21),
                f"function angel:angel/pose {{pose:\"regenerating\"}}",
                f'summon minecraft:interaction {num(lie_centre[0])} {num(by)} {num(lie_centre[2])} '
                f'{{Tags:["angel.story","angel.ia_push"],width:7.6f,height:4.2f,response:1b}}']
    s.do(fn("story/snd/silence"),                                                   # tick 0: every sound stopped ...
         sfx("sfx.mine", vol=4.0),                                                  # ... the mine begins (whine, then 2 s of nothing, then the blast)
         at_eyes + fn("story/s2/whiteout"), *fx.flash_burst(), *spawn_cloud, *cloud_sched,
         note="T0: SILENCE (stopsound everything), sfx.mine, the white-out begins with the whine, the fireball and cloud are built behind it")
    s.quiet(0.4, 2.4, note="sfx.mine: digital silence from 0.4 s to 2.4 s; the checker proves nothing else is scheduled to sound in it")
    s.after(WHITE_VEIL, sh.set_block("angel.mwhite", "white_stained_glass"), note="tick 20: the white thins to a veil (still silent), the fireball dim behind it; it holds")
    s.after(BLAST / 20.0, sh.kill("angel.mwhite"), at_eyes + fn("story/s2/blackout"),
            f"execute at {P()} run particle minecraft:dust_plume ~ ~0.5 ~ 5 1 5 0.03 80 force",
            f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:dirt\"}} ~ ~5 ~ 6 2 6 0.0 60 force",
            note="tick 48: THE BLAST arrives (sfx.mine at 2.400 s): from the white to a REAL black room at once (six opaque black slabs round his head), the shock wave's dust")
    s.after((BLAST + 2) / 20.0, *lie_cmds, sfx("sfx.car_roll", at=(lie_centre[0], by + 1.0, lie_centre[2]), vol=1.5),
            note="tick 50, in the black: the car lies on its side, the boy beside it TURNED TO IT, Misato behind his shoulder; sfx.car_roll (the car goes over twice); the black room moves with him")
    s.after((BLAST + 4) / 20.0, *fx.dust_at(lie_centre[0], by + 0.3, lie_centre[2], 60, 3.0))
    t_back = (BLAST + BLACK_HOLD) / 20.0
    s.after(t_back, sh.kill("angel.mblack"), "effect clear @a minecraft:blindness", blind(BLACK_FADE / 20.0),
            note="tick 72: after a second of black the room goes and the picture comes back over one second (blindness for its last second)")
    # dust in the air as it comes back: three more bursts round the car and round him
    for k, tk in enumerate((BLAST + BLACK_HOLD - 4, BLAST + BLACK_HOLD + 8, BLAST + BLACK_HOLD + 22, BLAST + BLACK_HOLD + 40)):
        s.after(tk / 20.0, *fx.dust_at(lie_centre[0], by + 0.6, lie_centre[2], 70, 3.4),
                f"execute at {P()} run particle minecraft:dust_plume ~ ~1.0 ~ 4 1.5 4 0.02 50 force",
                f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:dirt\"}} ~ ~4 ~ 4 1.5 4 0 30 force",
                note="dust in the air over the car and round him" if k == 0 else "")
    s.after(t_back + 0.5, sfx("sfx.ears_ringing", vol=1.0), note="tick 82: the ringing begins as the picture comes back (8 s, under 2.07)")
    s.after(9.0, *ctx.audio.start("bed", "town_empty", fade=6.0), note="tick 180: the blast's tail has ended: the town's air comes back slowly (6 s); no music")
    s.sleep((BLAST + BLACK_HOLD + BLACK_FADE) / 20.0 + 0.3, note="the picture is back (clear at tick 92)")

    # ================================================================ on the ground
    s.say("2.07")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    s.say("2.08")
    s.say("2.09")
    ia_push = "@e[tag=angel.ia_push,limit=1]"
    cleanup_push = [f"kill {ia_push}"]
    # touching the car, punching it or right-clicking it; Misato says it again after ten seconds
    s.until([C.near(roof[0], by, roof[2], 2.3, est=5), C.data(ia_push, "interaction", est=5), C.data(ia_push, "attack", est=5)],
            nag=(10.0, 14.0, [fn("say/2_09")]), timeout=50, on_done=cleanup_push, est=5.0, hint=("Walk up to the car - you push it by yourself.", []), hint_after=25,
            objective=objective("Help push the car over", at=(lie_centre[0], by + 1.0, lie_centre[2]), line="Walk up to the car - you push it over by yourself", how="walk"),
            note="the boy pushes (touch, punch or right-click); Misato repeats 2.09 after 10 s")
    s.beat(22)
    # the car rolls back onto its wheels, over two seconds, in eight short interpolations; sfx.car_drop lands with it
    keys = carfx.roll_keyframes(car, 90.0, 0.0, 40, 8)
    s.do(*fx.dust_at(cx_, by + 0.3, cz_, 30, 2.2),
         note="the car starts to go over (the strain is left silent: the library has no creak, and a borrowed one would be a vanilla sound; dust shakes off it instead)")
    for delay, cmds in keys:
        s.after(delay / 20.0 + 0.05, *cmds)
    s.after(2.05, sfx("sfx.car_drop", at=(lie_centre[0], by + 1.0, lie_centre[2]), vol=1.5),
            *fx.dust_at(cx_, by + 0.2, cz_, 70, 3.2), "kill @e[tag=angel.new]", note="sfx.car_drop: the car lands on its wheels")
    s.sleep(2.6)
    s.do(*carfx.look_boy(), note="she looks at him as she thanks him")
    s.say("2.10")
    # both get in: Misato first (the door opens), then the boy
    upright = (cx_, by, cz_, LIE_YAW, 0.0)
    s.do(*carfx.door_cmds(car, upright, True, 8), cast_remove("misato"),
         cast_summon("misato", cx_, by, cz_, LIE_YAW), cast_mount("misato", "driver"),
         f'summon minecraft:interaction {num(cx_)} {num(by)} {num(cz_)} {{Tags:["angel.story","angel.ia_car"],width:6f,height:2.6f,response:1b}}',
         note="the door opens; Misato gets in")
    s.say("2.11")
    dx, dy, dz = carfx.door_world(upright)
    ia_car = "@e[tag=angel.ia_car,limit=1]"
    s.until([C.near(dx, dy, dz, 2.2, est=5), C.data(ia_car, "interaction", est=5), C.data(ia_car, "attack", est=5)],
            timeout=20, on_done=[f"kill {ia_car}", *ride_passenger()], est=5.0, hint=("Walk up to the car - you get in by yourself.", []), hint_after=8,
            objective=objective("Get back in", at="@e[tag=angel.seat_passenger,limit=1]", line="Walk up to the car - you get in by yourself", how="walk", grace=2.0),
            note="get back in (walk to the door, or touch the car)")
    s.do(*carfx.door_cmds(car, upright, False, 8), note="the door shuts (sfx.car_door)")
    s.sleep(0.5)
    s.do(sfx("sfx.car_start", vol=1.2), note="sfx.car_start: the starter, the engine catching")
    s.after(2.0, *ctx.audio.start("bed", "car_interior", fade=2.0), note="the engine has caught: the car's bed comes back")
    s.sleep(3.2, note="the engine settles")

    # ================================================================ down to the gate
    s.do(*to_gate.start_cmds(), *ctx.audio.start("music", "road"), note="the drive resumes with the windscreen cracked: music.road again")
    s.sleep(1.0)
    s.do(*crater_on, note="the Angel in the crater: orange outline, flame at the crater (it is regrowing)")
    s.do(*carfx.look_road(car), note="she drives on, the telephone against her shoulder, eyes on the road")
    s.say("2.12")
    s.do(sset("#present_ritsuko", 2), note="Ritsuko, on the telephone")
    s.say("2.13")
    s.say("2.14")
    s.do(sset("#present_ritsuko", 0))
    s.say("2.15")
    carfx.say_glancing(s, car, "2.16", glance=3.0)
    s.until(to_gate.cond_done(), est=to_gate.seconds(), timeout=90, note="the car reaches the gate")
    s.do(*crater_off, *ctx.audio.stop("music"), note="the car stops at the gate: the music stops, the Angel is left behind")
    s.sleep(0.8)
    s.next_scene(3)


def carfx_door_open(car):
    from models import door_motion
    return {"door": door_motion(DOOR_OPEN_DEG)}

