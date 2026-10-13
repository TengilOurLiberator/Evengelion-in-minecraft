"""Scene 3, The descent, staged to cue-sheet.md.

The car rolls onto a rail wagon in the hillside hall (3.01) while the blast gate behind it closes (two striped leaves slide out of the wall:
daylight narrows to a line and is gone, sfx.gate_close, 5.35 s to the final boom), a fade with sfx.train_start in the dark, and the wagon,
carrying the car, goes down through the Geofront's tunnel (amb.tunnel) and gallery to the terminal at a steady slow speed.  3.02-3.07 are
said in the dark tunnel (three WAITs); the wagon waits at rest in the tunnel for the player's answers and goes on after 3.07.

The descent music.  music.descent blooms at exactly 8.000 s (tick 160).  The bloom must land on geofront.reveal (the point where the cavern
is fully revealed), so the music is started a fixed number of ticks before the wagon gets there, and that depends only on where the wagon
starts from: it always departs from REST at the holding point (frame S), the route table is played one frame per tick, and the reveal is
frame V, so the wagon needs V - S ticks from the tick it is let go.  The music therefore starts LEAD = 160 - (V - S) ticks before the
wagon is let go (the held breath is the wait: 2.9 s of music out of silence with the wagon at rest), and the same tick pair is used whether
the wagon has been held for a minute for the answers or 3.07 ended before it had even reached the holding point (the scene then waits for
it to arrive and be at rest first).  geofront.wall_opens (frame 892) comes 65 ticks after the wagon is let go; 3.08 begins there with
sfx.air_open and the tunnel bed dropping away to amb.geofront, and the reveal (bloom) comes 37 ticks later, during "Look out of your window".
Measured live (scratch server, logged game ticks): a scheduled function runs before that tick's tick functions, so the route counter moves on the
release tick itself and the reveal comes V - S - 1 ticks after the release; hence LEAD = 160 - (V - S) + 1 (SCHED_BEFORE_MOVER).

On the wagon the car stands the other way round, so its LEFT side -- the boy's window -- faces the cavern (the gallery has the cavern on
the right of the direction of travel).  Beat 30 for the ride, 31 from wall_opens.
"""
import math

import numpy as np

import carfx
import paths
import worldgen_sky
from audio import sfx
from context import (cast_look, cast_mount, cast_remove, cast_summon, play_at, ride_passenger, tp_player, title)
from core import blind, P, PA, T, fn, fnum, local_to_world, num, sset, TAG
from engine import C
from models import Rig, car_parts, cartrain_rig, wagon_parts
from motion import Path

N = 3
TITLE = "The descent"

TUNNEL_STATION_DIST = 54.0        # blocks along the line: the wagon holds here until 3.07 is over (wall_opens is at 58)
START_DIST = 10.0
NOMINAL_AFTER_WALL = 0.4 + 2.62 + 0.4 + 7.16 + 0.4 + 7.29     # seconds from wall_opens to the end of 3.10 (no pauses)
MAX_QUIET = 60.0                  # longer than this after 3.10 and we fade and skip ahead
BLOOM_TICKS = 160                 # music.descent: the bloom is at exactly 8.000 s
GATE_TRIGGER = 3.6                # seconds after the car starts to roll in that the gate begins to close (the car's tail is clear of the doorway by 6.8 s)
GATE_SEGMENTS = (17, 15, 15, 15, 15, 15, 15)    # sfx.gate_close: the slide is heard from 0.7 s and the boom is at 5.35 s: start at tick 17, six moves of 15, the last ends at tick 107
SCHED_BEFORE_MOVER = 1            # measured live: a scheduled function runs BEFORE that tick's story/mover (the counter moves on the release tick itself), so the reveal comes one tick sooner
STOP_LEAD = 130                   # ticks before the end of the ride that sfx.train_stop (6.5 s) begins


def smoothstep(u):
    return u * u * (3 - 2 * u)


