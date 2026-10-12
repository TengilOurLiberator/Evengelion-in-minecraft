"""Writes tools\\visual\\plans\\gallery2.json: the re-shoot of the gallery for the current anchors, with the new shots.

    python tools\\visual\\make_gallery2.py
    python tools\\visual_test.py --plan gallery2 --with-story --fov 75 --out work\\shots\\gallery2
    python tools\\visual_test.py --plan gallery2 --with-story --fov 75 --render 12 --only <geofront_* names> --out work\\shots\\gallery2\\r12

Differences to make_gallery.py: aerial cameras are inside each set's box and never pitched steeper than 35 degrees (checked here);
the monster in the outskirts is height 100; the cage is shot with its lights off, bank by bank, with the eyes, with Gendo at three
scales, Rei on the gurney from three places, the raised hand from below, the four title cards (the story's own card functions),
the lift lobby in red, and the amber plug and the cockpit of scene 6 (the story's scene 6 jumped to, shot by wall time).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BOX = {"outskirts": ((0, 32, 0), (256, 160, 256)), "city": ((1000, 32, 0), (1320, 192, 320)),
       "geofront": ((2000, 0, 0), (2320, 144, 320)), "hq": ((3000, 0, 0), (3192, 160, 192))}
MAX_PITCH = 35.0

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


def look(frm, to):
    dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
    return math.degrees(math.atan2(-dx, dz)), -math.degrees(math.atan2(dy, math.hypot(dx, dz)))


def aerial(set_name, cam, target):
    """A camera step for an aerial shot; refuses a camera outside the set's box or a pitch steeper than 35 degrees."""
    (x0, y0, z0), (x1, y1, z1) = BOX[set_name]
    assert x0 <= cam[0] <= x1 and y0 <= cam[1] <= y1 and z0 <= cam[2] <= z1, f"aerial camera {cam} is outside the {set_name} box"
    yaw, pitch = look((cam[0], cam[1] + 1.62, cam[2]), target)
    assert pitch <= MAX_PITCH + 0.01, f"aerial camera {cam} -> {target}: pitch {pitch:.1f} is steeper than {MAX_PITCH}"
    return tp(list(cam), yaw=round(yaw, 2), pitch=round(pitch, 2))


CLEAN = {"clean": True}
HUMAN = [{"scale": 1}, "execute as Tester run function angel:fight/become_human"]
GIANT = [{"scale": 16}, "execute as Tester run function angel:fight/become_giant"]
SUMMON = lambda i: 'function angel:cast/summon {id:"%s"}' % i
ANGEL = lambda h: "function angel:angel/summon {height:%d}" % h
POSE = lambda p: 'function angel:angel/pose {pose:"%s"}' % p
FN = lambda f: {"fn": f}

# ------------------------------------------------------------------------------------------------ outskirts, noon
OUT = {"enter": "outskirts"}
shot("outskirts_start", OUT, tp("outskirts.start"), settle=6)
shot("outskirts_phone_use", tp("outskirts.phone_use"))
shot("outskirts_street_east_to_sea", tp("outskirts.street", yaw=-90, pitch=0))
shot("outskirts_street_west_to_station", tp("outskirts.street", yaw=90, pitch=0))
shot("outskirts_vision_girl", at("outskirts.vision", SUMMON("rei_uniform"), yaw=90), {"wait": 1.0},
     tp("outskirts.street", look_at=[133.5, 65.2, 128.5]), settle=3)
shot("outskirts_car_arrive", CLEAN, tp("outskirts.car_arrive"))
shot("outskirts_ridge_toward_angel_spawn", tp("outskirts.ridge", look_at=[228.5, 63, 128.5]))
shot("outskirts_gate", tp("outskirts.gate"), settle=5)
shot("outskirts_cartrain", tp("outskirts.cartrain"))
shot("outskirts_aerial_overview", aerial("outskirts", (8, 118, 128), (150, 36, 128)), settle=8)
shot("outskirts_aerial_bay", aerial("outskirts", (60, 110, 128), (210, 35, 128)), settle=6)
shot("outskirts_monster100_from_street", CLEAN, at("outskirts.angel_spawn", ANGEL(100)), {"wait": 3.0},
     tp("outskirts.street", look_at=[228.5, 120, 128.5]), settle=5)
