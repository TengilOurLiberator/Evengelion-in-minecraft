"""Scene 4, Lost (headquarters, white corridors, the lift, the crossing).

Misato leads the boy through the corridors of the Geofront base and is lost (4.01, 4.02); the second time round the loop she stops dead at
the door she has passed already (4.03, WAIT, 4.04), presses a wall panel and has Ritsuko paged (4.05).  They go on down the long escalator.
In the lift lobby the lift arrives with a tone; Ritsuko steps out (4.06-4.10, WAIT, 4.11, beat 41); the first-stage alert dips the lights to
red (klaxon, 4.12); all three ride the lift down through black to the lake hall and cross the catwalk over the red lake, Ritsuko leading and
Misato beside the boy (4.13-4.17); at the cage door, as it opens onto darkness, 4.18.  Scene 5 follows without a break.

Misato never leaves the player behind (lead.py): she waits at each stop until he is within 6 blocks, looks back at him while she waits, and
stops and turns if he lags while she walks.  Beat 40 until the lift lobby, 41 from 4.11.  Ambience: amb.hq in the corridors, amb.lake from the
lower stop.
"""
import math

import lead as L
from context import cast_look, cast_remove, cast_summon, cast_pose, tp_player
from core import PA, P, blind, fn, num, sset
from audio import sfx
from engine import C, Cond
from hq_cage import cage, dirty_cmd
import worldgen_sky

N = 4
TITLE = "Lost"

SPEED = 0.15                 # blocks per tick for the walkers: 3 blocks a second


