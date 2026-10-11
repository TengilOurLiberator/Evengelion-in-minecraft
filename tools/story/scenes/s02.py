"""Scene 2, The road.

The blue car drives out of town and up the hill road to the ridge (2.01-2.04, a WAIT after 2.02).  On the ridge Misato sees the aircraft
withdraw (2.05, 2.06); the army's mine goes off: a white-out, a delayed deep blast, a mushroom cloud over the monster, which starts to
regrow.  The car ends on its side, the boy and Misato beside it (2.07, WAIT, 2.08, 2.09).  They push (touch, punch or right-click the car);
it rolls back onto its wheels (2.10, 2.11), they get in and drive on down to the gate (2.12-2.16, Ritsuko on the telephone).

Beats: 20 on the road, 21 from the blast, 22 once back on the road.
"""
import math

import carfx
import fx
import paths
from context import (actionbar, cast_look, cast_mount, cast_remove, cast_summon, play_at, play_player, ride_passenger, tp_player)
from core import blind, P, PA, angdiff, fn, local_to_world, num, sset, QI
from engine import C, Cond
from motion import Path
from models import DOOR_OPEN_DEG

N = 2
TITLE = "The road"

LIE_YAW = 100.0


def build(s, ctx):
    A = ctx.anchor
    arrive, ridge, blast, gate = A("outskirts.car_arrive"), A("outskirts.ridge"), A("outskirts.ridge_blast"), A("outskirts.gate")
    walk4 = A("outskirts.angel_walk_4")
    car = ctx.rig("car")
    probe = ctx.probe("outskirts")
    arrive_pose = (arrive["x"], arrive["y"], arrive["z"], arrive["yaw"], 0.0)

    # ---------------------------------------------------------------- route 1: town to the ridge, fast and a little wild
    pts, warns = paths.grounded(probe, paths.to_ridge_xz(ctx), arrive["y"])
    for w in warns:
        ctx.warn("scene 2 to_ridge: " + w)
    to_ridge = ctx.new_route("to_ridge", car)
    to_ridge.add_leg("drive", Path(pts), vmax=9.0, a_acc=1.3, a_dec=2.0, a_lat=2.6)
    ridge_pose = to_ridge.pose(to_ridge.end)

    # ---------------------------------------------------------------- the car on its side at ridge_blast, and route 2: down to the gate
    by = probe.surface(blast["x"], blast["z"], blast["y"])
    lie_pose = (blast["x"], by, blast["z"], LIE_YAW, 0.0)
    pts2, warns2 = paths.grounded(probe, paths.ridge_to_gate_xz(ctx), by)
    for w in warns2:
        ctx.warn("scene 2 ridge_to_gate: " + w)
    to_gate = ctx.new_route("to_gate", car)
    base_yaw = Path(pts2).heading(0.0)
    to_gate.add_leg("limp", Path(pts2), vmax=3.2, a_acc=0.6, a_dec=0.9, a_lat=1.3, smooth=0.6,
                    yaw_fn=lambda t, b: b + angdiff(LIE_YAW, base_yaw) * max(0.0, 1 - t / 3.0) ** 2)
    gate_pose = to_gate.pose(to_gate.end)

    player_spot, misato_spot = carfx.lie_stand_spots(lie_pose, side_blocks=7.0, fwd=(-0.8, 1.6))
    py_ = probe.surface(player_spot[0], player_spot[1], by) or by
    my_ = probe.surface(misato_spot[0], misato_spot[1], by) or by
    cx_, cz_ = lie_pose[0], lie_pose[2]
    face_car = math.degrees(math.atan2(-(cx_ - misato_spot[0]), (cz_ - misato_spot[1])))
    roof = local_to_world((cx_, by, cz_), LIE_YAW, 0.0, -4.3, 0.0, 0.0)          # the roof of the car lying on its right side
    lie_centre = local_to_world((cx_, by, cz_), LIE_YAW, 0.0, -3.0, 0.0, 0.0)
    mine = (walk4["x"], walk4["y"], walk4["z"])

    # ================================================================ setup (for a jump; a hand-over from scene 1 skips it)
    sx, sy, sz = carfx.seat_world(arrive_pose, "passenger")
    s.do(blind(3.5), note="fade out")
    s.sleep(0.4)
    s.do(*ctx.preload(arrive["x"], arrive["z"]), tp_player(sx, sy, sz), note="the player to the car, in the dark")
    s.sleep(0.9)
    s.do(*ctx.rig_spawn(car, "dooropen", arrive_pose, carfx_door_open(car)),
         cast_summon("misato", arrive["x"], arrive["y"], arrive["z"], arrive["yaw"]), cast_mount("misato", "driver"),
         *ride_passenger(),
         f"execute positioned {num(walk4['x'])} {num(walk4['y'])} {num(walk4['z'])} rotated 90 0 run function angel:angel/summon {{height:60}}",
         sset("#beat", 20), sset("#present_misato", 1), sset("#present_ritsuko", 0), sset("#present_gendo", 0), sset("#present_rei", 0),
         note="car, Misato at the wheel, the boy beside her, the monster inland")
    s.sleep(1.4)
    s.setup_done()

    # ================================================================ the drive
    s.beat(20)
    s.do(*carfx.door_cmds(car, arrive_pose, False, 8), cast_look("misato", "ahead"), note="the door shuts")
    s.sleep(0.8)
    s.do(*to_ridge.start_cmds(), note="she drives fast and badly, out of town and up into the hills")
    s.sleep(1.2)
    s.say("2.01")
    s.say("2.02")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    s.say("2.03")
    s.say("2.04")
    s.until(to_ridge.cond_done(), est=to_ridge.seconds(), timeout=120, note="the car reaches the ridge and stops")
    s.sleep(0.8)

    # ================================================================ the ridge: the planes pull back
    # the aircraft that circled the monster in scene 1 (if they still do) climb away to the east
    retreat = []
    for i in range(1, 5):
        retreat += [f"execute as @e[tag=angel.rig_ac{i},tag=angel.part] run data merge entity @s {{teleport_duration:59}}",
                    f"execute as @e[tag=angel.rig_ac{i},tag=angel.pt_fuselage,limit=1] at @s run tp @e[tag=angel.rig_ac{i},tag=angel.part] ^ ^28 ^90"]
    s.do(sset("#fx.air", 0), *retreat, f"schedule function angel:story/s2/f_cleanup_air 140t", note="the planes pull back")
    ctx.fx_scheduled.append("story/s2/f_cleanup_air")
    s.function("cleanup_air", ["kill @e[tag=angel.cmark]"] + [f"kill @e[tag=angel.rig_ac{i}]" for i in range(1, 5)])
    s.say("2.05")

    # ---------------------------------------------------------------- the mine (timeline from the start of 2.06)
    flash = fx.flash_burst()
    for k in range(5):
        s.after(4.0 + 0.15 * k, *flash, note=f"white-out {k}")
    s.after(4.7, blind(5.2), note="then dark, for the swap")
    spawn_cloud, cloud_sched = fx.mushroom(ctx, (mine[0], mine[1], mine[2]))
    lie_cmds = [sset("#ride", 0), f"ride {P()} dismount", cast_remove("misato"), "kill @e[tag=angel.rig_car]",
                *ctx.rig_spawn(car, "side", lie_pose, carfx.roll_motions(car, 90.0)),
                tp_player(player_spot[0], py_, player_spot[1]),
                cast_summon("misato", misato_spot[0], my_, misato_spot[1], face_car), cast_look("misato", "player"),
                sset("#beat", 21),
                f"function angel:angel/pose {{pose:\"regenerating\"}}",
                *spawn_cloud, *cloud_sched,
                f'summon minecraft:interaction {num(lie_centre[0])} {num(by)} {num(lie_centre[2])} '
                f'{{Tags:["angel.story","angel.ia_push"],width:7.4f,height:4.4f,response:1b}}']
    s.after(4.9, *lie_cmds, note="in the dark: the car on its side, the boy and Misato on their feet beside it, the cloud, the monster regrowing")
    s.after(5.1, *fx.dust_at(lie_centre[0], by + 0.3, lie_centre[2], 60, 3.0))
    # the sound arrives well after the light
    s.after(6.9, play_at("minecraft:entity.generic.explode", mine[0], mine[1] + 20, mine[2], 12.0, 0.4, 1.0),
            play_at("minecraft:entity.lightning_bolt.thunder", mine[0], mine[1] + 20, mine[2], 12.0, 0.5, 1.0),
            play_at("minecraft:entity.dragon_fireball.explode", mine[0], mine[1] + 20, mine[2], 12.0, 0.4, 1.0), note="the deep blast, late")
    s.after(7.6, f"execute at {P()} run particle minecraft:dust_plume ~ ~0.5 ~ 5 1 5 0.03 80 force",
            f"execute at {P()} run particle minecraft:falling_dust{{block_state:\"minecraft:dirt\"}} ~ ~5 ~ 6 2 6 0.0 60 force",
            play_at("minecraft:entity.generic.explode", ridge_pose[0], ridge_pose[1] + 3, ridge_pose[2], 6.0, 0.35, 0.8), note="the wave arrives")
    s.say("2.06")
    s.sleep(2.6, note="the white fades, the sound arrives, the dark lifts")

    # ================================================================ on the ground
    s.say("2.07")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    s.say("2.08")
    s.say("2.09")
    ia_push = "@e[tag=angel.ia_push,limit=1]"
    cleanup_push = [f"kill {ia_push}"]
    # touching the car, punching it or right-clicking it; Misato says it again after ten seconds
    s.until([C.near(roof[0], by, roof[2], 2.3, est=5), C.data(ia_push, "interaction", est=5), C.data(ia_push, "attack", est=5)],
            nag=(10.0, 14.0, [fn("say/2_09")]), timeout=50, on_done=cleanup_push, est=5.0, hint=("Push the car.", []), hint_after=25,
            note="the boy pushes (touch, punch or right-click); Misato repeats 2.09 after 10 s")
    s.beat(22)
    # the car rolls back onto its wheels, over two seconds, in eight short interpolations
    keys = carfx.roll_keyframes(car, 90.0, 0.0, 40, 8)
    s.do(play_at("minecraft:block.anvil.land", lie_centre[0], by + 1, lie_centre[2], 1.5, 0.5, 0.5),
         play_at("minecraft:entity.iron_golem.damage", lie_centre[0], by + 1, lie_centre[2], 2.0, 0.6, 0.5), note="the car starts to go over")
    for delay, cmds in keys:
        s.after(delay / 20.0 + 0.05, *cmds)
    s.after(2.2, play_at("minecraft:block.anvil.land", lie_centre[0], by, lie_centre[2], 2.0, 0.7, 0.6),
            *fx.dust_at(cx_, by + 0.2, cz_, 70, 3.2), "kill @e[tag=angel.new]")
    s.sleep(2.6)
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
            timeout=20, on_done=[f"kill {ia_car}", *ride_passenger()], est=5.0, hint=("Get in the car.", []), hint_after=8,
            note="get back in (walk to the door, or touch the car)")
    s.do(*carfx.door_cmds(car, upright, False, 8))
    s.sleep(0.7)

    # ================================================================ down to the gate
    s.do(*to_gate.start_cmds(), note="she drives on with the windscreen cracked")
    s.sleep(1.0)
    s.say("2.12")
    s.do(sset("#present_ritsuko", 2), note="Ritsuko, on the telephone")
    s.say("2.13")
    s.say("2.14")
    s.do(sset("#present_ritsuko", 0))
    s.say("2.15")
    s.say("2.16")
    s.until(to_gate.cond_done(), est=to_gate.seconds(), timeout=90, note="the car reaches the gate")
    s.sleep(0.8)
    s.next_scene(3)


def carfx_door_open(car):
    from models import door_motion
    return {"door": door_motion(DOOR_OPEN_DEG)}