shot("outskirts_monster100_street_level_low", tp("outskirts.street", look_at=[228.5, 85, 128.5]), settle=3)
shot("outskirts_monster100_from_ridge", tp("outskirts.ridge", look_at=[228.5, 120, 128.5]), settle=3)
shot("outskirts_monster100_aerial", aerial("outskirts", (60, 125, 100), (228.5, 80, 128.5)), settle=4)

# ------------------------------------------------------------------------------------------------ geofront
shot("geofront_start_dark_tunnel", CLEAN, {"enter": "geofront"}, tp("geofront.start"), settle=8)
shot("geofront_wall_opens", tp("geofront.wall_opens"))
shot("geofront_reveal", tp("geofront.reveal"), settle=6)
for n in (8, 16, 24):
    shot(f"geofront_train_{n}", tp(f"geofront.train_{n}"), settle=5)
shot("geofront_terminal", tp("geofront.terminal"))
shot("geofront_hq_entrance_pyramid", tp("geofront.hq_entrance"))
shot("geofront_overview_west_rim", aerial("geofront", (2045, 70, 160), (2235, 25, 160)), settle=8)
shot("geofront_overview_south", aerial("geofront", (2160, 60, 285), (2210, 30, 150)), settle=6)
shot("geofront_pyramid_from_terminal", tp("geofront.terminal", look_at=[2240, 45, 150]), settle=5)
GEOFRONT_NAMES = [s["name"] for s in shots if s["name"].startswith("geofront_")]

# ------------------------------------------------------------------------------------------------ hq
CXB = 3096.5                         # the bridge's centre line
shot("hq_start", {"enter": "hq"}, tp("hq.start"), settle=6)
shot("hq_corr_2", tp("hq.corr_2"))
shot("hq_loop_door", tp("hq.loop_door"))
shot("hq_escalator_hall_from_top", tp("hq.corr_5", look_at=[3050, 112, 160]))
shot("hq_escalator_hall_from_bottom", tp([3030, 107, 160], look_at=[3070, 128, 160]))
shot("hq_elevator", tp("hq.elevator"))
shot("hq_elevator_alert_red", FN("story/hq/strips_red"), {"wait": 0.5}, tp("hq.elevator"), settle=2)
shot("hq_dock", FN("story/hq/strips_on"), tp("hq.dock"), settle=6)
shot("hq_crossing", tp("hq.crossing"))
shot("hq_bridge_start_lights_off", tp("hq.bridge_start"), settle=6)
shot("hq_face_lights_off", tp("hq.face"), settle=5)
shot("hq_face_lights_off_look_up", tp("hq.face", pitch=-35), settle=3)
shot("hq_face_lights_off_look_down_lake", tp("hq.face", pitch=40), settle=3)
shot("hq_face_lights_off_look_back_south", tp("hq.face", yaw=0, pitch=0), settle=3)
shot("hq_bridge_mid_lights_off", tp([CXB, 54, 105], yaw=180, pitch=-5), settle=3)
# each bank of the cage lights, cumulative, from the middle of the bridge looking at the giant
for k in range(8):
    shot(f"hq_bank_{k}_on", FN(f"story/hq/bank_on_{k}"), {"wait": 0.7}, tp([CXB, 54, 105], yaw=180, pitch=-5), settle=2.5, max=10)
shot("hq_face_cage_lights_on_eyes_dark", tp("hq.face"), settle=4)
shot("hq_face_cage_lights_on_look_up", tp("hq.face", pitch=-35), settle=3)
shot("hq_face_cage_lights_on_look_down_lake", tp("hq.face", pitch=35), settle=3)
shot("hq_bridge_start_cage_lit", tp("hq.bridge_start"), settle=4)
shot("hq_face_eyes_lit", FN("story/hq/eyes_on"), {"wait": 1.0}, tp("hq.face"), settle=4)
shot("hq_face_eyes_lit_close", tp([CXB, 54, 75.5], pitch=-30), settle=3)
shot("hq_eyes_off_again", FN("story/hq/eyes_off"), {"wait": 0.7}, tp("hq.face"), settle=3)
# Gendo in the booth, from the "face" anchor: normal size and scaled
BOOTH_EYE = lambda sc: [3110.5, 63 + 1.55 * sc, 57.5]
shot("hq_booth_lit_empty", FN("story/hq/booth_on"), {"wait": 1.0}, tp("hq.face", look_at=[3110.5, 66, 57.5]), settle=4)
for sc, label in ((1.0, "1.0"), (1.6, "1.6"), (2.0, "2.0")):
    steps = [at("hq.booth", SUMMON("gendo"), yaw=43), {"wait": 1.0}]
    if sc != 1.0:
        steps += [at("hq.booth", 'function angel:cast/scale {id:"gendo",scale:%s}' % sc), {"wait": 1.2}]
    shot(f"hq_gendo_scale_{label}_from_face", *steps, tp("hq.face", look_at=BOOTH_EYE(sc)), settle=4)
