"""Scene 3, The descent.

The car rolls onto a rail wagon in the hillside hall (3.01), a fade, and the wagon, carrying the car, goes down through the Geofront's
tunnel and gallery to the terminal at a steady slow speed.  3.02-3.07 are said in the dark tunnel (three WAITs); the wagon waits in the
tunnel for the player's answers (it stops before geofront.wall_opens rather than reveal the cavern early) and moves on when 3.07 is over,
so that 3.08 ("look out of your window") is said as the car passes wall_opens and 3.09, 3.10 over the open cavern near geofront.reveal.
After 3.10 the ride goes on in quiet to the terminal; both get out; scene 4 follows (it starts in the hq set).

On the wagon the car stands the other way round, so its LEFT side -- the boy's window -- faces the cavern (the gallery has the cavern on
the right of the direction of travel).  Beat 30 for the ride, 31 from wall_opens.
"""
import math

import numpy as np

import carfx
import paths
import worldgen_sky
from context import (cast_look, cast_mount, cast_remove, cast_summon, play_at, ride_passenger, tp_player, title)
from core import blind, P, PA, T, fn, local_to_world, num, sset
from engine import C
from models import Rig, car_parts, cartrain_rig, wagon_parts
from motion import Path

N = 3
TITLE = "The descent"

TUNNEL_STATION_DIST = 54.0        # blocks along the line: the wagon holds here until 3.07 is over (wall_opens is at 58)
START_DIST = 10.0
NOMINAL_AFTER_WALL = 0.4 + 2.62 + 0.4 + 7.16 + 0.4 + 7.29     # seconds from wall_opens to the end of 3.10 (no pauses)
MAX_QUIET = 60.0                  # longer than this after 3.10 and we fade and skip ahead