def gate_leaves(ctx, probe, gate):
    """Two hazard-striped leaves hidden inside the portal wall, either side of the opening, and the functions that close them.
    The opening is read from the built set (free cells through the wall at the gate's x); the leaves are display entities one wall-thickness
    inside the wall (solid blocks hide them) so that the set itself is untouched.  Returns (spawn commands, [(tick, commands)], info)."""
    gx, gy = gate["x"], gate["y"]
    zc = None
    # the wall: the two rows of solid blocks beside the opening, found where the opening's side walls meet the sky
    xs_free = [x for x in range(int(gx) - 30, int(gx) + 31) if not probe.solid(x + 0.5, gy + 3.5, 21.5)]
    lo = hi = int(gx)
    while (lo - 1) in xs_free:
        lo -= 1
    while (hi + 1) in xs_free:
        hi += 1
    x_lo, x_hi = float(lo), float(hi + 1)
    top = gy
    while not probe.solid(gx, top + 0.5, 21.5) and top < gy + 30:
        top += 1
    height = float(top) - gy
    z0, depth = 21.6, 0.8
    cx = (x_lo + x_hi) / 2.0
    width = (x_hi - x_lo) / 2.0
    info = dict(x_lo=x_lo, x_hi=x_hi, height=height, width=width, centre=cx)

    def part(tag, block, u0, y0, w, h, dz=0.0, dd=0.0, bright=12, extra=""):
        return (f'summon minecraft:block_display {num(ox[tag])} {num(gy)} {num(z0)} {{Tags:["{TAG}","angel.gate","angel.gate_{tag}"{extra}],block_state:"minecraft:{block}",'
                f'brightness:{{sky:0,block:{bright}}},view_range:2.0f,teleport_duration:15,'
                f'transformation:{{translation:[{fnum(u0)},{fnum(y0)},{fnum(-dd)}],left_rotation:[0f,0f,0f,1f],'
                f'scale:[{fnum(w)},{fnum(h)},{fnum(depth + 2 * dd)}],right_rotation:[0f,0f,0f,1f]}}}}')

    open_off = width + 0.5
    ox = {"w": x_lo - open_off, "e": cx + open_off}              # the entity origins when open (hidden in the wall)
    closed = {"w": x_lo, "e": cx}                                 # ... and closed
    cmds = []
    for tag, flip in (("w", 1), ("e", -1)):
        # u runs from the wall side (0) to the leading edge (width); for the west leaf the wall side is the low x
        def uu(a, w, flip=flip):
            return a if flip == 1 else width - a - w
        cmds.append(part(tag, "yellow_concrete", 0.0, 0.0, width, height))
        for a in (0.55, 2.4, 4.25, 6.1):
            if a + 0.9 <= width:
                cmds.append(part(tag, "black_concrete", uu(a, 0.9), 0.0, 0.9, height, dd=0.01))
        cmds.append(part(tag, "iron_block", 0.0, 0.0, width, 0.4, dd=0.02))
        cmds.append(part(tag, "iron_block", 0.0, height - 0.4, width, 0.4, dd=0.02))
        cmds.append(part(tag, "iron_block", uu(width - 0.4, 0.4), 0.0, 0.4, height, dd=0.02))
        # two amber hazard lamps on the hall face of each leaf (a boy looking back over his shoulder sees them flash as the daylight narrows)
        for yy in (height - 1.3, height * 0.45):
            cmds.append(part(tag, "orange_concrete", uu(width - 1.2, 0.5), yy, 0.5, 0.5, dd=0.2, bright=15, extra=',"angel.gate_lamp"'))
    # the moves: the first begins at tick GATE_SEGMENTS[0], each later one 15 ticks after the previous (= the entities' teleport_duration, so the
    # glide is continuous); move k takes the leaves to smoothstep(k / n) of the way, the last one to the closed position at end_tick
    n = len(GATE_SEGMENTS) - 1
    sched = []
    t = GATE_SEGMENTS[0]
    for k in range(1, n + 1):
        u = smoothstep(k / float(n))
        moves = [f"execute as @e[tag=angel.gate_{tg}] run tp @s {num(ox[tg] + (closed[tg] - ox[tg]) * u)} {num(gy)} {num(z0)}" for tg in ("w", "e")]
        # sparks off the leading edges (the leaves are heavy and scrape their tracks), and a little dust shaken off the lintel
        edge_w = ox["w"] + (closed["w"] - ox["w"]) * u + width
        edge_e = ox["e"] + (closed["e"] - ox["e"]) * u
        for ex in (edge_w, edge_e):
            moves.append(f"particle minecraft:electric_spark {num(ex)} {num(gy + 1.0)} {num(z0 - 0.4)} 0.15 1.0 0.3 0.5 14 force")
            moves.append(f"particle minecraft:dust_plume {num(ex)} {num(gy + height - 0.5)} {num(z0 - 0.8)} 0.6 0.3 0.6 0.01 4 force")
        sched.append((t, moves))
        t += GATE_SEGMENTS[min(k, len(GATE_SEGMENTS) - 1)]
    info["end_tick"] = t
    return cmds, sched, info