shot("hq_gendo_scale_1.6_from_face_wide", tp("hq.face", yaw=140, pitch=-14), settle=2)
shot("hq_gendo_scale_1.0_closer", at("hq.booth", SUMMON("gendo"), yaw=43), {"wait": 1.0},
     tp([3103.5, 56, 68.5], look_at=BOOTH_EYE(1.0)), settle=3)
# the hand: lifted out of the coolant (the story's own hand_up) from the bridge, the front, the side, and from below
shot("hq_hand_raised_from_bridge", CLEAN, FN("story/hq/hand_up"), {"wait": 1.5},
     tp([CXB, 54, 94.5], look_at=[3092, 66, 78]), settle=4)
shot("hq_hand_raised_front", tp([CXB, 54, 103.5], look_at=[3094, 62, 80]), settle=3)
shot("hq_hand_raised_side", tp([3112, 62, 82], look_at=[3094, 62, 82]), settle=3)
shot("hq_hand_raised_from_below_close", tp([3092, 40, 100], yaw=180, pitch=-32), settle=3)
shot("hq_hand_raised_from_below_far", tp([3092, 38, 135], yaw=180, pitch=-20), settle=3)
shot("hq_hand_raised_from_below_side", tp([3125, 40, 80], look_at=[3092, 64, 80]), settle=3)
shot("hq_hand_raised_with_eyes_lit", FN("story/hq/eyes_on"), {"wait": 0.7}, tp("hq.face", pitch=-12), settle=3)
shot("hq_hand_down", FN("story/hq/hand_down"), FN("story/hq/eyes_off"), {"wait": 1.5}, tp([CXB, 54, 94.5], look_at=[3092, 50, 78]), settle=3)
# Rei on the gurney: from above, at the player's height from three sides
GM = "hq.gurney_mark"
shot("hq_gurney_rei_medics",
     at(GM, "function angel:cast/gurney {}"), {"wait": 0.5},
     at(GM, SUMMON("rei"), off=[0, 0.82, 0]), {"wait": 0.5},
     at(GM, 'function angel:cast/mount {id:"rei",tag:"angel.seat_gurney"}'), {"wait": 0.5},
     at(GM, 'function angel:cast/pose {id:"rei",pose:"lying"}'), {"wait": 0.5},
     at(GM, "function angel:cast/gurney_crew {}"), {"wait": 2.0},
     tp([CXB, 54, 90.5], look_at=[CXB, 56, 80.5]), settle=4)
shot("hq_rei_from_above", tp([CXB, 62, 80.5], yaw=-90, pitch=86), settle=3)
shot("hq_rei_from_above_wide", tp([CXB, 64, 82.5], yaw=180, pitch=75), settle=3)
shot("hq_rei_player_height_side_north", tp([CXB, 54, 76.5], look_at=[CXB, 55.4, 80.5]), settle=3)
shot("hq_rei_player_height_side_south", tp([CXB, 54, 85.5], look_at=[CXB, 55.4, 80.5]), settle=3)
shot("hq_rei_player_height_head_end", tp([3090.0, 54, 80.5], look_at=[3095.5, 55.4, 80.5]), settle=3)
shot("hq_rei_player_height_foot_end_close", tp([3100.0, 54, 80.5], look_at=[3096.3, 55.4, 80.5]), settle=3)
shot("hq_rei_close_face", tp([3093.2, 54, 79.0], look_at=[3095.4, 55.4, 80.5]), settle=3)
shot("hq_plug_seat", CLEAN, "function angel:cast/gurney_remove", tp("hq.plug_seat"))
shot("hq_pad_look_up_shaft", tp("hq.pad", pitch=-75), settle=6)

