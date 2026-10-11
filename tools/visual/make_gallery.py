"""Writes tools\\visual\\plans\\gallery.json (the first gallery).  Run:  python tools\\visual\\make_gallery.py"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

shots = []


def shot(name, *steps, settle=4, max=25):
    shots.append({"name": name, "steps": list(steps), "settle": settle, "max": max})


def tp(ref, **kw):
    d = {"tp": ref}
    d.update(kw)
    return d


def at(ref, run, **kw):
    d = {"at": ref, "run": run}
    d.update(kw)
    return d


CLEAN = {"clean": True}
HUMAN = [{"scale": 1}, "execute as Tester run function angel:fight/become_human"]
GIANT = [{"scale": 16}, "execute as Tester run function angel:fight/become_giant"]
SUMMON = lambda i: 'function angel:cast/summon {id:"%s"}' % i
ANGEL = lambda h: "function angel:angel/summon {height:%d}" % h
POSE = lambda p: 'function angel:angel/pose {pose:"%s"}' % p

# ------------------------------------------------------------------------------------------------ outskirts, noon
OUT = {"enter": "outskirts"}
shot("outskirts_start", OUT, tp("outskirts.start"), settle=6)
shot("outskirts_phone_use", tp("outskirts.phone_use"))
shot("outskirts_street_east_to_sea", tp("outskirts.street", yaw=-90, pitch=0))
shot("outskirts_street_west_to_station", tp("outskirts.street", yaw=90, pitch=0))
shot("outskirts_car_arrive", tp("outskirts.car_arrive"))
shot("outskirts_ridge_toward_angel_spawn", tp("outskirts.ridge", look_at=[228.5, 63, 128.5]))
shot("outskirts_gate", tp("outskirts.gate"), settle=5)
shot("outskirts_cartrain", tp("outskirts.cartrain"))
shot("outskirts_aerial_overview", tp([8, 118, 128], look_at=[150, 36, 128]), settle=8)
shot("outskirts_aerial_bay", tp([60, 110, 128], look_at=[210, 35, 128]), settle=6)
shot("outskirts_monster60_from_street", CLEAN, at("outskirts.angel_spawn", ANGEL(60)), {"wait": 2.5},
     tp("outskirts.street", look_at=[228.5, 93, 128.5]), settle=5)
shot("outskirts_monster60_from_ridge", tp("outskirts.ridge", look_at=[228.5, 93, 128.5]), settle=3)

# ------------------------------------------------------------------------------------------------ geofront
shot("geofront_start_dark_tunnel", CLEAN, {"enter": "geofront"}, tp("geofront.start"), settle=8)
shot("geofront_wall_opens", tp("geofront.wall_opens"))
shot("geofront_reveal", tp("geofront.reveal"), settle=6)
for n in (8, 16, 24):
    shot(f"geofront_train_{n}", tp(f"geofront.train_{n}"), settle=5)
shot("geofront_terminal", tp("geofront.terminal"))
shot("geofront_hq_entrance_pyramid", tp("geofront.hq_entrance"))
shot("geofront_overview_west_rim", tp([2045, 70, 160], look_at=[2235, 25, 160]), settle=8)
shot("geofront_overview_south", tp([2160, 60, 285], look_at=[2210, 30, 150]), settle=6)
shot("geofront_pyramid_from_terminal", tp("geofront.terminal", look_at=[2240, 45, 150]), settle=5)

# ------------------------------------------------------------------------------------------------ hq
shot("hq_start", {"enter": "hq"}, tp("hq.start"), settle=6)
shot("hq_corr_2", tp("hq.corr_2"))
shot("hq_loop_door", tp("hq.loop_door"))
shot("hq_escalator_hall_from_top", tp("hq.corr_5", look_at=[3050, 112, 160]))
shot("hq_escalator_hall_from_bottom", tp([3030, 107, 160], look_at=[3070, 128, 160]))
shot("hq_elevator", tp("hq.elevator"))
shot("hq_dock", tp("hq.dock"), settle=6)
shot("hq_crossing", tp("hq.crossing"))
shot("hq_bridge_start_lights_off", tp("hq.bridge_start"), settle=6)
shot("hq_face_lights_off", tp("hq.face"), settle=5)
shot("hq_face_cage_lights_on_eyes_dark", {"fn": "visual/cage_lights_on"}, {"wait": 1.5}, tp("hq.face"), settle=5)
shot("hq_face_eyes_lit", {"fn": "visual/eyes_on"}, {"wait": 1.0}, tp("hq.face"), settle=4)
shot("hq_booth_lit_gendo", {"fn": "visual/booth_lights_on"},
     at("hq.booth", SUMMON("gendo")), {"wait": 1.0}, tp("hq.face", look_at=[3115.5, 98, 42.5]), settle=5)
shot("hq_booth_gendo_closer", tp([3110, 96, 68], look_at=[3115.5, 96.8, 42.5]), settle=4)
shot("hq_shield_hand_raised", CLEAN, {"fn": "visual/hand_raised"}, {"wait": 1.0},
     tp([3096.5, 54, 94.5], look_at=[3092, 66, 78]), settle=5)
shot("hq_shield_hand_raised_front", tp([3096.5, 54, 103.5], look_at=[3094, 62, 80]), settle=4)
shot("hq_shield_hand_raised_side", tp([3112, 62, 82], look_at=[3094, 62, 82]), settle=4)
shot("hq_gurney_rei_medics",
     at("hq.gurney_mark", "function angel:cast/gurney {}"), {"wait": 0.5},
     at("hq.gurney_mark", SUMMON("rei"), off=[0, 0.82, 0]), {"wait": 0.5},
     at("hq.gurney_mark", 'function angel:cast/mount {id:"rei",tag:"angel.seat_gurney"}'), {"wait": 0.5},
     at("hq.gurney_mark", 'function angel:cast/pose {id:"rei",pose:"lying"}'), {"wait": 0.5},
     at("hq.gurney_mark", "function angel:cast/gurney_crew {}"), {"wait": 1.5},
     tp([3096.5, 54, 90.5], look_at=[3096.5, 56, 80.5]), settle=5)
shot("hq_rei_lying_close_south", tp([3096.5, 54, 85.5], look_at=[3096.5, 55.4, 80.5]), settle=3)
shot("hq_rei_lying_from_above", tp([3096.5, 60, 84.0], look_at=[3096.5, 55.3, 80.5]), settle=3)
shot("hq_plug_seat", CLEAN, tp("hq.plug_seat"))
shot("hq_pad_look_up_shaft", tp("hq.pad", pitch=-75), settle=6)

# ------------------------------------------------------------------------------------------------ cast, noon, on the street
CAST = ["misato", "ritsuko", "gendo", "rei", "rei_uniform", "medic1", "medic2"]
CX, CY, CZ = 100.5, 64.0, 128.5


def view(d, deg):
    a = math.radians(deg)
    return [round(CX + d * math.sin(a), 3), CY, round(CZ + d * math.cos(a), 3)]


first = True
for cid in CAST:
    pre = [{"enter": "outskirts"}] if first else []
    first = False
    shot(f"cast_{cid}_front_3m", CLEAN, *pre, at([CX, CY, CZ], SUMMON(cid), yaw=0), {"wait": 0.5},
         tp(view(3, 0), look_at=[CX, CY + 1.0, CZ]), {"wait": 2.0}, settle=3)
    shot(f"cast_{cid}_threequarter_6m", at([CX, CY, CZ], f'function angel:cast/look {{id:"{cid}",mode:"ahead"}}'),
         tp(view(6, 38), look_at=[CX, CY + 1.0, CZ]), settle=2)
    if cid in ("misato", "ritsuko", "gendo", "rei", "rei_uniform"):
        shot(f"cast_{cid}_face_closeup", tp(view(1.5, 12), look_at=[CX, CY + 1.55, CZ]), settle=2)
shot("cast_misato_just_removed", at([CX, CY, CZ], SUMMON("misato"), yaw=0), {"wait": 1.0},
     tp(view(3, 0), look_at=[CX, CY + 0.8, CZ]), {"wait": 1.0},
     at([CX, CY, CZ], 'function angel:cast/remove {id:"misato"}'), {"wait": 0.25}, settle=0.05, max=0)
LINE = ["misato", "ritsuko", "gendo", "rei"]
steps = [CLEAN]
for i, cid in enumerate(LINE):
    steps.append(at([CX - 2.1 + i * 1.4, CY, CZ], SUMMON(cid), yaw=0))
steps += [{"wait": 1.0}, tp([CX, CY, CZ + 5.5], look_at=[CX, CY + 1.0, CZ])]
shot("cast_four_in_a_line", *steps, {"wait": 2.0}, settle=3)

# ------------------------------------------------------------------------------------------------ city, night
shot("city_launch_top_human", CLEAN, {"enter": "city"}, tp("city.launch_top"), settle=8)
shot("city_aerial_overview", tp([1160, 210, -40], look_at=[1160, 40, 150]), settle=8)
shot("city_aerial_plaza", tp([1000, 150, 260], look_at=[1160, 40, 130]), settle=6)
shot("city_launch_top_as_giant", *GIANT, tp("city.launch_top"), settle=6)
shot("city_giant_sees_monster30_from_launch", at("city.angel_start", ANGEL(30)), {"wait": 3.0},
     tp("city.launch_top", look_at=[1160, 80, 50]), settle=5)
shot("city_giant_sees_monster30_halfway", tp([1160, 64, 105], look_at=[1160, 82, 50]), settle=3)
shot("city_giant_sees_monster30_12m", tp([1160, 64, 62], look_at=[1160, 82, 50]), settle=3)
for p in ("charging", "thrust", "regenerating", "dying"):
    steps = [at("city.angel_start", POSE(p)), {"wait": 3.5 if p != "dying" else 6.0}]
    shot(f"city_monster30_{p}", *steps, tp([1160, 64, 82], look_at=[1160, 80, 50]), settle=2)
shot("city_monster30_core_close", at("city.angel_start", ANGEL(30)), {"wait": 2.5},
     tp([1160, 64, 70], look_at=[1160, 76, 50]), settle=3)
shot("city_human_street_level_monster", *HUMAN, tp([1160, 64, 110], look_at=[1160, 80, 50]), settle=4)

plan = {"name": "gallery", "fov": 90, "render": 24, "width": 1600, "height": 900,
        "setup": ["gamemode spectator Tester", "execute as Tester run function angel:world/enter_outskirts"],
        "shots": shots}
out = os.path.join(HERE, "plans", "gallery.json")
json.dump(plan, open(out, "w"), indent=1)
print(len(shots), "shots ->", out)

