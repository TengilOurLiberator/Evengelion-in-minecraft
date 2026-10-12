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
from core import NS, OBJ, blind, P, PA, T, angdiff, fn, local_to_world, num, qaxis, sset, QI
from engine import C, Cond
from motion import Path, leg_frames
from models import DOOR_OPEN_DEG, transformation_nbt
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
GLOW_COLOUR = 16744448      # 0xFF7F00, the outline of the Angel in the crater

# Misato after the blast.  The first version put her 2.4 blocks BEHIND the boy's shoulder (178 degrees off the way he is turned: the car): the player
# looked at the car, heard her from behind and could not find her.  Now she stands where the picture shows her as it comes back.
MIS_DIST = (2.3, 2.0, 2.6, 1.8, 2.9)        # blocks from the boy (the checker wants 3 at most)
MIS_ANG = (35, -35, 42, -42, 28, -28, 50, -50)   # degrees off the way he looks (the checker wants 25..55: in view, not on the line to the car)
CAR_BOX = (-3.75, -1.7, -3.55, 3.55)        # the car lying on its right side, in its own frame (x left; xmin, xmax, zmin, zmax): the hull and its open top
PUSH_LOCAL = (-4.75, 1.7)                   # where she stands to push (car frame; the z takes the side she already stands on)
DRIVER_LOCAL = (-2.3, 0.12)                 # where she steps up to the driver's side of the car (the right flank)
WALK_SPEED_MIS = 0.11                       # blocks a tick
# the cloud of the mine thins out over this many seconds from the start of sfx.mine (the blast is at 2.4 s): gone 24 s after it
CLOUD_GONE = 26.6


def smoothstep(u):
    u = min(1.0, max(0.0, u))
    return u * u * (3 - 2 * u)


def to_local(pose, x, z):
    """World (x, z) in the frame of a car at `pose` (x left, z forward)."""
    yaw = math.radians(pose[3])
    dx, dz = x - pose[0], z - pose[2]
    return dx * math.cos(yaw) + dz * math.sin(yaw), -dx * math.sin(yaw) + dz * math.cos(yaw)


def box_gap(pose, x, z):
    lx, lz = to_local(pose, x, z)
    return math.hypot(max(CAR_BOX[0] - lx, 0.0, lx - CAR_BOX[1]), max(CAR_BOX[2] - lz, 0.0, lz - CAR_BOX[3]))


def yaw_to(x0, z0, x1, z1):
    return math.degrees(math.atan2(-(x1 - x0), z1 - z0))


def wrap(a):
    return (a + 180.0) % 360.0 - 180.0


def free_standing(probe, x, z, ref_y, flat=0.5):
    """Ground height at (x, z) if a person can stand there (flat enough, room for a body, no wall within 0.35), else None."""
    y = probe.surface(x, z, ref_y)
    if y is None or abs(y - ref_y) > flat:
        return None
    for dx, dz in ((0, 0), (0.35, 0), (-0.35, 0), (0, 0.35), (0, -0.35)):
        for h in (0.65, 1.2, 1.7):           # (a half-block step beside her is no wall: the cast steps over 1.0)
            if probe.solid(x + dx, y + h, z + dz):
                return None
    return y


