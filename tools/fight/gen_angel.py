"""Generates the monster's functions (namespace angel, folder angel/).

Design in short:
  * every part of the monster is a block_display standing at ONE point (the foot position of the monster); the part's
    offset is baked into its transformation, so turning/moving the whole monster is just teleporting the parts to a
    marker (angel.root) that carries position and yaw;
  * a pose is a function per (pose, height) that sets the transformation of every part (with interpolation);
  * heights are generated for the set HEIGHTS; `summon {height:N}` snaps N to the nearest of them.
"""
import math
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402

HEIGHTS = (20, 30, 40, 50, 60, 80, 100, 150)
SNAP = []        # (upper bound inclusive, height): geometric midpoints
for a, b in zip(HEIGHTS, HEIGHTS[1:]):
    SNAP.append((int(math.floor(math.sqrt(a * b))), a))
SNAP.append((10 ** 6, HEIGHTS[-1]))

POSE_FILES = ["idle_a", "idle_b"] + [f"regen_{i}" for i in range(8)] + ["charge", "charge_2", "charge_3", "windup", "thrust", "stagger", "wrap_open",
              "wrap_close", "die_1", "die_2", "die_3", "walk_l", "walk_r"]

BRIGHT = model.BRIGHT
BLOCK_TAGS = {"eye": "angel.eye", "core": "angel.corebody", "halo": "angel.corebody", "jaw": "angel.jaw",
              "coreglow": "angel.coreglow", "veil": "angel.veil", "eyeglow": "angel.eyeglow", "gather": "angel.gather"}

CORE_BOX = 0.15          # core hit box edge as a fraction of the height
BODY_W, BODY_H = 0.24, 0.56
CORE_FWD = 8.0           # the core hit box sits this many model units in front of the core centre


def f(x):
    s = f"{x:.3f}".rstrip("0").rstrip(".")
    if s in ("-0", ""):
        s = "0"
    return s + "f"


def vec(v):
    return "[" + ",".join(f(x) for x in v) + "]"


def quat(R):
    """Rotation matrix -> [x, y, z, w]."""
    m = R
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        w = 0.25 * s
        x = (m[2, 1] - m[1, 2]) / s
        y = (m[0, 2] - m[2, 0]) / s
        z = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        w = (m[2, 1] - m[1, 2]) / s
        x = 0.25 * s
        y = (m[0, 1] + m[1, 0]) / s
        z = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        w = (m[0, 2] - m[2, 0]) / s
        x = (m[0, 1] + m[1, 0]) / s
        y = 0.25 * s
        z = (m[1, 2] + m[2, 1]) / s
    else:
        s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
        w = (m[1, 0] - m[0, 1]) / s
        x = (m[0, 2] + m[2, 0]) / s
        y = (m[1, 2] + m[2, 1]) / s
        z = 0.25 * s
    q = np.array([x, y, z, w])
    q /= np.linalg.norm(q)
    if q[3] < 0:
        q = -q
    return q


def transform_nbt(e, k, full=False):
    size = 2 * e["half"] * k
    R = e["R"]
    t = e["centre"] * k - R @ (size / 2)
    q = quat(R)
    body = f"translation:{vec(t)},left_rotation:{vec(q)},scale:{vec(size)}"
    if full:
        body += ",right_rotation:[0f,0f,0f,1f]"
    return "{" + body + "}"


def part_tags(i, p):
    tags = ["angel.mon", "angel.part", f"angel.p{i}"]
    if p["tag"] in BLOCK_TAGS:
        tags.append(BLOCK_TAGS[p["tag"]])
    return tags


def snbt_list(xs):
    return "[" + ",".join(f'"{x}"' for x in xs) + "]"