def build(s, ctx):
    A = ctx.anchor
    gate, cart = A("outskirts.gate"), A("outskirts.cartrain")
    gstart, wall, reveal, term = A("geofront.start"), A("geofront.wall_opens"), A("geofront.reveal"), A("geofront.terminal")
    car = ctx.rig("car")
    probe_o = ctx.probe("outskirts")

    # ---------------------------------------------------------------- the wagon in the hall, and the car's way onto it
    plat = cart["y"]            # the anchors' standing level (the set's own floor in the passage is a block lower; see README, known issues)
    top = plat + 1.0
    wagon_o = ctx.register_rig(Rig("wagon_o", wagon_parts(ramp=True), {}))
    wagon_pose = (cart["x"], top, cart["z"], 180.0, 0.0)
    ctrain_a = ctx.register_rig(cartrain_rig("cartrain_a", reversed_car=False, ramp=True))
    xz = paths.gate_to_cartrain_xz(ctx)
    pts = [(x, gate["y"], z) for x, z in xz]
    warns = []
    rear, ramp_len = cart["z"] + 4.5, 4.0                      # the wagon's rear edge (it faces north) and the foot of its ramp
    fixed = []
    for (x, y, z) in pts:
        if z >= rear + ramp_len:
            fixed.append((x, gate["y"], z))
        elif z > rear:
            fixed.append((x, plat + (rear + ramp_len - z) / ramp_len, z))
        else:
            fixed.append((x, top, z))
    pts = fixed
    for w in warns:
        ctx.warn("scene 3 gate_to_cartrain: " + w)
    route_a = ctx.new_route("gate_to_wagon", car)
    route_a.add_leg("roll", Path(pts), vmax=3.2, a_acc=0.8, a_dec=1.0, a_lat=1.2)
    gate_pose = (gate["x"], gate["y"], gate["z"], gate["yaw"], 0.0)

    # ---------------------------------------------------------------- the ride down the Geofront
    xs, ys, zs, dist, gwarns, g = paths.geofront_line(ctx)
    for w in gwarns[:5]:
        ctx.warn("scene 3 geofront line: " + w)
    i0 = int(np.argmin(np.abs(dist - START_DIST)))
    iS = int(np.argmin(np.abs(dist - TUNNEL_STATION_DIST)))
    it = int(np.argmin((xs - term["x"]) ** 2 + (zs - term["z"]) ** 2))
    iw = int(np.argmin((xs - wall["x"]) ** 2 + (zs - wall["z"]) ** 2))
    ir = int(np.argmin((xs - reveal["x"]) ** 2 + (zs - reveal["z"]) ** 2))
    ptsA = [(xs[i], ys[i], zs[i]) for i in range(i0, iS + 1)]
    ptsB = [(xs[i], ys[i], zs[i]) for i in range(iS, it + 1)]
    ctrain_b = ctx.register_rig(cartrain_rig("cartrain_b", reversed_car=True, ramp=False, bright=(0, 8)))
    ride = ctx.new_route("geofront_ride", ctrain_b)
    ride.add_leg("tunnel", Path(ptsA), vmax=1.15, a_acc=0.35, a_dec=0.4, a_lat=1.0, station="tunnel", smooth=0.8)
    pB = Path(ptsB)
    dB0 = float(dist[iS])
    ride.add_leg("descent", pB, vmax=5.6, a_acc=0.8, a_dec=0.8, a_lat=1.4, smooth=0.8,
                 marks={"wall_opens": float(dist[iw] - dB0), "reveal": float(dist[ir] - dB0)})
    start_pose = ride.pose(0)
    end_pose = ride.pose(ride.end)
    # the ride follows the rail line the anchors were cut from: check that it passes geofront.train_1 .. train_28
    fr = np.array([(f[0], f[1], f[2]) for f in ride.frames])
    worst_xz, worst_y, nk = 0.0, 0.0, 0
    for k in range(1, 29):
        a = A(f"geofront.train_{k}")
        d = np.hypot(fr[:, 0] - a["x"], fr[:, 2] - a["z"])
        j = int(np.argmin(d))
        worst_xz = max(worst_xz, float(d[j]))
        worst_y = max(worst_y, abs(float(fr[j, 1]) - a["y"]))
        nk += 1
    ctx.warn(f"scene 3: the ride passes all {nk} train anchors; worst distance {worst_xz:.2f} blocks, worst height difference {worst_y:.2f} "
             f"(anchors are whole-number heights, the ride follows the deck)")
    rem = (ride.end - (ride.marks["wall_opens"] + T(NOMINAL_AFTER_WALL))) / 20.0
    ctx.warn(f"scene 3: ride is {ride.seconds():.0f}s long; {rem:.0f}s of it remain after 3.10 ends "
             f"({'a fade and skip is added' if rem > MAX_QUIET else 'no skip needed'})")
    out_spot = local_to_world((end_pose[0], end_pose[1], end_pose[2]), end_pose[3], 0.0, -4.2, 0.0, 1.5)
    out_spot2 = local_to_world((end_pose[0], end_pose[1], end_pose[2]), end_pose[3], 0.0, -4.2, 0.0, -0.2)
    probe_g = ctx.probe("geofront")
    oy1 = probe_g.surface(out_spot[0], out_spot[2], end_pose[1]) or end_pose[1] - 1.0
    oy2 = probe_g.surface(out_spot2[0], out_spot2[2], end_pose[1]) or end_pose[1] - 1.0

    # ================================================================ setup (for a jump): the car at the gate, both in it
    sx, sy, sz = carfx.seat_world(gate_pose, "passenger")
    s.do(blind(3.5), note="fade out")
    s.sleep(0.4)
    s.do(*ctx.preload(gate["x"], gate["z"]), tp_player(sx, sy, sz), *worldgen_sky.sky("outskirts"), note="the player to the gate, in the dark")
    s.sleep(0.9)
    s.do(*ctx.rig_spawn(car, "closed", gate_pose),
         cast_summon("misato", gate["x"], gate["y"], gate["z"], gate["yaw"]), cast_mount("misato", "driver"), cast_look("misato", "ahead"), *ride_passenger(),
         sset("#beat", 30), sset("#present_misato", 1), sset("#present_ritsuko", 0), sset("#present_gendo", 0), sset("#present_rei", 0),
         note="the car at the gate")
    s.sleep(1.4)
    s.setup_done()

    # ================================================================ onto the wagon
    s.beat(30)
    s.do(*ctx.rig_spawn(wagon_o, "still", wagon_pose, seats=False), note="the wagon waits in the hall")
    s.do(*route_a.start_cmds(), note="the car rolls onto the flat wagon")
    s.say("3.01")
    s.until(route_a.cond_done(), est=route_a.seconds(), timeout=60, note="the car is on the wagon")
    s.sleep(0.5)
    ca_pose = (cart["x"], top, cart["z"], 180.0, 0.0)
    s.do(sset("#ride", 0), "kill @e[tag=angel.rig_car]", "kill @e[tag=angel.rig_wagon_o]", cast_remove("misato"),
         *ctx.rig_spawn(ctrain_a, "loaded", ca_pose),
         cast_summon("misato", cart["x"], top, cart["z"], 180.0), cast_mount("misato", "driver"), cast_look("misato", "ahead"), *ride_passenger(),
         play_at("minecraft:block.iron_door.close", cart["x"], top + 1, cart["z"] - 8, 2.0, 0.6, 0.4),
         note="the car and the wagon become one rig (same picture, same place)")
    s.sleep(2.0, note="gate closing, the wagon starts")

    # ================================================================ fade, and down
    s.do(blind(4.6), note="to the Geofront")
    s.sleep(0.5)
    s.do(sset("#ride", 0), "kill @e[tag=angel.rig_cartrain_a]", cast_remove("misato"), *ctx.preload(start_pose[0], start_pose[2]),
         tp_player(start_pose[0], start_pose[1], start_pose[2]), *worldgen_sky.sky("geofront"), note="in the dark: to geofront.start")
    s.sleep(1.4, note="the chunks load")
    s.do(*ctx.rig_spawn(ctrain_b, "ride", start_pose),
         cast_summon("misato", start_pose[0], start_pose[1], start_pose[2], start_pose[3] + 180.0), cast_mount("misato", "driver"),
         cast_look("misato", "ahead"), *ride_passenger(), sset("#present_misato", 1), note="the wagon at the mouth of the tunnel")
    s.sleep(1.6)
    s.do(*ride.start_cmds(limit="tunnel"), note="the wagon creeps into the dark")
    s.sleep(1.5)
    s.say("3.02")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    booklet = ("give " + PA() + ' minecraft:written_book[written_book_content={title:"NERV",author:"NERV",pages:'
               '[{raw:"NERV\\nFor Your Eyes Only"},{raw:"There is no test."}]}]')
    s.do(booklet, play_at("minecraft:entity.item.pickup", start_pose[0], start_pose[1], start_pose[2], 0.6, 0.9, 0.0), note="a booklet in his lap")
    s.say("3.03")
    s.say("3.04")
    s.say("3.05")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    s.say("3.06")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    s.say("3.07")
    s.do(*ride.limit_cmds("end"), note="the tunnel wall falls away: the wagon goes on")
    s.until(ride.cond_at("wall_opens"), est=ride.marks["wall_opens"] / 20.0, timeout=60, note="the wagon passes wall_opens")
    s.beat(31)
    s.say("3.08")
    s.say("3.09")
    s.say("3.10")
    if rem > MAX_QUIET:
        skip_to = max(ride.marks["reveal"], ride.end - T(24))
        s.fade(ride.jump_cmds(skip_to), black=1.2, note="skip the long quiet stretch")
    s.until(ride.cond_done(), est=ride.seconds(), timeout=240, note="the ride goes on in quiet, to the terminal")

    # ================================================================ the terminal
    s.sleep(1.2)
    s.do(sset("#ride", 0), f"ride {P()} dismount", cast_remove("misato"),
         tp_player(out_spot[0], oy1, out_spot[2]), cast_summon("misato", out_spot2[0], oy2, out_spot2[2], end_pose[3] + 90.0),
         note="both get out")
    s.sleep(3.0)
    s.next_scene(4, jump=True)