def build(s, ctx):
    A = ctx.anchor
    start, c1, c2, c3 = A("hq.start"), A("hq.corr_1"), A("hq.corr_2"), A("hq.corr_3")
    loop_door, c4, c5, c6 = A("hq.loop_door"), A("hq.corr_4"), A("hq.corr_5"), A("hq.corr_6")
    elev, elev_in, dock, crossing, cdoor = A("hq.elevator"), A("hq.elevator_in"), A("hq.dock"), A("hq.crossing"), A("hq.cage_door")
    cg = cage(ctx)
    Y_UP, Y_LO, Y_DK = start["y"], elev["y"], dock["y"]
    Z = start["z"]                                # the route's centre line, z = 160.5
    ox = 3000.0

    # --- the ring (loop room, x 95..111, z 152..168 round a solid core x 100..106, z 157..163): lane centres
    EAST, WEST = ox + 109.5, ox + 97.5
    NORTH, SOUTH = 155.5, 165.5

    # ================================================================ setup (a jump runs it; a hand-over from scene 3 comes here too)
    s.do(blind(3.5), note="fade out")
    s.sleep(0.4)
    s.do(*ctx.preload_rect(3000, 128, 3190, 176), note="preload the corridors, the lobby, the lake hall")
    s.sleep(1.2, note="the chunks load")
    s.do(fn("story/hq/reset_cage"), fn("story/hq/reset_lobby"), dirty_cmd(), fn("story/hq/side_closed"), fn("story/hq/lift_closed"),
         note="the set as it should stand: cage dark and shut, the lift's door closed, the hospital door closed")
    s.do(tp_player(start["x"], start["y"], start["z"]), *worldgen_sky.sky("hq"), note="the player to hq.start (the head is not turned)")
    s.do(sset("#beat", 40), sset("#present_misato", 1), sset("#present_ritsuko", 0), sset("#present_gendo", 0), sset("#present_rei", 0),
         cast_summon("misato", start["x"] - 2.0, start["y"], start["z"], 90.0), cast_look("misato", "ahead"),
         cast_summon("ritsuko", elev_in["x"], elev_in["y"], elev_in["z"], -90.0), cast_look("ritsuko", "ahead"),
         note="Misato two paces ahead; Ritsuko waits in the lift behind its closed door")
    s.do(*ctx.audio.start("bed", "hq"), note="the hum of the corridors")
    s.sleep(1.5)
    s.setup_done()

    # ================================================================ the corridors: Misato leads
    L.lead(s, ctx, "misato", [
        L.Stop(c1["x"], Y_UP, c1["z"], say_at=["4.01"], note="corr_1"),
        L.Stop(c2["x"], Y_UP, c2["z"], say_at=["4.02"], note="corr_2 (the walkway)"),
        L.Stop(c3["x"], Y_UP, c3["z"], note="corr_3"),
        # once round the ring: in from the east, up the east lane, west along the north lane (past the door the first time), down the
        # west lane, east along the south lane (corr_4 is its west end), up the east lane again, west to the door
        L.Stop(EAST, Y_UP, Z, wait=False, note="the ring, east lane"),
        L.Stop(EAST, Y_UP, NORTH, wait=False, note="the ring, north-east corner"),
        L.Stop(WEST, Y_UP, NORTH, wait=False, note="the ring, north-west corner (the door D is passed)"),
        L.Stop(c4["x"], Y_UP, c4["z"], note="corr_4"),
        L.Stop(EAST, Y_UP, SOUTH, wait=False, note="the ring, south-east corner"),
        L.Stop(EAST, Y_UP, NORTH, wait=False, note="the ring, north-east corner again"),
    ], speed=SPEED, start=(start["x"] - 2.0, start["z"]))
    # the second time past the door she stops dead in front of it
    L.lead(s, ctx, "misato", [L.Stop(loop_door["x"], Y_UP, loop_door["z"], wait=False, note="hq.loop_door, the second time")],
           speed=SPEED, start=(EAST, NORTH))
    door_pt = (loop_door["x"], Y_UP + 1.6, loop_door["z"] + 3.2)               # the orange hatch, in the wall just south of her
    s.do(*L.face(ctx, "misato", *door_pt), note="she stops dead and looks at the door")
    s.until(L.near_char("misato", 6.0), timeout=120, est=0.5, hint=("Misato has stopped at a door.", []), hint_after=30,
            on_timeout=[tp_player(loop_door["x"] + 2.5, Y_UP, loop_door["z"] - 1.0)], note="the player catches up")
    s.sleep(0.9)
    s.say("4.03")
    s.do(L.face_player("misato"), note="she turns to him")
    s.wait_answer(speaker="misato", prompt="answer Misato")
    s.say("4.04")
    # she presses a wall panel (the north wall of the ring, opposite the door)
    panel = (loop_door["x"], Y_UP + 1.4, 151.9)
    s.do(f'function angel:cast/walk {{id:"misato",x:{num(loop_door["x"])},y:{num(Y_UP)},z:{num(153.0)},speed:0.12}}', note="she steps to the wall")
    s.until(L.arrived("misato", est=2.0), est=2.0, timeout=20, note="at the panel")
    s.do(*L.face(ctx, "misato", *panel))
    s.sleep(1.0)
    s.do("playsound minecraft:block.stone_button.click_on master @a " + f"{num(panel[0])} {num(panel[1])} {num(panel[2])} 2.0 0.9 0.3",
         f"particle minecraft:electric_spark {num(panel[0])} {num(panel[1])} {num(panel[2] + 0.3)} 0.15 0.15 0.15 0.05 10 force",
         note="click")
    s.sleep(0.9)
    s.do(sfx("sfx.pa_chime"), note="the page: a chime")
    s.sleep(1.4)
    s.say("4.05")
    s.sleep(0.6)

    # ================================================================ onward: the escalator, no lines
    L.lead(s, ctx, "misato", [
        L.Stop(WEST, Y_UP, NORTH, wait=False, note="the ring, north-west corner"),
        L.Stop(WEST, Y_UP, Z, wait=False, note="the ring, west lane"),
        L.Stop(ox + 91.5, Y_UP, Z, wait=False, note="the connector"),
        L.Stop(c5["x"], Y_UP, c5["z"], note="corr_5 (the top of the escalator)"),
        L.Stop(ox + 33.5, Y_LO + 0.5, Z, wait=False, note="down the long escalator"),
        L.Stop(c6["x"], Y_LO, c6["z"], note="corr_6 (the bottom)"),
        L.Stop(ox + 13.8, Y_LO, Z - 2.2, note="the lift lobby"),
    ], speed=SPEED, start=(loop_door["x"], 153.0))

    # ================================================================ the lift lobby
    s.until(C.near(elev["x"], Y_LO, elev["z"], 8.5, est=3), timeout=90, est=2.0, note="the player reaches the lobby",
            on_timeout=[tp_player(elev["x"] + 5.0, Y_LO, elev["z"] + 0.0)])
    s.sleep(0.8)
    s.do(sfx("sfx.elevator_arrive", at=(elev_in["x"], Y_LO + 1.5, elev_in["z"]), vol=2.0, minvol=0.6), note="the lift arrives: a tone")
    s.sleep(1.1)
    s.do(fn("story/hq/lift_opened"), sfx("sfx.elevator_doors", at=(elev_in["x"] + 2, Y_LO + 1.5, elev_in["z"]), vol=2.0, minvol=0.6), note="the doors open")
    s.sleep(0.9)
    s.do(sset("#present_ritsuko", 1), f'function angel:cast/walk {{id:"ritsuko",x:{num(elev["x"])},y:{num(Y_LO)},z:{num(elev["z"])},speed:0.13}}',
         note="Ritsuko steps out of the lift")
    s.until(L.arrived("ritsuko", est=3.5), est=3.5, timeout=25, note="Ritsuko reaches hq.elevator")
    s.sleep(0.3)
    # positions as they stand: Ritsuko at hq.elevator, Misato near (13.8, 158.3)
    rit_pt = (elev["x"], Y_LO + 1.6, elev["z"])
    mis_pt = (ox + 13.8, Y_LO + 1.6, Z - 2.2)
    s.do(*L.face(ctx, "ritsuko", *mis_pt), note="Ritsuko turns to Misato")
    s.say("4.06")
    s.do(*L.face(ctx, "misato", *rit_pt), note="Misato to Ritsuko")
    s.say("4.07")
    s.do(L.face_player("ritsuko"), note="Ritsuko turns to the boy")
    s.say("4.08")
    s.do(*L.face(ctx, "misato", *rit_pt))
    s.say("4.09")
    s.say("4.10")
    s.wait_answer(speaker="ritsuko", prompt="answer Ritsuko")
    s.do(L.face_player("misato"), note="Misato to the boy")
    s.say("4.11")
    s.beat(41)

    # ================================================================ the alert
    # the lobby lights dip to a red glow in pulses; the klaxon; 4.12 over it
    s.do(sfx("sfx.klaxon", vol=1.0), fn("story/hq/strips_red"), note="first-stage alert: lights dip to red, klaxon")
    for k, (t_on, t_off) in enumerate([(0.0, 0.8), (1.5, 2.3), (3.0, 3.8)]):
        if t_on > 0:
            s.after(t_on, fn("story/hq/strips_red"), note=f"red pulse {k + 1}")
        s.after(t_off, fn("story/hq/strips_on"), note=f"back {k + 1}")
    s.after(4.3, sfx("sfx.klaxon", vol=0.4), note="the klaxon again, under the voice")
    s.sleep(1.4)
    s.say("4.12")
    s.sleep(0.5)

    # ================================================================ down: all three into the lift
    car_c = (elev_in["x"], Y_LO, elev_in["z"])                     # (3005.5, 107, 160.5)
    s.do(f'function angel:cast/walk {{id:"ritsuko",x:{num(car_c[0] - 1.0)},y:{num(Y_LO)},z:{num(car_c[2] - 1.0)},speed:0.14}}',
         f'function angel:cast/walk {{id:"misato",x:{num(car_c[0] - 1.0)},y:{num(Y_LO)},z:{num(car_c[2] + 1.0)},speed:0.14}}',
         note="Ritsuko and Misato step into the lift")
    s.until([C.near(car_c[0], Y_LO, car_c[2], 1.2, est=6)], timeout=50, est=6.0, hint=("Step into the lift (all the way in: the doors close).", []), hint_after=14,
            on_timeout=[tp_player(car_c[0], Y_LO, car_c[2])], note="the player steps into the lift")
    s.until(Cond(["if score #arrived_ritsuko angel.cast matches 1", "if score #arrived_misato angel.cast matches 1"], 2.0, "both in the car"),
            timeout=15, est=1.0, note="both are in")
    east = (car_c[0] + 8.0, Y_LO + 1.6, car_c[2])
    s.do(*L.face(ctx, "ritsuko", *east), *L.face(ctx, "misato", *east), note="they turn to face the doors")
    s.sleep(0.7)
    s.do(fn("story/hq/lift_closed"), sfx("sfx.elevator_doors", at=(car_c[0] + 1.5, Y_LO + 1.5, car_c[2]), vol=2.0, minvol=0.6), note="the doors close")
    s.sleep(1.4)
    # the ride: through black.  The motor is a vanilla stand-in (a low hum and a thump) until a recorded one exists.
    s.do(blind(7), *ctx.audio.stop("bed"), sfx("minecraft:block.beacon.ambient", vol=0.9, pitch=0.5), note="the lift goes down: to black")
    s.sleep(0.6)
    s.do(cast_remove("ritsuko"), cast_remove("misato"), tp_player(car_c[0], Y_DK, car_c[2]),
         cast_summon("ritsuko", car_c[0] - 1.0, Y_DK, car_c[2] - 1.0, -90.0), cast_summon("misato", car_c[0] - 1.0, Y_DK, car_c[2] + 1.0, -90.0),
         cast_look("ritsuko", "ahead"), cast_look("misato", "ahead"), note="in the dark: the lower stop")
    s.after(2.6, sfx("minecraft:block.beacon.ambient", vol=0.9, pitch=0.5), note="the hum goes on")
    s.after(4.2, sfx("minecraft:block.piston.contract", vol=1.0, pitch=0.5), note="the lift slows")
    s.after(4.9, sfx("sfx.elevator_arrive", vol=1.0), *ctx.audio.start("bed", "lake"), note="a tone; the lake hall's air")
    s.sleep(5.6, note="the dark lifts")
    s.do(sfx("sfx.elevator_doors", vol=0.8), L.face_player("ritsuko"), note="the doors are open on the dock")
    s.sleep(0.8)

    # ================================================================ the crossing: Ritsuko leads, Misato beside the boy
    xl = ox + 96.5
    L.lead(s, ctx, "ritsuko", [
        L.Stop(dock["x"], Y_DK, dock["z"], note="hq.dock"),
        L.Stop(crossing["x"], Y_DK, crossing["z"], say_while=["4.13", "4.14"], note="hq.crossing"),
        L.Stop(xl, Y_DK, Z, wait=False, say_while=["4.15", "4.16"], note="the corner of the catwalk"),
        L.Stop(xl, Y_DK, cdoor["z"] + 5.0, wait=False, say_while=["4.17"], note="up to the cage door"),
        L.Stop(xl, Y_DK, cdoor["z"] - 1.8, note="in front of the cage door"),
    ], speed=SPEED, companion=("misato", 2.6, 1.3), start=(car_c[0] - 1.0, car_c[2] - 1.0))
    s.do(L.face_player("misato"), note="Misato arrives and looks at him")
    s.sleep(0.6)
    # 4.18 at hq.cage_door, as the door opens onto darkness
    s.do(fn("story/hq/door_open"), sfx("sfx.door_heavy", at=(xl, Y_DK + 2.5, 140.5), vol=3.0, minvol=0.7), note="the cage door opens onto darkness")
    s.sleep(1.2)
    s.say("4.18")
    s.sleep(0.5)
    s.next_scene(5)