def walk_stride(k):
    """Blocks the body moves per step, from the two walking key poses (planted foot goes from front to back)."""
    a = {e["name"]: e for e in model.pose_boxes(model.poses()["walk_l"])}
    b = {e["name"]: e for e in model.pose_boxes(model.poses()["walk_r"])}
    dz = a["footL"]["centre"][2] - b["footL"]["centre"][2]
    return abs(dz) * k


def foot_offsets(k):
    """(lateral, forward, in blocks) of the forward foot in walk_l and in walk_r."""
    a = {e["name"]: e for e in model.pose_boxes(model.poses()["walk_l"])}
    b = {e["name"]: e for e in model.pose_boxes(model.poses()["walk_r"])}
    fl = a["footL"]["centre"]
    fr = b["footR"]["centre"]
    return (fl[0] * k, fl[2] * k), (fr[0] * k, fr[2] * k)


def pose_hit_offsets(pose, k):
    """Offsets (left, up, forward) in blocks of the two interaction boxes' feet (their bottom centre) for a pose."""
    bs = model.pose_boxes(pose)
    core = [e for e in bs if e["name"] == "coreA"][0]["centre"]
    ch = CORE_BOX * k * 100
    c = (core[0] * k, core[1] * k - ch / 2, (core[2] + CORE_FWD) * k)
    bh = BODY_H * k * 100
    body = (0.0, 0.66 * k * 100 - bh / 2, 0.0)
    return c, body