def build(s, ctx):
    import pace
    PC = pace.PACE
    # the pacing's numbers shadow the module's (pace.py: s3_*)
    GATE_TRIGGER = PC.s3_gate_trigger
    START_DIST = PC.s3_start_dist
    MAX_QUIET = PC.s3_max_quiet
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
    route_a.add_leg("roll", Path(pts), **PC.s3_roll)
    # the car climbs the ramp onto the wagon's deck, one block above the passage floor: the checker is told (sim.check_routes reads deck_lift)
    route_a.deck_lift = [max(0.0, float(f[1]) - gate["y"]) for f in route_a.frames]
    gate_pose = (gate["x"], gate["y"], gate["z"], gate["yaw"], 0.0)
    leaf_cmds, leaf_sched, leaf_info = gate_leaves(ctx, probe_o, gate)
    # the car's tail must be clear of the doorway before the leaves reach its lane
    fa = np.array(route_a.frames)
    clear_frame = int(np.argmax(fa[:, 2] <= 21.0 - 3.6))
    ctx.warn(f"scene 3: the gate (opening x {leaf_info['x_lo']:g}..{leaf_info['x_hi']:g}, {leaf_info['height']:g} high) begins to close {GATE_TRIGGER} s after the car "
             f"starts to roll and shuts {GATE_TRIGGER + leaf_info['end_tick'] / 20.0:.2f} s after it; the car's tail clears the doorway at {clear_frame / 20.0:.1f} s")

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
    ctrain_b = ctx.register_rig(cartrain_rig("cartrain_b", reversed_car=True, ramp=False, bright=(0, 8), low_side="R"))
    ride = ctx.new_route("geofront_ride", ctrain_b)
    ride.add_leg("tunnel", Path(ptsA), a_lat=1.0, station="tunnel", smooth=0.8, **PC.s3_tunnel)
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

    # the descent music: the wagon always leaves the holding point from rest, V - S frames (= ticks) before the reveal
    S_f, V_f = ride.stations["tunnel"], ride.marks["reveal"]
    W_f = ride.marks["wall_opens"]
    LEAD = BLOOM_TICKS - (V_f - S_f) + SCHED_BEFORE_MOVER
    ctx.warn(f"scene 3: holding point = frame {S_f}, wall_opens = frame {W_f} ({W_f - S_f} ticks after release), reveal = frame {V_f} ({V_f - S_f} ticks after release): "
             f"music.descent starts {LEAD} ticks ({LEAD / 20.0:.2f} s) BEFORE the wagon is let go, so its bloom (tick {BLOOM_TICKS}) lands on the reveal"
             if LEAD >= 1 else f"scene 3: reveal is {V_f - S_f} ticks after release: music.descent starts {-LEAD} ticks AFTER the wagon is let go")
    ctx.descent = dict(station=S_f, wall=W_f, reveal=V_f, lead=LEAD, end=ride.end, bloom=BLOOM_TICKS, offset=SCHED_BEFORE_MOVER)

    # ================================================================ setup (for a jump): the car at the gate, both in it
    sx, sy, sz = carfx.seat_world(gate_pose, "passenger")
    s.do(blind(3.5), note="fade out")
    s.sleep(0.4)
    s.move_player(sx, sy, sz, before=worldgen_sky.sky("outskirts"), settle=0.9, note="the player to the gate, in the dark")
    s.do(*ctx.rig_spawn(car, "closed", gate_pose),
         cast_summon("misato", gate["x"], gate["y"], gate["z"], gate["yaw"]), cast_mount("misato", "driver"), *car.ahead_cmds(), *ride_passenger(),
         sset("#beat", 30), sset("#present_misato", 1), sset("#present_ritsuko", 0), sset("#present_gendo", 0), sset("#present_rei", 0),
         *ctx.audio.start("bed", "car_interior"),
         note="the car at the gate (a jump: the engine's bed as scene 2 leaves it)")
    s.sleep(1.4)
    s.setup_done()

    # ================================================================ onto the wagon; the gate shuts behind the car
    s.beat(30)
    s.do(*ctx.rig_spawn(wagon_o, "still", wagon_pose, seats=False), *leaf_cmds, note="the wagon waits in the hall; the two gate leaves wait inside the wall")
    s.do(*route_a.start_cmds(), note="the car rolls onto the flat wagon")
    s.after(GATE_TRIGGER, sfx("sfx.gate_close", at=(leaf_info["centre"], gate["y"] + 4.0, 22.0), vol=2.0),
            note="the gate begins to close: sfx.gate_close (motor, then the slide from 0.7 s, the boom at 5.35 s)")
    for tick, moves in leaf_sched:
        s.after(GATE_TRIGGER + tick / 20.0, *moves, note=f"gate leaves slide in (tick {tick})" if tick == leaf_sched[0][0] else "")
    # the hazard lamps flash from the moment the leaves start to move until they have shut (a flip every 0.35 s)
    lamp_on = "execute as @e[tag=angel.gate_lamp] run data merge entity @s {brightness:{sky:15,block:15}}"
    lamp_off = "execute as @e[tag=angel.gate_lamp] run data merge entity @s {brightness:{sky:0,block:2}}"
    for k in range(int((GATE_TRIGGER + leaf_info["end_tick"] / 20.0 + 0.8) / 0.35)):
        s.after(0.2 + 0.35 * k, lamp_off if k % 2 else lamp_on, note="gate lamp" if k == 0 else "")
    s.say("3.01")
    s.until(route_a.cond_done(), est=route_a.seconds(), timeout=60, note="the car is on the wagon")
    s.bed_out("car_interior", 1.5, note="the engine is switched off")
    s.sleep(0.5)
    ca_pose = (cart["x"], top, cart["z"], 180.0, 0.0)
    s.do(sset("#ride", 0), "kill @e[tag=angel.rig_car]", "kill @e[tag=angel.rig_wagon_o]", cast_remove("misato"),
         *ctx.rig_spawn(ctrain_a, "loaded", ca_pose),
         cast_summon("misato", cart["x"], top, cart["z"], 180.0), cast_mount("misato", "driver"), *ctrain_a.ahead_cmds(), *ride_passenger(),
         note="the car and the wagon become one rig (same picture, same place)")
    # the gate has shut by GATE_TRIGGER + 5.35 s after the roll began; the bolts run to 6.3 s: let them finish before the fade
    s.sleep(max(0.4, GATE_TRIGGER + PC.s3_gate_tail - route_a.seconds() - 0.5), note="the gate's boom and bolts finish")

    # ================================================================ fade, and down
    s.do(blind(PC.s3_fade), sfx("sfx.train_start", vol=1.0), note="to the Geofront: sfx.train_start (6.5 s) in the dark")
    s.sleep(PC.s3_fade_pause)
    s.do(sset("#ride", 0), "kill @e[tag=angel.rig_cartrain_a]", "kill @e[tag=angel.gate]", cast_remove("misato"), note="the car train and the gate are taken away")
    s.move_player(start_pose[0], start_pose[1], start_pose[2], before=worldgen_sky.sky("geofront"), settle=PC.s3_settle, note="in the dark: to geofront.start")
    s.sleep(PC.s3_settle2, note="the chunks settle")
    s.do(*ctx.rig_spawn(ctrain_b, "ride", start_pose),
         cast_summon("misato", start_pose[0], start_pose[1], start_pose[2], start_pose[3] + 180.0), cast_mount("misato", "driver"),
         *ctrain_b.ahead_cmds(), *ride_passenger(), sset("#present_misato", 1), note="the wagon at the mouth of the tunnel (the car turned about: the boy's window faces the cavern)")
    s.sleep(PC.s3_ride_pause)
    s.do(*ride.start_cmds(limit="tunnel"), *ctx.audio.start("bed", "tunnel", fade=3.0),
         note="the wagon creeps into the dark; amb.tunnel comes in under the end of sfx.train_start")
    s.sleep(PC.s3_ride_pause2)
    s.do(*carfx.look_boy(), note="3.02: she asks, looking at him")
    s.say("3.02")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    booklet = ("give " + PA() + ' minecraft:written_book[written_book_content={title:"NERV",author:"NERV",pages:'
               '[{raw:"NERV\\nFor Your Eyes Only"},{raw:"There is no test."}]}]')
    s.do(booklet, note="a booklet in his lap (left silent: the library has no paper event and a vanilla pickup would be a stand-in)")
    carfx.say_glancing(s, ctrain_b, "3.03", glance=2.6)
    s.say("3.04")
    s.do(*carfx.look_boy(), note="3.05: she asks, looking at him")
    s.say("3.05")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    s.say("3.06")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    carfx.say_glancing(s, ctrain_b, "3.07", glance=3.0)

    # ---------------------------------------------------------------- let the wagon go, with the music exactly 8.000 s before the reveal
    s.until(ride.cond_at("tunnel"), est=ride.stations["tunnel"] / 20.0, timeout=150,
            note="the wagon is at rest at the holding point (3.07 may end before it has crept this far: the scene waits for it)")
    if LEAD >= 1:
        s.do(*ctx.audio.start("music", "descent"), note=f"music.descent starts NOW, with the wagon at rest: its bloom is {BLOOM_TICKS} ticks later")
        s.after(LEAD / 20.0, *ride.limit_cmds("end"), note=f"{LEAD} ticks later the wagon is let go: it reaches geofront.reveal {V_f - S_f} ticks after that")
    else:
        s.do(*ride.limit_cmds("end"), note="the wagon is let go")
        s.after(-LEAD / 20.0, *ctx.audio.start("music", "descent"), note=f"music.descent starts {-LEAD} ticks after the wagon moves")
    s.until(ride.cond_at("wall_opens"), est=ride.marks["wall_opens"] / 20.0, timeout=60, note="the wagon passes wall_opens")
    s.beat(31)
    s.do(sfx("sfx.air_open", vol=1.0), *ctx.audio.start("bed", "geofront", fade=2.5, out="tunnel", out_fade=1.2),
         note="the wall falls away: sfx.air_open, the tunnel bed drops away into amb.geofront")
    s.do(*carfx.look_boy(), note="3.08: she looks at him, past him to the window: the open air is on his side")
    s.say("3.08")
    s.say("3.09")
    s.say("3.10")
    if rem > MAX_QUIET:
        if PC.s3_look:
            s.sleep(PC.s3_look, note="a moment to look at the cavern")
        skip_to = max(ride.marks["reveal"], ride.end - T(PC.s3_skip_keep))
        s.fade(ride.jump_cmds(skip_to), black=PC.s3_skip_black, note="skip the long quiet stretch")
    s.until(ride.cond_at(max(0, ride.end - STOP_LEAD)), est=(ride.end - STOP_LEAD) / 20.0, timeout=240, note="the ride goes on in quiet: the brakes begin")
    s.do(sfx("sfx.train_stop", vol=1.0), note="sfx.train_stop (6.5 s): brakes, the clacks slowing, the final shunt as it stops")
    s.until(ride.cond_done(), est=ride.seconds(), timeout=240, note="the wagon stops at the terminal")

    # ================================================================ the terminal
    s.sleep(PC.s3_end_pause)
    s.do(sset("#ride", 0), cast_remove("misato"), note="both get out")
    s.move_player(out_spot[0], oy1, out_spot[2], r=2.5, settle=0.2, note="the boy steps onto the platform")
    s.do(cast_summon("misato", out_spot2[0], oy2, out_spot2[2], end_pose[3] + 90.0), note="Misato beside him")
    s.sleep(PC.s3_end_pause2)
    s.next_scene(4, jump=True)

