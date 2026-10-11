"""Scene 1, The empty city (outskirts, noon).

The boy wakes on the station platform with the letter and the photograph.  The payphone.  The street, the girl who is not there, the
ground jumps, the monster walks ashore, the aircraft, one comes down burning, the blue car slides out of the smoke.

Beats: 10 until Misato arrives, then 11.
"""
import json

import carfx
import fx
import paths
import worldgen_sky
from context import (actionbar, cast_look, cast_mount, cast_remove, cast_summon, play_at, play_player, ride_passenger, title,
                     tp_player)
from core import blind, P, PA, T, fn, local_to_world, num, sset
from engine import C, Cond
from motion import Path

N = 1
TITLE = "The empty city"


def build(s, ctx):
    A = ctx.anchor
    start, phone, use, street = A("outskirts.start"), A("outskirts.phone"), A("outskirts.phone_use"), A("outskirts.street")
    vision, crash, arrive = A("outskirts.vision"), A("outskirts.crash"), A("outskirts.car_arrive")
    spawn = A("outskirts.angel_spawn")
    walks = [A(f"outskirts.angel_walk_{i}") for i in range(1, 5)]
    car = ctx.rig("car")
    probe = ctx.probe("outskirts")

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
    s.do(tp_player(start["x"], start["y"], start["z"]), *worldgen_sky.sky("outskirts"), note="the player to outskirts.start, noon, clear (head not turned)")
    s.do(f"gamemode adventure {PA()}",
         f"clear {PA()} minecraft:written_book", f"clear {PA()} minecraft:paper",
         f"give {PA()} minecraft:written_book[written_book_content={{title:\"Letter\",author:\"Gendo Ikari\",pages:[{{raw:\"Come.\"}}]}}]",
         f"give {PA()} minecraft:paper[custom_name={{text:\"Photograph\",italic:false}},max_stack_size=1,"
         f"lore=[{{text:\"A woman, smiling. On the back:\",italic:false,color:\"gray\"}},"
         f"{{text:\"I'll come for you at the station. Wait there. M.K.\",italic:true,color:\"gray\"}}]]",
         note="the letter (one word) and the photograph")
    s.do(f'summon minecraft:interaction {num(phone["x"])} {num(phone["y"] - 1.0)} {num(phone["z"])} '
         f'{{Tags:["angel.story","angel.ia_phone"],width:1.4f,height:2.4f,response:1b}}', note="the payphone can be touched")
    s.sleep(1.5)
    s.do(*title("Midsummer. Noon.", None, "white", 20, 70, 30), note="title")
    s.setup_done()

    # ---------------------------------------------------------------- the payphone
    ia_phone = "@e[tag=angel.ia_phone,limit=1]"
    s.until([C.near(use["x"], use["y"], use["z"], 1.8, est=15), C.data(ia_phone, "interaction", est=15)],
            hint=("A payphone, outside the station.", [f"particle minecraft:end_rod {num(phone['x'])} {num(phone['y'] + 1)} {num(phone['z'])} 0.2 1.2 0.2 0.01 30 force"]),
            hint_after=45, timeout=150, on_timeout=[tp_player(use["x"], use["y"], use["z"])], note="walk to the payphone")
    s.do(f"kill {ia_phone}")
    s.say("1.01")
    s.say("1.02")
    s.sleep(0.8)

    # ---------------------------------------------------------------- the street: the girl
    s.until(C.near(street["x"], street["y"], street["z"], 3.0, est=14),
            hint=("The street runs east.", [f"particle minecraft:end_rod {num(street['x'])} {num(street['y'] + 1)} {num(street['z'])} 0.2 1.2 0.2 0.01 30 force"]),
            hint_after=45, timeout=150, on_timeout=[tp_player(street["x"], street["y"], street["z"])], note="walk out into the street")
    birds = fx.birds(ctx)
    s.do(cast_summon("rei_uniform", vision["x"], vision["y"], vision["z"], vision["yaw"]),
         cast_look("rei_uniform", "player"),
         "tag @e[tag=angel.rei_uniform,tag=angel.char,limit=1] add angel.look_target",
         sset("#f.seen", 0), *birds, note="a girl in a school uniform, perfectly still; the birds go up")
    vanish = [f"execute at @e[tag=angel.rei_uniform,tag=angel.char,limit=1] run particle minecraft:poof ~ ~1 ~ 0.25 0.6 0.25 0.02 10 force",
              cast_remove("rei_uniform"), "kill @e[tag=angel.look_target]"]
    s.until(Cond([ "if score #f.seen angel.story matches 1", "if score #looking angel.story matches 0"], 3.0, "looked, then looked away"),
            timeout=6.0, tick=[fn("story/util/looking"), "execute if score #looking angel.story matches 1 run scoreboard players set #f.seen angel.story 1"],
            on_done=vanish, est=4.0, note="she is gone the moment he looks away (or after six seconds)")
    s.sleep(1.4)

    # ---------------------------------------------------------------- the ground jumps; the monster comes ashore
    s.do(*fx.jolt(ctx), note="the ground jumps")
    s.sleep(1.6)
    air_start, rigs, air_tick = fx.aircraft_setup(ctx)
    frames = fx.crash_route(ctx, (crash["x"], crash["y"], crash["z"]))
    fx.crash_functions(ctx, (crash["x"], crash["y"], crash["z"]), frames)
    fx.air_functions(ctx, air_tick)
    s.do(f"execute positioned {num(spawn['x'])} {num(spawn['y'])} {num(spawn['z'])} rotated {num(spawn['yaw'])} 0 run function angel:angel/summon {{height:60}}",
         *air_start, note="something as tall as the hills walks out of the sea; the aircraft are already on it")
    # it walks angel_walk_1..4 at 0.15 blocks per tick: 16 + 16 + 12 + 10 blocks
    t_acc = 0
    prev = (spawn["x"], spawn["z"])
    for i, w in enumerate(walks):
        s.after(max(0.05, t_acc / 20.0), f"function angel:angel/walk {{x:{num(w['x'])},y:{num(w['y'])},z:{num(w['z'])},speed:0.15}}", note=f"walk to angel_walk_{i + 1}")
        t_acc += int(round(((w["x"] - prev[0]) ** 2 + (w["z"] - prev[1]) ** 2) ** 0.5 / 0.15))
        prev = (w["x"], w["z"])
    s.sleep(5.0, note="the aircraft circle and fire")
    s.say("1.03")
    s.until(C.flag("crash", est=5), timeout=40, est=4.0, note="one of the aircraft comes down burning")
    s.sleep(1.4)

    # ---------------------------------------------------------------- the blue car
    s.do(*ctx.rig_spawn(car, "closed", f0),
         cast_summon("misato", f0[0], f0[1], f0[2], f0[3]), cast_mount("misato", "driver"), cast_look("misato", "ahead"),
         *route.start_cmds(), note="the blue car out of the smoke, with Misato at the wheel")
    s.until(route.cond_done(), est=route.seconds(), note="the car slides sideways and stops")
    pose_end = route.pose(route.end)
    s.do(*carfx.door_cmds(car, pose_end, True, 10), sset("#beat", 11), sset("#present_misato", 1), cast_look("misato", "player"),
         f"summon minecraft:interaction {num(pose_end[0])} {num(pose_end[1])} {num(pose_end[2])} "
         f'{{Tags:["angel.story","angel.ia_car"],width:6f,height:2.6f,response:1b}}', note="the door opens")
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
    s.next_scene(2)