def gen(F, add_block_tag=None):
    """F: dict path -> list of lines. Paths are relative to function/angel/."""
    model.build()
    P = model.PARTS
    poses = model.poses()
    LB = {}

    def put(path, lines):
        F.setdefault(path, []).extend(lines if isinstance(lines, list) else lines.split("\n"))

    # ------------------------------------------------------------ per height: summon and pose functions
    for H in HEIGHTS:
        k = H / 100.0
        bs0 = model.pose_boxes(poses["idle_a"])
        lines = [f"# The Angel at height {H}: root and helper markers, hit boxes, {len(P)} display parts, at the executor.",
                 'summon minecraft:marker ~ ~ ~ {Tags:["angel.mon","angel.root","angel.new"]}',
                 'summon minecraft:marker ~ ~ ~ {Tags:["angel.mon","angel.aim","angel.new"]}',
                 'summon minecraft:marker ~ ~ ~ {Tags:["angel.mon","angel.target","angel.new"]}',
                 'summon minecraft:marker ~ ~ ~ {Tags:["angel.mon","angel.aimpt","angel.new"]}']
        cs = CORE_BOX * H
        lines.append(f'summon minecraft:interaction ~ ~ ~ {{Tags:["angel.mon","angel.core","angel.new"],width:{f(cs)},height:{f(cs)},response:1b}}')
        lines.append(f'summon minecraft:interaction ~ ~ ~ {{Tags:["angel.mon","angel.body","angel.new"],width:{f(BODY_W * H)},height:{f(BODY_H * H)},response:1b}}')
        for i, (p, e) in enumerate(zip(P, bs0)):
            bl, sk = BRIGHT.get(p["block"], (15, 15))
            if p["light"]:
                bl, sk = p["light"] if isinstance(p["light"], tuple) else (p["light"], p["light"])
            tags = part_tags(i, p) + ["angel.new"]
            lines.append(
                f'summon minecraft:block_display ~ ~ ~ {{Tags:{snbt_list(tags)},block_state:"{p["block"]}",'
                f'transformation:{transform_nbt(e, k, True)},interpolation_duration:0,teleport_duration:2,'
                f'view_range:8f,shadow_radius:0f,brightness:{{block:{bl},sky:{sk}}}}}')
        lines += ["tp @e[tag=angel.new] ~ ~ ~ ~ 0",
                  "tag @e[tag=angel.new] remove angel.new",
                  f"scoreboard players set #h angel.mon {H}",
                  f"scoreboard players set #S angel.mon {int(round(walk_stride(k) * 1000))}",
                  "scoreboard players set #arrived angel.walk 0",
                  "scoreboard players set #walking angel.mon 0",
                  "scoreboard players set #dur angel.mon 1",
                  "function angel:angel/pose_idle"]
        put(f"s/{H}", lines)

        for pn in POSE_FILES:
            pose = poses[pn]
            bs = model.pose_boxes(pose)
            lines = [f"# pose {pn}, height {H}. #dur angel.mon = interpolation ticks",
                     "execute as @e[type=minecraft:block_display,tag=angel.part] store result entity @s interpolation_duration int 1 run scoreboard players get #dur angel.mon",
                     "execute as @e[type=minecraft:block_display,tag=angel.part] run data modify entity @s start_interpolation set value 0"]
            for i, e in enumerate(bs):
                lines.append(f"data merge entity @e[type=minecraft:block_display,tag=angel.p{i},limit=1] {{transformation:{transform_nbt(e, k)}}}")
            eye = model.EYE_ON if pose.get("eyes") else model.EYE_OFF
            lines.append(f'execute as @e[type=minecraft:block_display,tag=angel.eye] run data merge entity @s {{block_state:"{eye}"}}')
            c, b = pose_hit_offsets(pose, k)
            lines.append(f'data modify storage angel:mon off set value {{cx:"{c[0]:.3f}",cy:"{c[1]:.3f}",cz:"{c[2]:.3f}",bx:"{b[0]:.3f}",by:"{b[1]:.3f}",bz:"{b[2]:.3f}"}}')
            lines.append("function angel:angel/sync_hit with storage angel:mon off")
            put(f"p/{pn}_{H}", lines)

        (lx, lz), (rx, rz) = foot_offsets(k)
        sc = max(0.5, k)
        fx = [f"# footfall at height {H}: the foot that just landed. #foot 0 = left (walk_l), 1 = right (walk_r)"]
        for nm, (x, z) in (("0", (lx, lz)), ("1", (rx, rz))):
            fx += [
                f"execute if score #foot angel.mon matches {nm} positioned ^{x:.2f} ^ ^{z:.2f} run function angel:angel/fx_foot_{H}_at"]
        put(f"fx_foot_{H}", fx)
        vol = min(8.0, 1.5 + k * 3.5)
        n = int(min(60, 10 + k * 40))
        put(f"fx_foot_{H}_at", [
            f"playsound minecraft:entity.warden.step hostile @a ~ ~ ~ {vol:.1f} 0.5",
            f"playsound minecraft:entity.iron_golem.step hostile @a ~ ~ ~ {vol:.1f} 0.5",
            f"playsound minecraft:block.anvil.land hostile @a ~ ~ ~ {vol * 0.6:.1f} 0.5",
            f'particle minecraft:block{{block_state:"minecraft:gray_concrete"}} ~ ~0.2 ~ {sc * 2.0:.1f} 0.2 {sc * 2.0:.1f} 0.08 {n} force',
            f"particle minecraft:large_smoke ~ ~0.4 ~ {sc * 2.5:.1f} 0.1 {sc * 2.5:.1f} 0.01 {max(4, n // 3)} force",
            f"particle minecraft:poof ~ ~0.3 ~ {sc * 3.0:.1f} 0.1 {sc * 3.0:.1f} 0.04 {max(4, n // 4)} force",
        ])

    # ------------------------------------------------------------ dispatchers: pose -> per-height function
    for pn in POSE_FILES:
        put(f"pp/{pn}", [f"execute if score #h angel.mon matches {H} run function angel:angel/p/{pn}_{H}" for H in HEIGHTS])
    put("summon_dispatch", [f"execute if score #h angel.mon matches {H} run function angel:angel/s/{H}" for H in HEIGHTS])
    put("fx_foot", [f"execute if score #h angel.mon matches {H} run function angel:angel/fx_foot_{H}" for H in HEIGHTS])

    # ------------------------------------------------------------ summon / remove
    snap = ["# snap the requested height to the nearest generated one (geometric midpoints)",
            "execute store result score #hin angel.mon run data get storage angel:mon in.height 1"]
    lo = 0
    for hi, H in SNAP:
        snap.append(f"execute if score #hin angel.mon matches {lo}..{hi} run scoreboard players set #h angel.mon {H}")
        lo = hi + 1
    put("summon_snap", snap)
    put("summon", [
        "# function angel:angel/summon {height:60}   at the executor's position and rotation",
        "function angel:angel/remove",
        "$data modify storage angel:mon in set value {height:$(height)}",
        "function angel:angel/summon_snap",
        "function angel:angel/summon_dispatch",
    ])
    put("remove", [
        "# function angel:angel/remove   (everything of the monster; also stops its loops)",
        "schedule clear angel:angel/walk_tick",
        "schedule clear angel:angel/anim_tick",
        "schedule clear angel:angel/die_2",
        "schedule clear angel:angel/die_3",
        "scoreboard players set #walking angel.mon 0",
        "scoreboard players set #loop angel.mon 0",
        "kill @e[tag=angel.mon]",
    ])
    put("sync_hit", [
        "# keeps the two hit boxes at their offsets from the root (macro args: cx cy cz bx by bz, left/up/forward)",
        "$execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run tp @e[type=minecraft:interaction,tag=angel.core,limit=1] ^$(cx) ^$(cy) ^$(cz)",
        "$execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run tp @e[type=minecraft:interaction,tag=angel.body,limit=1] ^$(bx) ^$(by) ^$(bz)",
    ])
    put("sync", [
        "# moves every part and both hit boxes to the root",
        "execute as @e[type=minecraft:block_display,tag=angel.part] run tp @s @e[type=minecraft:marker,tag=angel.root,limit=1]",
        "function angel:angel/sync_hit with storage angel:mon off",
    ])

    # ------------------------------------------------------------ public poses
    def loop_pose(name, a, b, dur_a, period, eyes_note=""):
        put(f"pose_{name}", [
            f"# pose {name}: a slow loop of two key poses",
            "schedule clear angel:angel/anim_tick", "schedule clear angel:angel/die_2", "schedule clear angel:angel/die_3",
            "schedule clear angel:angel/charge_2", "schedule clear angel:angel/charge_3",
            f"scoreboard players set #loop angel.mon {1 if name == 'idle' else 2}",
            f"scoreboard players set #lp angel.mon 0",
            f"scoreboard players set #dur angel.mon {dur_a}",
            f"function angel:angel/pp/{a}",
            f"schedule function angel:angel/anim_tick {period}t",
        ])

    loop_pose("idle", "idle_a", "idle_b", 30, 40)
    loop_pose("regenerating", "regen_0", "regen_1", 14, 10)
    put("anim_tick", [
        "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
        "execute if score #walking angel.mon matches 1 run return 0",
        "execute if score #loop angel.mon matches 0 run return 0",
        "execute if score #loop angel.mon matches 2 run return run function angel:angel/anim_r",
        "execute if score #lp angel.mon matches 0 run return run function angel:angel/anim_b",
        "function angel:angel/anim_a",
    ])
    put("anim_b", [
        "scoreboard players set #lp angel.mon 1",
        "execute if score #loop angel.mon matches 1 run scoreboard players set #dur angel.mon 40",
        "execute if score #loop angel.mon matches 1 run function angel:angel/pp/idle_b",
        "execute if score #loop angel.mon matches 1 run schedule function angel:angel/anim_tick 40t",
    ])
    put("anim_a", [
        "scoreboard players set #lp angel.mon 0",
        "execute if score #loop angel.mon matches 1 run scoreboard players set #dur angel.mon 40",
        "execute if score #loop angel.mon matches 1 run function angel:angel/pp/idle_a",
        "execute if score #loop angel.mon matches 1 run schedule function angel:angel/anim_tick 40t",
    ])
    # regenerating: 8 key frames, one every 10 ticks (slow breathing, a flickering core, the plates shifting)
    put("anim_r", ["scoreboard players add #lp angel.mon 1",
                   "execute if score #lp angel.mon matches 8.. run scoreboard players set #lp angel.mon 0",
                   "scoreboard players set #dur angel.mon 9"] +
        [f"execute if score #lp angel.mon matches {i} run function angel:angel/pp/regen_{i}" for i in range(8)] +
        ["schedule function angel:angel/anim_tick 10t"])

    def one_shot(name, pp, dur, extra=()):
        clr = ["schedule clear angel:angel/charge_2", "schedule clear angel:angel/charge_3"]
        if not name.startswith("dying"):
            clr += ["schedule clear angel:angel/die_2", "schedule clear angel:angel/die_3"]
        put(f"pose_{name}", [f"# pose {name} (held until the next pose)", "schedule clear angel:angel/anim_tick"] + clr + [
                             "scoreboard players set #loop angel.mon 0", f"scoreboard players set #dur angel.mon {dur}",
                             f"function angel:angel/pp/{pp}"] + list(extra))

    # charging: three stages (the glow of the eyes grows, the body leans further, a glow gathers in front of the mask)
    put("pose_charging", [
        "# pose charging: stage 1 now, stage 2 after 10 ticks, stage 3 after 24 (the beam fires at 34 / 40)",
        "schedule clear angel:angel/anim_tick", "schedule clear angel:angel/die_2", "schedule clear angel:angel/die_3",
        "scoreboard players set #loop angel.mon 0", "scoreboard players set #dur angel.mon 10",
        "function angel:angel/pp/charge",
        "schedule function angel:angel/charge_2 10t", "schedule function angel:angel/charge_3 24t"])
    put("charge_2", ["execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
                     "scoreboard players set #dur angel.mon 14", "function angel:angel/pp/charge_2"])
    put("charge_3", ["execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
                     "scoreboard players set #dur angel.mon 10", "function angel:angel/pp/charge_3"])
    one_shot("windup", "windup", 14)
    one_shot("thrust", "thrust", 3)
    one_shot("stagger", "stagger", 6)
    one_shot("wrap_open", "wrap_open", 10)
    one_shot("wrapping", "wrap_close", 8)
    one_shot("dying_1", "die_1", 30)
    one_shot("dying_2", "die_2", 40)
    one_shot("dying_3", "die_3", 30)
    put("pose_dying", [
        "# the death: knees buckle, it folds, falls back (about 4 seconds); the core goes dark",
        "schedule clear angel:angel/anim_tick", "schedule clear angel:angel/charge_2", "schedule clear angel:angel/charge_3",
        "scoreboard players set #walking angel.mon 0",
        "function angel:angel/pose_dying_1",
        "function angel:angel/core_stage {stage:2}",
        "schedule function angel:angel/die_2 30t",
        "schedule function angel:angel/die_3 70t",
    ])
    put("die_2", ["execute if entity @e[type=minecraft:marker,tag=angel.root] run function angel:angel/pose_dying_2"])
    put("die_3", ["execute if entity @e[type=minecraft:marker,tag=angel.root] run function angel:angel/pose_dying_3"])
    put("pose", [
        "# function angel:angel/pose {pose:\"idle\"}   idle | regenerating | charging | dying | windup | thrust | stagger | wrap_open | wrapping",
        "$function angel:angel/pose_$(pose)",
    ])
    put("core_stage", [
        "# function angel:angel/core_stage {stage:0|1|2}   0 whole, 1 cracked (magma texture), 2 dead (dark)",
        "$function angel:angel/core_stage_$(stage)",
    ])
    put("core_stage_0", [f'execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {{block_state:"{model.CORE}"}}'])
    put("core_stage_1", [f'execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {{block_state:"{model.CORE_CRACKED}"}}'])
    put("core_stage_2", ['execute as @e[type=minecraft:block_display,tag=angel.coreglow] run data merge entity @s {block_state:"minecraft:black_concrete"}',
                         'execute as @e[type=minecraft:block_display,tag=angel.veil] run data merge entity @s {block_state:"minecraft:air"}',
                         'execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {block_state:"minecraft:black_concrete"}',
                         'execute as @e[type=minecraft:block_display,tag=angel.halo] run data merge entity @s {block_state:"minecraft:gray_stained_glass"}'])
    # the halo carries both tags corebody + halo: mark it in the summon lines
    # (done below by a tag line in the summons)
    for H in HEIGHTS:
        F[f"s/{H}"].insert(-1, "tag @e[type=minecraft:block_display,tag=angel.p%d] add angel.halo" % [p["name"] for p in P].index("coreHalo"))

    # ------------------------------------------------------------ walking
    put("walk", [
        "# function angel:angel/walk {x:..,y:..,z:..,speed:0.15}   sets #arrived angel.walk to 1 on arrival (0 while walking)",
        "kill @e[type=minecraft:marker,tag=angel.target]",
        '$summon minecraft:marker $(x) $(y) $(z) {Tags:["angel.mon","angel.target"]}',
        "$data modify storage angel:mon walk set value {speed:$(speed),stop:0.0d}",
        "function angel:angel/walk_go",
    ])
    put("walk_go", [
        "# starts (or re-tunes) walking toward the angel.target marker; speed/stop come from storage angel:mon walk",
        "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
        "execute store result score #spd angel.mon run data get storage angel:mon walk.speed 1000",
        "execute if score #spd angel.mon matches ..20 run scoreboard players set #spd angel.mon 20",
        "# blocks the body travels per step / speed per tick = ticks per step",
        "scoreboard players operation #T angel.mon = #S angel.mon",
        "scoreboard players operation #T angel.mon /= #spd angel.mon",
        "execute if score #T angel.mon matches ..13 run scoreboard players set #T angel.mon 14",
        "execute if score #T angel.mon matches 161.. run scoreboard players set #T angel.mon 160",
        "# movement per update (2 ticks) and the arrival distance as macro args",
        "scoreboard players operation #stp angel.mon = #spd angel.mon",
        "scoreboard players operation #stp angel.mon *= #2 angel.mon",
        "execute store result storage angel:mon walk.step double 0.001 run scoreboard players get #stp angel.mon",
        "scoreboard players add #stp angel.mon 100",
        "execute store result storage angel:mon walk.arr double 0.001 run scoreboard players get #stp angel.mon",
        "execute if data storage angel:mon {walk:{stop:0.0d}} run data modify storage angel:mon walk.stopd set from storage angel:mon walk.arr",
        "execute unless data storage angel:mon {walk:{stop:0.0d}} run data modify storage angel:mon walk.stopd set from storage angel:mon walk.stop",
        "scoreboard players set #arrived angel.walk 0",
        "execute if score #walking angel.mon matches 1 run return 0",
        "scoreboard players set #walking angel.mon 1",
        "scoreboard players set #step angel.mon 0",
        "scoreboard players set #foot angel.mon 1",
        "scoreboard players set #landed angel.mon 0",
        "schedule function angel:angel/walk_tick 1t",
    ])
    put("turn", [
        "# turns the root toward the angel.target marker, at most 8 degrees per call (calls come every 2 ticks)",
        "tp @e[type=minecraft:marker,tag=angel.aim,limit=1] @e[type=minecraft:marker,tag=angel.root,limit=1]",
        "rotate @e[type=minecraft:marker,tag=angel.aim,limit=1] facing entity @e[type=minecraft:marker,tag=angel.target,limit=1] feet",
        "execute store result score #ya angel.mon run data get entity @e[type=minecraft:marker,tag=angel.aim,limit=1] Rotation[0] 10",
        "execute store result score #yr angel.mon run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Rotation[0] 10",
        "scoreboard players operation #dy angel.mon = #ya angel.mon",
        "scoreboard players operation #dy angel.mon -= #yr angel.mon",
        "execute if score #dy angel.mon matches 1801.. run scoreboard players remove #dy angel.mon 3600",
        "execute if score #dy angel.mon matches ..-1801 run scoreboard players add #dy angel.mon 3600",
        "execute if score #dy angel.mon matches 80.. as @e[type=minecraft:marker,tag=angel.root,limit=1] run rotate @s ~8 ~",
        "execute if score #dy angel.mon matches ..-80 as @e[type=minecraft:marker,tag=angel.root,limit=1] run rotate @s ~-8 ~",
        "execute if score #dy angel.mon matches -79..79 run tp @e[type=minecraft:marker,tag=angel.root,limit=1] @e[type=minecraft:marker,tag=angel.aim,limit=1]",
    ])
    put("walk_tick", [
        "execute unless score #walking angel.mon matches 1 run return 0",
        "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return run scoreboard players set #walking angel.mon 0",
        "function angel:angel/turn",
        "# arrived?",
        "function angel:angel/walk_arrive_check with storage angel:mon walk",
        "execute unless score #walking angel.mon matches 1 run return 0",
        "# one update of movement: 2 ticks worth",
        "function angel:angel/walk_move with storage angel:mon walk",
        "function angel:angel/sync",
        "scoreboard players remove #step angel.mon 2",
        "execute if score #step angel.mon matches ..0 run function angel:angel/step",
        "schedule function angel:angel/walk_tick 2t",
    ])
    put("walk_arrive_check", [
        "$execute at @e[type=minecraft:marker,tag=angel.target,limit=1] if entity @e[type=minecraft:marker,tag=angel.root,distance=..$(stopd)] run function angel:angel/walk_arrive",
    ])
    put("walk_move", [
        "$execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s run tp @s ^ ^ ^$(step)",
    ])
    put("walk_arrive", [
        "scoreboard players set #walking angel.mon 0",
        "scoreboard players set #arrived angel.walk 1",
        "execute if score #foot angel.mon matches 0..1 run function angel:angel/fx_foot",
        "# on a real arrival (a target reached, not a stand-off) snap onto it; stand-offs keep their place",
        "execute if data storage angel:mon {walk:{stop:0.0d}} at @e[type=minecraft:marker,tag=angel.target,limit=1] run tp @e[type=minecraft:marker,tag=angel.root,limit=1] ~ ~ ~",
        "scoreboard players set #dur angel.mon 24",
        "function angel:angel/sync",
        "function angel:angel/pose_idle",
    ])
    # step toggles properly: write it explicitly instead of the clumsy lines above
    put("step", [
        "# a step boundary: the foot that was moving forward has landed (fx), the other leg starts to swing",
        "execute if score #landed angel.mon matches 1 run function angel:angel/fx_foot",
        "scoreboard players set #landed angel.mon 1",
        "scoreboard players set #dur angel.mon 0",
        "scoreboard players operation #dur angel.mon = #T angel.mon",
        "execute if score #foot angel.mon matches 0 run scoreboard players set #nextfoot angel.mon 1",
        "execute if score #foot angel.mon matches 1 run scoreboard players set #nextfoot angel.mon 0",
        "scoreboard players operation #foot angel.mon = #nextfoot angel.mon",
        "scoreboard players operation #step angel.mon = #T angel.mon",
        "execute if score #foot angel.mon matches 0 run function angel:angel/pp/walk_l",
        "execute if score #foot angel.mon matches 1 run function angel:angel/pp/walk_r",
    ])
    put("stop_walking", [
        "schedule clear angel:angel/walk_tick",
        "scoreboard players set #walking angel.mon 0",
    ])
    return F