def cloud_dissipation(mine, K):
    """[(seconds from the start of sfx.mine, [commands])]: the mushroom cloud (parts angel.cl_*, see fx.mushroom: the cap and skirt have bloomed by 6.5 s)
    hangs, then thins and spreads, greys and darkens, rises and shrinks in stages, and is removed part by part: the fireballs first, the skirt,
    the stem, the caps.  The first version removed nothing: all eight parts stood until the scene was torn down, minutes later."""
    bx, by, bz = mine
    ident = (0, 0, 0, 1)
    rot45 = qaxis("y", 45)
    cube = lambda tag, cy, size, rot, dur: fx._centered_cube_merge(tag, (0, cy * K, 0), 1.0, rot, dur, size=tuple(v * K for v in size))
    look = lambda tag, block, br: (f'data merge entity @e[tag=angel.cl_{tag},limit=1] {{block_state:{{Name:"minecraft:{block}"}},'
                                   f'brightness:{{sky:{br},block:0}}}}')
    smoke = lambda cy, spread, n: (f"particle minecraft:large_smoke {num(bx)} {num(by + cy * K)} {num(bz)} {num(spread * K)} {num(2.0 * K)} {num(spread * K)} 0.02 {n} force")
    st = []
    st.append((11.0, [f"kill @e[tag=angel.cl_fb{i}]" for i in range(4)] + [
        cube("capA", 64, (38, 9, 38), ident, 120), cube("capB", 66, (36, 7, 36), rot45, 120), cube("skirt", 50, (26, 4, 26), ident, 120),
        f"data merge entity @e[tag=angel.cl_stem,limit=1] {{start_interpolation:0,interpolation_duration:120,{transformation_nbt((-2.0 * K, 0, -2.0 * K), ident, (4.0 * K, 40.0 * K, 4.0 * K))}}}",
        look("capA", "light_gray_concrete", 12), look("capB", "gray_concrete", 12), look("skirt", "gray_concrete", 10), look("stem", "gray_concrete", 10),
        smoke(60, 14, 40)]))
    st.append((16.5, [
        "kill @e[tag=angel.cl_skirt]",
        f"data merge entity @e[tag=angel.cl_stem,limit=1] {{start_interpolation:0,interpolation_duration:90,{transformation_nbt((-1.5 * K, 14.0 * K, -1.5 * K), ident, (3.0 * K, 28.0 * K, 3.0 * K))}}}",
        cube("capA", 70, (34, 6, 34), ident, 100), cube("capB", 72, (32, 5, 32), rot45, 100),
        look("capA", "gray_concrete", 9), look("capB", "gray_concrete", 8), look("stem", "gray_concrete", 6),
        smoke(66, 16, 50)]))
    st.append((21.0, [
        "kill @e[tag=angel.cl_stem]",
        cube("capA", 78, (24, 4, 24), ident, 70), cube("capB", 80, (22, 3, 22), rot45, 70),
        look("capA", "gray_concrete", 6), look("capB", "black_concrete", 5),
        smoke(74, 14, 40)]))
    st.append((24.0, [cube("capA", 88, (8, 1.2, 8), ident, 50), cube("capB", 90, (7, 1.0, 7), rot45, 50),
                      look("capA", "black_concrete", 3), look("capB", "black_concrete", 2), smoke(84, 8, 24)]))
    st.append((CLOUD_GONE, ["kill @e[tag=angel.cloud]"]))
    return st


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

    cx_, cz_ = lie_pose[0], lie_pose[2]
    roof = carfx.lie_top(lie_pose)                                               # the open top of the car lying on its right side (the side the boy is on)
    lie_centre = carfx.lie_centre(lie_pose)
    mine = (walk4["x"], walk4["y"], walk4["z"])
    # He is put down on the open-top side of the car, turned to the middle of the car (tp ... facing).  Misato is put where that picture shows her: 2 to 3
    # blocks from him, 25 to 55 degrees off the way he looks (in his forward 120 degrees but not on the line to the car), on level ground with room for a
    # body, clear of the car's hull, and turned to him.  His own spot is the original one (6.3 blocks out, a little before the car's middle) unless
    # the hill leaves her no room there (the car lies 2.4 blocks from it, and the ground falls away to the west): then it slides along the car.
    misato_spot = player_spot = py_ = gaze = None
    for side_blocks, along in ((6.3, -0.8), (6.3, -1.6), (6.3, -2.4), (6.3, -3.0), (6.8, -2.4), (6.8, -3.0), (6.3, -3.6), (6.8, -3.6), (7.3, -3.0)):
        ps = local_to_world((lie_pose[0], lie_pose[1], lie_pose[2]), lie_pose[3], 0.0, -side_blocks, 0.0, along)
        ps = (ps[0], ps[2])
        pg = free_standing(probe, ps[0], ps[1], by)
        if pg is None:
            continue
        gz = yaw_to(ps[0], ps[1], lie_centre[0], lie_centre[2])
        for dist in MIS_DIST:
            for ang in MIS_ANG:
                yw = math.radians(gz + ang)
                mx_, mz_ = ps[0] - dist * math.sin(yw), ps[1] + dist * math.cos(yw)
                if (free_standing(probe, mx_, mz_, pg) is not None and box_gap(lie_pose, mx_, mz_) >= 1.1
                        and dist * abs(math.sin(math.radians(ang))) >= 1.0):
                    misato_spot, player_spot, py_, gaze = (mx_, mz_), ps, pg, gz
                    break
            if misato_spot:
                break
        if misato_spot:
            ctx.warn(f"scene 2: the boy stands {side_blocks} blocks out of the car's side and {along:+.1f} along it")
            break
    if misato_spot is None:
        raise ValueError("scene 2: no standable place for Misato within 3 blocks of the boy in his forward 120 degrees")
    my_ = probe.surface(misato_spot[0], misato_spot[1], by) or by
    face_boy = yaw_to(misato_spot[0], misato_spot[1], player_spot[0], player_spot[1])
    m_off = wrap(yaw_to(player_spot[0], player_spot[1], misato_spot[0], misato_spot[1]) - gaze)
    m_dist = math.hypot(misato_spot[0] - player_spot[0], misato_spot[1] - player_spot[1])
    ctx.warn(f"scene 2: Misato stands at ({misato_spot[0]:.1f}, {my_:.1f}, {misato_spot[1]:.1f}), {m_dist:.1f} blocks from the boy, {m_off:+.0f} degrees off the way "
             f"he looks, {box_gap(lie_pose, *misato_spot):.1f} clear of the car, turned to him (ground {my_:.1f}, his {py_:.1f})")
    # where she stands to push (beside the open top, on the side she is already on), and where she steps up to the driver's side of the upright car
    side = 1.0 if to_local(lie_pose, *misato_spot)[1] >= 0 else -1.0
    push_xy = local_to_world((lie_pose[0], lie_pose[1], lie_pose[2]), lie_pose[3], 0.0, PUSH_LOCAL[0], 0.0, side * PUSH_LOCAL[1])
    push_y = free_standing(probe, push_xy[0], push_xy[2], py_)
    if push_y is None:
        push_xy, push_y = (misato_spot[0], 0.0, misato_spot[1]), my_
        ctx.warn("scene 2: no standable place by the car's open top: she pushes from where she stands")
    face_push = yaw_to(push_xy[0], push_xy[2], lie_centre[0], lie_centre[2])
    drv_xy = local_to_world((lie_pose[0], lie_pose[1], lie_pose[2]), lie_pose[3], 0.0, DRIVER_LOCAL[0], 0.0, DRIVER_LOCAL[1])
    drv_y = free_standing(probe, drv_xy[0], drv_xy[2], py_)
    if drv_y is None:
        raise ValueError("scene 2: no standable place at the driver's side of the car")
    ctx.presence = getattr(ctx, "presence", [])
    ctx.presence.append(dict(scene=2, who="misato", set="outskirts", car=lie_pose, car_box=CAR_BOX,
                             player=(player_spot[0], py_, player_spot[1], gaze),
                             stations=[dict(name="picture back (2.07)", x=misato_spot[0], z=misato_spot[1], y=my_, yaw=face_boy, cone=True, maxd=3.0),
                                       dict(name="at the car (2.09)", x=push_xy[0], z=push_xy[2], y=push_y, yaw=face_push, cone=False, maxd=6.0),
                                       dict(name="driver's side (2.11)", x=drv_xy[0], z=drv_xy[2], y=drv_y, yaw=None, cone=False, maxd=6.0, hull=False)],
                             from_note="tick 50, in the black", to_note="the drive resumes"))

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
    # The aircraft that circle the monster (scene 1; none on a jump) break off one after another, turn away from the ridge, climb and leave over the
    # horizon (ride_air.leave_setup: the orbit and the tracers stop at once, nothing is left hanging), and are gone while 2.05 is still being said.
    # The wreck in the town goes on burning (smoke on the horizon) until the scene is over.
    away_dx, away_dz = walk4["x"] - ridge["x"], walk4["z"] - ridge["z"]
    away_n = math.hypot(away_dx, away_dz)
    away = (walk4["x"] + away_dx / away_n * 900.0, walk4["y"] + MON_H + 220.0, walk4["z"] + away_dz / away_n * 900.0)
    leave = ride_air.leave_setup(ctx, away)
    along = lambda d, h: (walk4["x"] + away_dx / away_n * d, walk4["y"] + MON_H + h, walk4["z"] + away_dz / away_n * d)
    s.do(*leave, sfx("sfx.jet_pass", at=along(0.0, 0.0), vol=4.0, pitch=1.0, minvol=0.3),
         note="the planes pull back: they peel off one after another, turn away and climb out over the horizon (about 3 s); the jets' note recedes")
    s.after(1.3, sfx("sfx.jet_pass", at=along(120.0, 40.0), vol=3.0, pitch=0.9, minvol=0.2), note="the engines, further off")
    s.after(2.6, sfx("sfx.jet_pass", at=along(300.0, 80.0), vol=2.2, pitch=0.82, minvol=0.15), note="and fading")
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
                cast_summon("misato", misato_spot[0], my_, misato_spot[1], face_boy), cast_look("misato", "player"),
                sset("#beat", 21),
                f"function angel:angel/pose {{pose:\"regenerating\"}}",
                f'summon minecraft:interaction {num(lie_centre[0])} {num(by)} {num(lie_centre[2])} '
                f'{{Tags:["angel.story","angel.ia_push"],width:7.6f,height:4.2f,response:1b}}']
    s.do(fn("story/snd/silence"),                                                   # tick 0: every sound stopped ...
         sfx("sfx.mine", vol=4.0),                                                  # ... the mine begins (whine, then 2 s of nothing, then the blast)
         at_eyes + fn("story/s2/whiteout"), *fx.flash_burst(), *spawn_cloud, *cloud_sched,
         *ride_air.stop_cmds(), sset("#fx.leave", 0),                              # (the sky is already empty; this is the belt and braces)
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
    for t_c, cmds_c in cloud_dissipation(mine, MON_H / 60.0):
        s.after(t_c, *cmds_c, note=(f"the mushroom cloud dissipates: stage at {t_c:.1f} s from the start of sfx.mine" if t_c < CLOUD_GONE
                                    else f"{t_c:.1f} s from the start of sfx.mine ({t_c - BLAST / 20.0:.1f} s after the blast): the last of the cloud is gone"))
    ctx.removals = getattr(ctx, "removals", [])
    ctx.removals.append(dict(scene=2, tag="angel.cloud", spawn_note="T0: SILENCE", within=BLAST / 20.0 + 25.0, at_end=True,
                             why="gone 25 s after the blast, long before the telephone call"))
    s.sleep((BLAST + BLACK_HOLD + BLACK_FADE) / 20.0 + 0.3, note="the picture is back (clear at tick 92)")

    # ================================================================ on the ground
    s.say("2.07")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    # 2.08: "Come on. Push when I say.": she walks the couple of blocks to the car's open top, beside where he will stand, and turns to the car
    mis = "@e[type=minecraft:mannequin,tag=angel.misato,limit=1]"
    mis_arrived = Cond(["if score #arrived_misato angel.cast matches 1"], 0.5, "Misato has arrived")
    s.do(cast_look("misato", "ahead"), f'function angel:cast/walk {{id:"misato",x:{num(push_xy[0])},y:{num(push_y)},z:{num(push_xy[2])},speed:{num(WALK_SPEED_MIS)}}}',
         note="2.08: she walks to the car to push")
    s.say("2.08")
    s.until(mis_arrived, timeout=8, on_timeout=['function angel:cast/stop {id:"misato"}'], est=0.5, note="Misato is at the car (the walk has its own time limit)")
    s.do(f"execute as {mis} anchored eyes run rotate @s facing {num(lie_centre[0])} {num(by + 1.6)} {num(lie_centre[2])}", note="she faces the car (eyes level with it), hands ready")
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
    # (the first version removed her and summoned her already in the seat: she was never seen to get in, and a cast mount makes her invisible for 12 ticks)
    s.do(*carfx.door_cmds(car, upright, True, 8), cast_look("misato", "ahead"),
         f'function angel:cast/walk {{id:"misato",x:{num(drv_xy[0])},y:{num(drv_y)},z:{num(drv_xy[2])},speed:{num(WALK_SPEED_MIS)}}}',
         f'summon minecraft:interaction {num(cx_)} {num(by)} {num(cz_)} {{Tags:["angel.story","angel.ia_car"],width:6f,height:2.6f,response:1b}}',
         note="the door opens; Misato walks round to the driver's side")
    s.say("2.11")
    s.until(mis_arrived, timeout=8, on_timeout=['function angel:cast/stop {id:"misato"}'], est=0.5, note="Misato is at the driver's side")
    s.do(f"data merge entity {mis} {{immovable:1b,NoGravity:1b}}", f"ride {mis} mount @e[tag=angel.seat_driver,limit=1]", f"tag {mis} add angel.mounted",
         *carfx.look_road(car), note="she steps up into the driver's seat (a plain ride: the cast's own mount would hide her for 12 ticks)")
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
    s.do(*crater_off, *ctx.audio.stop("music"), sset("#fx.wreck", 0), "kill @e[tag=angel.wreck]", *ride_air.stop_cmds(), sset("#fx.leave", 0),
         "kill @e[tag=angel.cloud]", "kill @e[tag=angel.ia_push]", "kill @e[tag=angel.ia_car]", "kill @e[tag=angel.mwhite]", "kill @e[tag=angel.mblack]",
         note="the car stops at the gate: the music stops, the Angel is left behind; the town's wreck, the last of the cloud and every prop of the scene are removed")
    s.sleep(0.8)
    s.next_scene(3)


def carfx_door_open(car):
    from models import door_motion
    return {"door": door_motion(DOOR_OPEN_DEG)}