# ------------------------------------------------------------------------------------------------ the four title cards (the story's own functions)
card_names = ["ad2015", "angel_attack", "evangelion_unit01", "to_be_continued"]
for i, nm in enumerate(card_names, 1):
    pre = [tp("hq.dock", pause=3)] if i == 1 else []
    shot(f"card_{i}_{nm}", *pre, FN("story/card/bg"), FN(f"story/card/c{i}"), {"wait": 0.8}, settle=1.5, max=6)
    shots[-1]["after"] = [FN("story/card/off")]          # run after the picture (visual_test.py: "after")

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
LINE = ["misato", "ritsuko", "gendo", "rei"]
steps = [CLEAN]
for i, cid in enumerate(LINE):
    steps.append(at([CX - 2.1 + i * 1.4, CY, CZ], SUMMON(cid), yaw=0))
steps += [{"wait": 1.0}, tp([CX, CY, CZ + 5.5], look_at=[CX, CY + 1.0, CZ])]
shot("cast_four_in_a_line", *steps, {"wait": 2.0}, settle=3)

# ------------------------------------------------------------------------------------------------ city, night
shot("city_launch_top_human", CLEAN, {"enter": "city"}, tp("city.launch_top"), settle=8)
shot("city_aerial_overview", aerial("city", (1160, 185, 8), (1160, 60, 190)), settle=8)
shot("city_aerial_plaza", aerial("city", (1010, 150, 260), (1160, 40, 130)), settle=6)
shot("city_launch_top_as_giant", *GIANT, tp("city.launch_top"), settle=6)
shot("city_giant_sees_monster30_from_launch", at("city.angel_start", ANGEL(30)), {"wait": 3.0},
     tp("city.launch_top", look_at=[1160, 80, 50]), settle=5)
shot("city_giant_sees_monster30_halfway", tp([1160, 64, 105], look_at=[1160, 82, 50]), settle=3)
shot("city_giant_sees_monster30_12m", tp([1160, 64, 62], look_at=[1160, 82, 50]), settle=3)
for p in ("charging", "thrust", "regenerating", "dying"):
    st = [at("city.angel_start", POSE(p)), {"wait": 3.5 if p != "dying" else 6.0}]
    shot(f"city_monster30_{p}", *st, tp([1160, 64, 82], look_at=[1160, 80, 50]), settle=2)
shot("city_monster30_core_close", at("city.angel_start", ANGEL(30)), {"wait": 2.5},
     tp([1160, 64, 70], look_at=[1160, 76, 50]), settle=3)
shot("city_human_street_level_monster", *HUMAN, tp([1160, 64, 110], look_at=[1160, 80, 50]), settle=4)

# ------------------------------------------------------------------------------------------------ the plug (scene 6, jumped to; by wall time after the jump)
# times are from the start of `angel:story/scene {n:6}`; the jump itself takes about 7 s of fade and setup
t0 = ("story6_jump",)
shots.append({"name": "plug_seat_sealed_dark", "steps": [CLEAN, {"enter": "hq"}, "function angel:story/scene {n:6}", {"wait": 12.5}], "settle": 0.3, "max": 0})
for nm, w in (("plug_dark_instrument_light", 2.0), ("plug_amber_rising_low", 7.0), ("plug_amber_at_the_eyes", 2.2), ("plug_amber_full", 2.5),
              ("plug_contact_shimmer", 9.5), ("plug_cockpit_in_the_white", 1.2), ("plug_cockpit_view_down_the_bridge", 1.5),
              ("plug_cockpit_view_later", 5.0)):
    shots.append({"name": nm, "steps": [{"wait": w}], "settle": 0.2, "max": 0})
shots.append({"name": "plug_stop", "steps": ["function angel:story/stop", "gamemode spectator Tester"], "nopic": True})

plan = {"name": "gallery2", "fov": 75, "render": 24, "width": 1600, "height": 900,
        "setup": ["gamemode spectator Tester", "execute as Tester run function angel:world/enter_outskirts"],
        "shots": shots, "geofront": GEOFRONT_NAMES}
out = os.path.join(HERE, "plans", "gallery2.json")
json.dump(plan, open(out, "w"), indent=1)
print(len([s for s in shots if not s.get("skip")]), "shots ->", out)
print("geofront:", ",".join(GEOFRONT_NAMES))
