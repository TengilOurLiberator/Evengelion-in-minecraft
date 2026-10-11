"""Generates the fight's functions (namespace angel, folder fight/).  See README.md for the design.

Everything about the boss fight is numbers in CFG (below) so the lead can tune it and rebuild.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402

FH = 30                                    # monster height in the fight
K = FH / 100.0

CFG = dict(
    giant_hp=100,           # the giant's health (points)
    core_hp=40,             # hits on the core to win
    crack_at=20,            # core hits left when the core cracks (phase B)
    wrap_at=8,              # core hits left when the monster wraps itself round the giant
    wrap_ticks=280,         # the self-destruct countdown (14 s); the remaining core hits must land in it
    beam_dmg=25, thrust_dmg=15,
    beam_charge=40, beam_charge_b=34,       # ticks of charging (eyes lit) before the beam
    beam_recover=24,
    thrust_windup=26, thrust_recover=44,
    cd_beam=150, cd_beam_b=105, cd_thrust=100, cd_thrust_b=70,       # cooldown after an attack
    hit_cd=7,               # ticks between two counted core hits
    near=12.5,              # blocks: from the giant's shoulders (22 up) to the core centre: the barrier cancels inside this
    reach_up=22.0,
    giant_inv=20,           # invulnerability ticks after a hit
    regen_wait=160, regen_every=20, regen_amt=2,
    speed_a=0.30, speed_b=0.42, wrap_speed=0.9,
    stand_off=17.0, thrust_range=24, beam_range=140,
    intro_ticks=500, intro_after_step=120,
    scale=16, step_height=2.6, move_speed=0.30, jump=1.0, gravity=0.12, safe_fall=48, reach_entity=18,
    reach_block=20, atk_dmg=20, atk_kb=2, kb_res=0.6,
)

ARENA = dict(origin=(1160.0, 64.0, 160.0), angel=(1160.0, 64.0, 50.0), xmin=1152.0, xmax=1168.0, zmax=140.0)


def eye_offset():
    """(up, forward) in blocks of the eyes from the root, in the charging pose."""
    model.build()
    e = model.eye_centre(model.poses()["charge"])
    return e[1] * K, e[2] * K


def script_lines():
    """{ '7_04': ('MISATO', 'text') } from script.md (scene 7)."""
    out = {}
    p = os.path.join(os.path.dirname(os.path.dirname(HERE)), "script.md")
    if not os.path.isfile(p):
        return out
    for ln in open(p, encoding="utf-8"):
        m = re.match(r"\*\*(\w+)\*\*\s+`(7)\.(\d+)`\s+(.*)$", ln.strip())
        if m:
            txt = re.sub(r"\s*\*\(.*?\)\*\s*$", "", m.group(4)).strip()
            out[f"7_{m.group(3)}"] = (m.group(1), txt)
    return out


def tjson(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def gen(F, pack_function_dir, story_hand_exists):
    """F: dict path -> lines, relative to function/fight/."""
    C = CFG

    def put(path, lines):
        F.setdefault(path, []).extend(lines if isinstance(lines, list) else lines.strip("\n").split("\n"))

    ey, ez = eye_offset()
    ox, oy, oz = ARENA["origin"]
    ax, ay, az = ARENA["angel"]
    core_y = 0.0
    sc = lambda n, v: f"scoreboard players set #{n} angel.fight {v}"

    # ============================================================ load / tick
    put("load", [
        "# objectives, constants, bossbars (all idempotent)",
        "scoreboard objectives add angel.mon dummy",
        "scoreboard objectives add angel.walk dummy",
        "scoreboard objectives add angel.fight dummy",
        "scoreboard objectives add angel.barks dummy",
        "scoreboard objectives add angel.story dummy",
        "scoreboard players set #2 angel.mon 2",
        "scoreboard players set #2 angel.fight 2",
        'bossbar add angel:fight/giant {"text":"UNIT-01","color":"green"}',
        'bossbar add angel:fight/angel {"text":"ANGEL","color":"red"}',
        'bossbar add angel:fight/wrap {"text":"SELF-DESTRUCT","color":"dark_red"}',
        f"bossbar set angel:fight/giant max {C['giant_hp']}",
        f"bossbar set angel:fight/angel max {C['core_hp']}",
        f"bossbar set angel:fight/wrap max {C['wrap_ticks']}",
        "bossbar set angel:fight/giant color green",
        "bossbar set angel:fight/angel color red",
        "bossbar set angel:fight/angel style notched_10",
        "bossbar set angel:fight/wrap color red",
        "bossbar set angel:fight/wrap style notched_20",
        "execute unless data storage angel:fight q run data modify storage angel:fight q set value []",
        "execute unless data storage angel:fight played run data modify storage angel:fight played set value []",
        "execute unless score #run angel.fight matches 1 run scoreboard players set #run angel.fight 0",
    ])
    put("tick", [
        "# free when no fight is running: one score check",
        "execute unless score #run angel.fight matches 1 run return 0",
        "scoreboard players add #tick angel.fight 1",
        "function angel:fight/pump",
        "execute if score #phase angel.fight matches 4 run return run function angel:fight/won_tick",
        "execute if score #phase angel.fight matches 5 run return run function angel:fight/lost_tick",
        "function angel:fight/giant_tick",
        "function angel:fight/hit_tick",
        "function angel:fight/ai_tick",
    ])

    # ============================================================ the giant: attributes
    giant_attrs = [("scale", C["scale"]), ("step_height", C["step_height"]), ("movement_speed", C["move_speed"]),
                   ("jump_strength", C["jump"]), ("gravity", C["gravity"]), ("safe_fall_distance", C["safe_fall"]),
                   ("fall_damage_multiplier", 0.0), ("entity_interaction_range", C["reach_entity"]),
                   ("block_interaction_range", C["reach_block"]), ("attack_damage", C["atk_dmg"]),
                   ("attack_knockback", C["atk_kb"]), ("knockback_resistance", C["kb_res"])]
    put("become_giant", ["# as the player: scale 16 (the attribute's maximum) and everything that goes with it. become_human restores all."]
        + [f"attribute @s minecraft:{a} base set {v}" for a, v in giant_attrs]
        + ["tag @s add angel.giant"])
    put("become_human", ["# as the player: every attribute back to its default"]
        + [f"attribute @s minecraft:{a} base reset" for a, _ in giant_attrs]
        + ["tag @s remove angel.giant", "effect clear @s minecraft:slowness", "effect clear @s minecraft:blindness"])
    put("leave_giant", [
        "# as the giant: back to human size at the launch plaza lift, facing north up the avenue",
        f"tp @s {ox + 0.5} {oy} {oz + 0.5} 180 0",
        "function angel:fight/become_human",
    ])

    # ============================================================ start / stop
    put("start", [
        "# function angel:fight/start   (as the player, who has just arrived at city.launch_top)",
        "function angel:fight/stop_quiet",
        "execute unless score #test angel.fight matches 1 run tag @a remove angel.giant",
        "execute if entity @s[type=minecraft:player] run tag @s add angel.giant",
        "execute unless entity @e[tag=angel.giant] run tag @a[limit=1] add angel.giant",
        "execute if entity @s[tag=angel.pending] run tag @s add angel.giant",
        "tag @e[tag=angel.pending] remove angel.pending",
        "execute as @e[tag=angel.giant] run function angel:fight/become_giant",
        "scoreboard players add #attempt angel.fight 1",
        sc("gh", C["giant_hp"]), sc("ch", C["core_hp"]), sc("phase", 0), sc("st", 0), sc("t", 0), sc("cd", 0),
        sc("ginv", 0), sc("gcalm", 0), sc("hitcd", 0), sc("cd09", 0), sc("steps", 0), sc("it", 0), sc("nav", 99),
        sc("t20", 0), sc("pt", 0), sc("gap", 0), sc("bt", C["beam_charge"]), sc("locked", 0), sc("sl", 30),
        sc("wt", C["wrap_ticks"]), sc("dmg", 0), sc("blocked1", 0), sc("destroy", 1),
        "scoreboard players reset * angel.barks",
        "data modify storage angel:fight q set value []",
        "data modify storage angel:fight played set value []",
        "kill @e[tag=angel.fight]",
        f'summon minecraft:marker {ox} {oy} {oz} {{Tags:["angel.fight","angel.origin"]}}',
        f"execute positioned {ax} {ay} {az} rotated 0 0 run function angel:angel/summon {{height:{FH}}}",
        "tag @e[tag=angel.mon] add angel.fight",
        "function angel:angel/core_stage {stage:0}",
        "bossbar set angel:fight/giant players @e[tag=angel.giant,type=minecraft:player]",
        "bossbar set angel:fight/angel players @e[tag=angel.giant,type=minecraft:player]",
        "bossbar set angel:fight/angel name {\"text\":\"ANGEL\",\"color\":\"red\"}",
        "bossbar set angel:fight/wrap players",
        "bossbar set angel:fight/giant visible true",
        "bossbar set angel:fight/angel visible true",
        "bossbar set angel:fight/wrap visible false",
        "bossbar set angel:fight/giant color green",
        "function angel:fight/bark {id:\"7_01\"}",
        "function angel:fight/bark {id:\"7_02\"}",
        sc("run", 1),
    ])
    put("stop_quiet", [
        "# cleans up everything of the fight except the player's scale",
        sc("run", 0), sc("phase", 0),
        "schedule clear angel:fight/fx_fade", "schedule clear angel:fight/fx_clear", "schedule clear angel:fight/restart_go",
        "function angel:angel/remove",
        "kill @e[tag=angel.fight]",
        "bossbar set angel:fight/giant players", "bossbar set angel:fight/angel players", "bossbar set angel:fight/wrap players",
        "bossbar set angel:fight/giant visible false", "bossbar set angel:fight/angel visible false", "bossbar set angel:fight/wrap visible false",
        "execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness",
        "execute as @e[tag=angel.giant] run effect clear @s minecraft:blindness",
    ])
    put("stop", [
        "# function angel:fight/stop   removes every entity of the fight and returns the player to human size",
        "execute as @e[tag=angel.giant] run function angel:fight/become_human",
        "function angel:fight/stop_quiet",
        "scoreboard players set #test angel.fight 0",
        "kill @e[tag=angel.test]",
    ])

    # ============================================================ barks (queue)
    ids = [f"7_{i:02d}" for i in range(1, 21)]
    put("bark", [
        "# function angel:fight/bark {id:\"7_04\"}: queues a line, once per attempt",
        "$execute if score #$(id) angel.barks matches 1 run return 0",
        "$scoreboard players set #$(id) angel.barks 1",
        "$data modify storage angel:fight q append value {id:\"$(id)\"}",
    ])
    put("bark_beam", [
        "# the beam warning may repeat, with a cooldown, and only if nothing else is waiting",
        "execute if score #cd09 angel.fight matches 1.. run return 0",
        "execute if score #talking angel.story matches 1 run return 0",
        "execute if data storage angel:fight q[0] run return 0",
        sc("cd09", 400),
        'data modify storage angel:fight q append value {id:"7_09"}',
    ])
    put("pump", [
        "# plays the next queued line when nothing is being said",
        "execute if score #gap angel.fight matches 1.. run scoreboard players remove #gap angel.fight 1",
        "execute if score #gap angel.fight matches 1.. run return 0",
        "execute if score #talking angel.story matches 1 run return 0",
        "execute unless data storage angel:fight q[0] run return 0",
        "function angel:fight/bark_play with storage angel:fight q[0]",
    ])
    put("bark_play", [
        "$data modify storage angel:fight played append value {id:\"$(id)\"}",
        "$function angel:fight/say/$(id)",
        "data remove storage angel:fight q[0]",
        sc("gap", 10),
    ])
    lines = script_lines()
    for i in ids:
        real = os.path.join(pack_function_dir, "say", f"{i}.mcfunction")
        if os.path.isfile(real):
            put(f"say/{i}", [f"function angel:say/{i}"])
        else:
            who, txt = lines.get(i, ("", i))
            col = {"MISATO": "gold", "RITSUKO": "aqua", "GENDO": "gray", "BASE": "green", "REI": "white"}.get(who, "white")
            dur = max(40, int(len(txt) * 1.5))
            put(f"say/{i}", [
                f"# stand-in for angel:say/{i} (no such function when the pack was built)",
                f'tellraw @a [{{"text":"[{who}] ","color":"{col}","bold":true}},{{"text":"{tjson(txt)}","color":"white"}}]',
                "scoreboard players set #talking angel.story 1",
                f"schedule function angel:fight/talk_end {dur}t",
            ])
    put("talk_end", ["scoreboard players set #talking angel.story 0"])
    put("queue_empty", ["# return value: 1 when no line is queued or playing",
                        "execute if data storage angel:fight q[0] run return 0",
                        "execute if score #talking angel.story matches 1 run return 0",
                        "execute if score #gap angel.fight matches 1.. run return 0",
                        "return 1"])

    # ============================================================ the giant each tick
    put("giant_tick", [
        "execute if score #ginv angel.fight matches 1.. run scoreboard players remove #ginv angel.fight 1",
        "execute if score #hitcd angel.fight matches 1.. run scoreboard players remove #hitcd angel.fight 1",
        "execute if score #cd09 angel.fight matches 1.. run scoreboard players remove #cd09 angel.fight 1",
        "scoreboard players add #gcalm angel.fight 1",
        "scoreboard players add #t20 angel.fight 1",
        "execute if score #t20 angel.fight matches 20.. run function angel:fight/second",
        "execute store result bossbar angel:fight/giant value run scoreboard players get #gh angel.fight",
        "execute store result bossbar angel:fight/angel value run scoreboard players get #ch angel.fight",
        "execute if score #steps angel.fight matches 0 at @e[type=minecraft:marker,tag=angel.origin,limit=1] unless entity @e[tag=angel.giant,distance=..8] run function angel:fight/first_steps",
        "# the barrier, drawn in light while the giant is too far to cancel it",
        "execute if score #wallt angel.fight matches 1.. run scoreboard players remove #wallt angel.fight 1",
        "execute unless score #wallt angel.fight matches 1.. run function angel:fight/wall_hint",
    ])
    put("second", [
        sc("t20", 0),
        f"execute if score #gcalm angel.fight matches {C['regen_wait']}.. if score #gh angel.fight matches ..{C['giant_hp'] - 1} run scoreboard players add #gh angel.fight {C['regen_amt']}",
        f"execute if score #gh angel.fight matches {C['giant_hp'] + 1}.. run scoreboard players set #gh angel.fight {C['giant_hp']}",
        "execute if score #gh angel.fight matches 60.. run bossbar set angel:fight/giant color green",
        "execute if score #gh angel.fight matches 30..59 run bossbar set angel:fight/giant color yellow",
        "execute if score #gh angel.fight matches ..29 run bossbar set angel:fight/giant color red",
    ])
    put("first_steps", [sc("steps", 1), 'function angel:fight/bark {id:"7_03"}'])

    # ============================================================ hurting the giant
    put("hurt", [
        "# #dmg angel.fight = points. Shared invulnerability window; the real player also takes a token hit for the flash",
        "execute if score #phase angel.fight matches 4.. run return 0",
        "execute if score #ginv angel.fight matches 1.. run return 0",
        "scoreboard players operation #gh angel.fight -= #dmg angel.fight",
        sc("ginv", C["giant_inv"]), sc("gcalm", 0),
        "execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 3 0.6",
        "execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.iron_golem.damage hostile @a ~ ~ ~ 3 0.5",
        "execute as @e[tag=angel.giant,type=minecraft:player] run damage @s 1 minecraft:magic",
        "execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:instant_health 1 4 true",
        'function angel:fight/bark {id:"7_04"}',
        'function angel:fight/bark {id:"7_05"}',
        f"execute if score #gh angel.fight matches ..{C['giant_hp'] // 4} run function angel:fight/bark {{id:\"7_10\"}}",
        f"execute if score #gh angel.fight matches ..{C['giant_hp'] // 4} run function angel:fight/bark {{id:\"7_11\"}}",
        "execute if score #gh angel.fight matches ..0 run function angel:fight/lost_start",
    ])

    # ============================================================ hits on the monster
    put("hit_tick", [
        "execute as @e[type=minecraft:interaction,tag=angel.core] if data entity @s attack at @s run function angel:fight/core_hit",
        "execute as @e[type=minecraft:interaction,tag=angel.body] if data entity @s attack at @s run function angel:fight/body_hit",
    ])
    put("core_hit", [
        "data remove entity @s attack",
        "execute if score #hitcd angel.fight matches 1.. run return 0",
        "execute if score #phase angel.fight matches 4.. run return 0",
        sc("hitcd", C["hit_cd"]),
        f"# the giant's reach point is {C['reach_up']} up; the box's foot is half its height below the core centre",
        f"execute positioned ~ ~-{C['reach_up'] - FH * 0.15 / 2:.2f} ~ if entity @e[tag=angel.giant,distance=..{C['near']}] run return run function angel:fight/core_land",
        "function angel:fight/core_blocked",
    ])
    put("core_blocked", [
        "# beyond arm's length: the hit stops on the wall of light",
        "execute if score #blocked1 angel.fight matches 0 run function angel:fight/first_blocked",
        sc("wallt", 30),
        f"execute positioned ~ {FH * 0.15 / 2:.2f} ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_flash",
    ])
    put("first_blocked", [sc("blocked1", 1), 'function angel:fight/bark {id:"7_06"}', 'function angel:fight/bark {id:"7_07"}',
                          'function angel:fight/bark {id:"7_08"}'])
    put("core_land", [
        "# within arm's length the fields cancel and the hit lands on the core",
        "scoreboard players remove #ch angel.fight 1",
        "execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0",
        f"particle minecraft:flash{{color:[1.0,0.55,0.45,1.0]}} ~ ~{FH * 0.15 / 2:.2f} ~ 0 0 0 0 1 force",
        f"particle minecraft:crit ~ ~{FH * 0.15 / 2:.2f} ~ 1.2 1.2 1.2 0.4 30 force",
        f"particle minecraft:dust{{color:[1.0,0.1,0.1],scale:2.5}} ~ ~{FH * 0.15 / 2:.2f} ~ 1.4 1.4 1.4 0 24 force",
        "playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 3 1.5",
        "playsound minecraft:block.anvil.land hostile @a ~ ~ ~ 3 1.7",
        "playsound minecraft:entity.iron_golem.damage hostile @a ~ ~ ~ 3 0.6",
        'function angel:fight/bark {id:"7_08"}',
        "execute if score #st angel.fight matches 3 run function angel:fight/begin_stagger",
        f"execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..{C['crack_at']} run function angel:fight/core_crack",
        f"execute if score #phase angel.fight matches 1..2 if score #ch angel.fight matches ..{C['wrap_at']} run function angel:fight/wrap_start",
        "execute if score #phase angel.fight matches 3 if score #ch angel.fight matches ..0 run function angel:fight/won_start",
    ])
    put("body_hit", [
        "data remove entity @s attack",
        "execute if score #hitcd angel.fight matches 1.. run return 0",
        sc("hitcd", C["hit_cd"]),
        "particle minecraft:crit ~ ~ ~ 1 1 1 0.2 6 force",
        "particle minecraft:electric_spark ~ ~ ~ 1.5 1.5 1.5 0.2 8 force",
        "playsound minecraft:block.anvil.hit hostile @a ~ ~ ~ 2 1.8",
        'function angel:fight/bark {id:"7_08"}',
    ])

    # ============================================================ barrier drawing
    R = 0.45 * FH
    ap = R * 0.9239
    wall_hint = ["# faint octagon of light, on the monster's side, facing the giant (every 10 ticks while the giant is far)",
                 "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
                 "execute if score #phase angel.fight matches 3.. run return 0",
                 sc("wallt", 10),
                 "execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~2.25 ~ unless entity @e[tag=angel.giant,distance=..60] run return 0",
                 f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~{FH * 0.075:.2f} ~ positioned ~ ~-{C['reach_up']} ~ if entity @e[tag=angel.giant,distance=..{C['near']}] run return 0",
                 f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~{FH * 0.075:.2f} ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_dots"]
    put("wall_hint", wall_hint)
    import math
    dots = []
    for i in range(8):
        a = math.radians(22.5 + 45 * i)
        a2 = math.radians(22.5 + 45 * (i + 1))
        for t in (0.0, 0.5):
            x = R * ((1 - t) * math.cos(a) + t * math.cos(a2))
            y = R * ((1 - t) * math.sin(a) + t * math.sin(a2))
            dots.append(f"particle minecraft:dust{{color:[1.0,0.62,0.12],scale:3.0}} ^{x:.2f} ^{y:.2f} ^ 0.15 0.15 0.15 0 1 force")
    for a in (0, 90, 180, 270):
        r = math.radians(a)
        dots.append(f"particle minecraft:dust{{color:[1.0,0.62,0.12],scale:2.0}} ^{R * 0.5 * math.cos(r):.2f} ^{R * 0.5 * math.sin(r):.2f} ^ 0.4 0.4 0.4 0 1 force")
    put("wall_dots", dots)

    def disp(block, tr, rot, sc3, tags, bright=15):
        return (f'summon minecraft:block_display ~ ~ ~ {{Tags:["angel.fight","angel.flash",{tags}],block_state:"{block}",'
                f'view_range:16f,interpolation_duration:0,brightness:{{block:{bright},sky:{bright}}},'
                f'transformation:{{translation:[{tr[0]:.3f}f,{tr[1]:.3f}f,{tr[2]:.3f}f],left_rotation:[0f,0f,{math.sin(rot / 2):.4f}f,{math.cos(rot / 2):.4f}f],'
                f'scale:[{sc3[0]:.3f}f,{sc3[1]:.3f}f,{sc3[2]:.3f}f],right_rotation:[0f,0f,0f,1f]}}}}')

    wall = ["# the wall of light flashing where a hit was stopped: 8 bars + 2 translucent squares, facing the giant",
            "playsound minecraft:block.amethyst_block.resonate hostile @a ~ ~ ~ 4 0.7",
            "playsound minecraft:entity.evoker.cast_spell hostile @a ~ ~ ~ 3 1.6",
            "playsound minecraft:block.beacon.deactivate hostile @a ~ ~ ~ 3 1.8"]
    s_edge = 2 * R * math.sin(math.pi / 8)
    th = 0.7
    for i in range(8):
        a = math.radians(45 * i)
        c = (ap * math.cos(a), ap * math.sin(a))
        # centre the box: size (th, s_edge, th) turned about z by a, then its centre sits at c
        # box local centre = size/2; the rotation turns it about the origin, so translate = c - R(size/2)
        sz = (th, s_edge, th)
        h = (sz[0] / 2, sz[1] / 2, sz[2] / 2)
        tx = c[0] - (math.cos(a) * h[0] - math.sin(a) * h[1])
        ty = c[1] - (math.sin(a) * h[0] + math.cos(a) * h[1])
        wall.append(disp("minecraft:orange_concrete", (tx, ty, -h[2]), a, sz, '"angel.wnew"'))
    hh = 0.7 * R
    for rot_deg in (0, 45):
        a = math.radians(rot_deg)
        sz = (2 * hh, 2 * hh, 0.2)
        h = (hh, hh, 0.1)
        tx = -(math.cos(a) * h[0] - math.sin(a) * h[1])
        ty = -(math.sin(a) * h[0] + math.cos(a) * h[1])
        wall.append(disp("minecraft:orange_stained_glass", (tx, ty, -0.1), a, sz, '"angel.wnew"'))
    wall += ["execute as @e[type=minecraft:block_display,tag=angel.wnew] run rotate @s facing entity @e[tag=angel.giant,limit=1] eyes",
             "tag @e[tag=angel.wnew] remove angel.wnew",
             f"particle minecraft:flash{{color:[1.0,0.7,0.3,1.0]}} ~ ~ ~ 0 0 0 0 1 force",
             "schedule function angel:fight/fx_fade 4t", "schedule function angel:fight/fx_clear 14t"]
    put("wall_flash", wall)
    put("fx_fade", ["execute as @e[type=minecraft:block_display,tag=angel.flash] run data merge entity @s {start_interpolation:0,interpolation_duration:9,transformation:{scale:[0f,0f,0f]}}"])
    put("fx_clear", ["kill @e[type=minecraft:block_display,tag=angel.flash]"])

    # a cross of light (hit by the beam): vertical bar and two horizontal ones, so it reads as a cross from anywhere
    def cross(prefix, v, hbar, thick, block="minecraft:white_concrete", at_y=0.0):
        return [
            disp(block, (-thick / 2, -v / 2 + at_y, -thick / 2), 0, (thick, v, thick), '"angel.wnew"'),
            disp(block, (-hbar / 2, -thick / 2 + at_y, -thick / 2), 0, (hbar, thick, thick), '"angel.wnew"'),
            disp(block, (-thick / 2, -thick / 2 + at_y, -hbar / 2), 0, (thick, thick, hbar), '"angel.wnew"'),
        ]
    put("cross_flash", ["# a cross-shaped flash at the current position"] + cross("c", 34.0, 16.0, 1.3)
        + ["tag @e[tag=angel.wnew] remove angel.wnew",
           "particle minecraft:flash{color:[1.0,1.0,1.0,1.0]} ~ ~ ~ 0 0 0 0 1 force",
           "particle minecraft:end_rod ~ ~ ~ 3 6 3 0.25 40 force",
           "playsound minecraft:entity.lightning_bolt.impact hostile @a ~ ~ ~ 6 1.4",
           "playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 6 0.7",
           "schedule function angel:fight/fx_fade 4t", "schedule function angel:fight/fx_clear 16t"])
    # the death: a tall cross-shaped pillar of light
    put("pillar", ["# the Angel's end: a tall cross of light where it stood (bars at a high crossing)"]
        + cross("p", 190.0, 60.0, 5.0, "minecraft:white_concrete", at_y=30.0)
        + cross("q", 190.0, 60.0, 9.0, "minecraft:light_blue_stained_glass", at_y=30.0)
        + ["tag @e[tag=angel.wnew] remove angel.wnew",
           "particle minecraft:flash{color:[1.0,1.0,1.0,1.0]} ~ ~10 ~ 0 0 0 0 1 force",
           "particle minecraft:end_rod ~ ~ ~ 4 40 4 0.3 200 force",
           "particle minecraft:explosion_emitter ~ ~12 ~ 5 5 5 0 6 force",
           "playsound minecraft:entity.lightning_bolt.thunder hostile @a ~ ~ ~ 12 0.6",
           "playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 12 0.5",
           "playsound minecraft:entity.wither.death hostile @a ~ ~ ~ 12 0.6",
           "schedule function angel:fight/fx_fade 90t", "schedule function angel:fight/fx_clear 112t"])

    # ============================================================ monster brain
    put("ai_tick", [
        "execute if score #phase angel.fight matches 0 run function angel:fight/intro_tick",
        "execute if score #phase angel.fight matches 0 run return 0",
        "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
        "execute if score #cd angel.fight matches 1.. run scoreboard players remove #cd angel.fight 1",
        "scoreboard players add #t angel.fight 1",
        "scoreboard players operation #odd angel.fight = #t angel.fight",
        "scoreboard players operation #odd angel.fight %= #2 angel.fight",
        "execute if score #st angel.fight matches 0 run function angel:fight/st_move",
        "execute if score #st angel.fight matches 1 run function angel:fight/st_beam",
        "execute if score #st angel.fight matches 2 run function angel:fight/st_beam_rec",
        "execute if score #st angel.fight matches 3 run function angel:fight/st_thrust",
        "execute if score #st angel.fight matches 4 run function angel:fight/st_thrust_rec",
        "execute if score #st angel.fight matches 5 run function angel:fight/st_stagger",
        "execute if score #st angel.fight matches 6 run function angel:fight/st_wrap_in",
        "execute if score #st angel.fight matches 7 run function angel:fight/st_wrapped",
    ])
    put("intro_tick", [
        "scoreboard players add #it angel.fight 1",
        f"execute if score #steps angel.fight matches 1 if score #it angel.fight matches {C['intro_after_step']}.. run function angel:fight/begin_ai",
        f"execute if score #it angel.fight matches {C['intro_ticks']}.. run function angel:fight/begin_ai",
    ])
    put("begin_ai", [sc("phase", 1), sc("cd", 80), sc("st", 0), sc("t", 0)])
    # --- moving
    put("st_move", [
        "scoreboard players add #nav angel.fight 1",
        "execute if score #nav angel.fight matches 10.. run function angel:fight/nav",
        "execute unless score #walking angel.mon matches 1 if score #odd angel.fight matches 0 run function angel:fight/face_giant",
        "execute if score #cd angel.fight matches ..0 run function angel:fight/choose",
    ])
    xmin, xmax, zmax = ARENA["xmin"] * 10, ARENA["xmax"] * 10, ARENA["zmax"] * 10
    put("nav", [
        "# where to walk: the giant if it is near, else down the avenue; kept on the avenue",
        sc("nav", 0),
        "execute store result score #rz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[2] 10",
        "scoreboard players add #rz angel.fight 260",
        f"data modify entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos set value [{ox}d,{oy}d,0.0d]",
        f"execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] double 0.1 run scoreboard players get #rz angel.fight",
        "execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..75] run tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]",
        "execute store result score #tx angel.fight run data get entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[0] 10",
        "execute store result score #tz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] 10",
        f"execute if score #tx angel.fight matches ..{int(xmin)} run scoreboard players set #tx angel.fight {int(xmin)}",
        f"execute if score #tx angel.fight matches {int(xmax)}.. run scoreboard players set #tx angel.fight {int(xmax)}",
        f"execute if score #tz angel.fight matches {int(zmax)}.. run scoreboard players set #tz angel.fight {int(zmax)}",
        "execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[0] double 0.1 run scoreboard players get #tx angel.fight",
        "execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] double 0.1 run scoreboard players get #tz angel.fight",
        f"execute if score #phase angel.fight matches 1 run data modify storage angel:mon walk set value {{speed:{C['speed_a']},stop:{C['stand_off']}d}}",
        f"execute if score #phase angel.fight matches 2 run data modify storage angel:mon walk set value {{speed:{C['speed_b']},stop:{C['stand_off']}d}}",
        "# walk only while it is farther than the stand-off distance (+ a margin)",
        f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s unless entity @e[tag=angel.giant,distance=..{C['stand_off'] + 3}] run function angel:angel/walk_go",
        f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..{C['stand_off'] + 3}] run function angel:fight/face_giant",
    ])
    put("face_giant", [
        "tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]",
        "function angel:angel/turn", "function angel:angel/sync"])
    put("choose", [
        f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..{C['thrust_range']}] run return run function angel:fight/begin_thrust",
        f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..{C['beam_range']}] run return run function angel:fight/begin_beam",
    ])
    # --- eye beam
    put("begin_beam", [
        sc("st", 1), sc("t", 0), sc("locked", 0),
        f"execute if score #phase angel.fight matches 1 run scoreboard players set #bt angel.fight {C['beam_charge']}",
        f"execute if score #phase angel.fight matches 2.. run scoreboard players set #bt angel.fight {C['beam_charge_b']}",
        "function angel:angel/stop_walking",
        "scoreboard players set #dur angel.mon 14",
        "function angel:angel/pose_charging",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.sonic_charge hostile @a ~ ~ ~ 8 0.9",
        "function angel:fight/bark_beam",
    ])
    put("st_beam", [
        "execute if score #locked angel.fight matches 0 if score #odd angel.fight matches 0 run function angel:fight/aim_track",
        "scoreboard players operation #lk angel.fight = #bt angel.fight",
        "scoreboard players remove #lk angel.fight 12",
        "execute if score #t angel.fight >= #lk angel.fight if score #locked angel.fight matches 0 run function angel:fight/aim_lock",
        "execute if score #locked angel.fight matches 1 run function angel:fight/aim_warn",
        "# charging fx: sparks gather at the eyes, a rising note",
        f"execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^{ey:.2f} ^{ez:.2f} run particle minecraft:end_rod ~ ~ ~ 1.6 1.6 1.6 0.12 4 force",
        f"execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^{ey:.2f} ^{ez:.2f} run particle minecraft:electric_spark ~ ~ ~ 1.2 1.2 1.2 0.3 3 force",
        "execute if score #t angel.fight matches 12 at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.beacon.power_select hostile @a ~ ~ ~ 6 0.7",
        "execute if score #t angel.fight matches 22 at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.beacon.power_select hostile @a ~ ~ ~ 6 1.1",
        "execute if score #t angel.fight matches 30 at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.beacon.power_select hostile @a ~ ~ ~ 6 1.6",
        "execute if score #t angel.fight >= #bt angel.fight run function angel:fight/beam_fire",
    ])
    put("aim_track", [
        "tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]",
        "function angel:angel/turn", "function angel:angel/sync"])
    put("aim_lock", [
        sc("locked", 1),
        "execute at @e[tag=angel.giant,limit=1] run tp @e[type=minecraft:marker,tag=angel.aimpt,limit=1] ~ ~18 ~",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.nearby_closest hostile @a ~ ~ ~ 8 1.4",
    ])
    put("aim_warn", [
        "# a thin red sighting line along the locked beam path",
        "scoreboard players set #rs angel.fight 45",
        f"execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^{ey:.2f} ^{ez:.2f} facing entity @e[type=minecraft:marker,tag=angel.aimpt,limit=1] feet run function angel:fight/ray_warn",
    ])
    put("ray_warn", [
        "execute unless block ~ ~ ~ #angel:fight/beam_pass run return 0",
        "particle minecraft:dust{color:[1.0,0.12,0.1],scale:2.2} ~ ~ ~ 0.05 0.05 0.05 0 1 force",
        "scoreboard players remove #rs angel.fight 1",
        "execute if score #rs angel.fight matches 1.. positioned ^ ^ ^3 run function angel:fight/ray_warn",
    ])
    put("beam_fire", [
        sc("st", 2), sc("t", 0),
        "kill @e[type=minecraft:marker,tag=angel.bi]", "kill @e[type=minecraft:marker,tag=angel.bo]",
        sc("rs", 150), sc("bs", 0),
        "scoreboard players set #dur angel.mon 8",
        "function angel:angel/pose_idle",
        f"execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^{ey:.2f} ^{ez:.2f} run summon minecraft:marker ~ ~ ~ {{Tags:[\"angel.fight\",\"angel.bo\"]}}",
        f"execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^{ey:.2f} ^{ez:.2f} facing entity @e[type=minecraft:marker,tag=angel.aimpt,limit=1] feet run function angel:fight/beam_step",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.sonic_boom hostile @a ~ ~ ~ 10 0.8",
        "execute at @e[type=minecraft:marker,tag=angel.bo,limit=1] run playsound minecraft:entity.lightning_bolt.thunder hostile @a ~ ~ ~ 8 1.8",
        "execute if entity @e[type=minecraft:marker,tag=angel.bi] run function angel:fight/beam_visual",
    ])
    put("beam_step", [
        "# one block of the beam; stops on a block, on the giant, or after the range",
        "execute unless block ~ ~ ~ #angel:fight/beam_pass run return run function angel:fight/beam_impact",
        "execute positioned ~-0.5 ~-0.5 ~-0.5 if entity @e[tag=angel.giant,dx=0,dy=0,dz=0] run return run function angel:fight/beam_hit",
        "particle minecraft:dust{color:[1.0,0.85,0.35],scale:3.0} ~ ~ ~ 0.25 0.25 0.25 0 1 force",
        "scoreboard players add #bs angel.fight 1",
        "scoreboard players remove #rs angel.fight 1",
        "execute if score #rs angel.fight matches 1.. positioned ^ ^ ^1 run function angel:fight/beam_step",
        "execute if score #rs angel.fight matches ..0 run summon minecraft:marker ~ ~ ~ {Tags:[\"angel.fight\",\"angel.bi\"]}",
    ])
    put("beam_impact", [
        "summon minecraft:marker ~ ~ ~ {Tags:[\"angel.fight\",\"angel.bi\"]}",
        "particle minecraft:explosion_emitter ~ ~ ~ 0 0 0 0 2 force",
        "particle minecraft:flash{color:[1.0,0.9,0.6,1.0]} ~ ~ ~ 0 0 0 0 1 force",
        "particle minecraft:large_smoke ~ ~ ~ 2.5 2.5 2.5 0.05 40 force",
        "playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 12 0.6",
        "# a little damage to the city, never near the ground (plaza, street and the lift stay)",
        "execute if score #destroy angel.fight matches 1 run function angel:fight/beam_break",
    ])
    put("beam_break", [
        "summon minecraft:marker ~ ~ ~ {Tags:[\"angel.fight\",\"angel.imp\"]}",
        "execute if entity @e[type=minecraft:marker,tag=angel.imp,y=70,dy=300] run fill ~-1 ~-1 ~-1 ~1 ~1 ~1 minecraft:air",
        "kill @e[type=minecraft:marker,tag=angel.imp]",
    ])
    put("beam_hit", [
        "summon minecraft:marker ~ ~ ~ {Tags:[\"angel.fight\",\"angel.bi\"]}",
        "execute at @e[type=minecraft:marker,tag=angel.bi,limit=1] run function angel:fight/cross_flash",
        sc("dmg", C["beam_dmg"]),
        "function angel:fight/hurt",
    ])
    put("beam_visual", [
        "# the beam itself: a thick white core and a wide yellow glow, from the eyes to where it ended; fades fast",
        "execute store result storage angel:fight beam.len double 1 run scoreboard players get #bs angel.fight",
        "execute at @e[type=minecraft:marker,tag=angel.bo,limit=1] run function angel:fight/beam_draw with storage angel:fight beam",
        "execute as @e[type=minecraft:block_display,tag=angel.wnew] at @s run rotate @s facing entity @e[type=minecraft:marker,tag=angel.bi,limit=1] feet",
        "tag @e[tag=angel.wnew] remove angel.wnew",
        "schedule function angel:fight/fx_fade 4t", "schedule function angel:fight/fx_clear 14t",
    ])
    put("beam_draw", [
        '$summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:white_concrete",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-0.6f,-0.6f,0f],left_rotation:[0f,0f,0f,1f],scale:[1.2f,1.2f,$(len)f],right_rotation:[0f,0f,0f,1f]}}',
        '$summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:yellow_stained_glass",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-1.8f,-1.8f,0f],left_rotation:[0f,0f,0f,1f],scale:[3.6f,3.6f,$(len)f],right_rotation:[0f,0f,0f,1f]}}',
    ])
    put("st_beam_rec", [
        f"execute if score #t angel.fight matches {C['beam_recover']}.. run function angel:fight/end_attack_beam",
    ])
    put("end_attack_beam", [
        sc("st", 0), sc("t", 0), sc("nav", 99),
        f"execute if score #phase angel.fight matches 1 run scoreboard players set #cd angel.fight {C['cd_beam']}",
        f"execute if score #phase angel.fight matches 2.. run scoreboard players set #cd angel.fight {C['cd_beam_b']}",
    ])
    # --- arm thrust
    put("begin_thrust", [
        sc("st", 3), sc("t", 0), sc("locked", 0),
        "function angel:angel/stop_walking",
        "scoreboard players set #dur angel.mon 14",
        "function angel:angel/pose_windup",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.agitated hostile @a ~ ~ ~ 8 0.8",
    ])
    tw = C["thrust_windup"]
    put("st_thrust", [
        f"execute if score #t angel.fight matches ..{tw - 12} if score #odd angel.fight matches 0 run function angel:fight/aim_track",
        f"execute if score #t angel.fight matches {tw - 11}..{tw - 1} run function angel:fight/thrust_warn",
        f"execute if score #t angel.fight matches {tw} run function angel:fight/thrust_strike",
    ])
    put("thrust_warn", [
        "# red marks on the ground where the arm will land",
        f"execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^ ^{FH * 0.62:.1f} run function angel:fight/thrust_ring",
    ])
    ring = []
    for i in range(10):
        a = math.radians(36 * i)
        ring.append(f"particle minecraft:dust{{color:[1.0,0.15,0.1],scale:3.0}} ~{6 * math.cos(a):.2f} ~0.2 ~{6 * math.sin(a):.2f} 0.1 0.05 0.1 0 1 force")
    put("thrust_ring", ring)
    put("thrust_strike", [
        sc("st", 4), sc("t", 0),
        "scoreboard players set #dur angel.mon 3",
        "function angel:angel/pose_thrust",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.attack_impact hostile @a ~ ~ ~ 10 0.7",
        f"execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^ ^{FH * 0.62:.1f} run particle minecraft:explosion ~ ~1 ~ 2 1 2 0 6 force",
        f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s positioned ^ ^ ^{FH * 0.62:.1f} positioned ~-4.5 ~-2 ~-4.5 if entity @e[tag=angel.giant,dx=9,dy=26,dz=9] run function angel:fight/thrust_hit",
    ])
    put("thrust_hit", [
        sc("dmg", C["thrust_dmg"]),
        "function angel:fight/hurt",
        "execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:slowness 2 2 true",
        "execute at @e[tag=angel.giant,limit=1] run particle minecraft:crit ~ ~14 ~ 4 8 4 0.5 40 force",
    ])
    put("st_thrust_rec", [
        "execute if score #t angel.fight matches 14 run scoreboard players set #dur angel.mon 14",
        "execute if score #t angel.fight matches 14 run function angel:angel/pose_idle",
        f"execute if score #t angel.fight matches {C['thrust_recover']}.. run function angel:fight/end_attack_thrust",
    ])
    put("end_attack_thrust", [
        sc("st", 0), sc("t", 0), sc("nav", 99),
        f"execute if score #phase angel.fight matches 1 run scoreboard players set #cd angel.fight {C['cd_thrust']}",
        f"execute if score #phase angel.fight matches 2.. run scoreboard players set #cd angel.fight {C['cd_thrust_b']}",
    ])
    # --- stagger (a hit during the windup) and the crack's pause
    put("begin_stagger", [
        sc("st", 5), sc("t", 0), sc("sl", 36),
        "scoreboard players set #dur angel.mon 6",
        "function angel:angel/pose_stagger",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.hurt hostile @a ~ ~ ~ 8 0.6",
    ])
    put("st_stagger", [
        "execute if score #t angel.fight >= #sl angel.fight run function angel:fight/end_stagger",
    ])
    put("end_stagger", [
        sc("st", 0), sc("t", 0), sc("nav", 99),
        "scoreboard players set #dur angel.mon 20",
        "function angel:angel/pose_idle",
        "execute if score #cd angel.fight matches 41.. run scoreboard players set #cd angel.fight 40",
        "execute unless score #cd angel.fight matches 31.. run scoreboard players set #cd angel.fight 30",
    ])
    put("core_crack", [
        sc("phase", 2), sc("st", 5), sc("t", 0), sc("sl", 80),
        "function angel:angel/stop_walking",
        "function angel:angel/core_stage {stage:1}",
        "function angel:angel/pose_regenerating",
        'execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.roar hostile @a ~ ~ ~ 10 0.7',
        'execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.glass.break hostile @a ~ ~ ~ 10 0.5',
        f'execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:lava ~ ~{FH * 0.075:.2f} ~ 1 1 1 0.2 30 force',
        'bossbar set angel:fight/angel name {"text":"ANGEL  -  core cracked","color":"red"}',
        'function angel:fight/bark {id:"7_12"}',
        'function angel:fight/bark {id:"7_13"}',
    ])
    # --- the wrap and the countdown
    put("wrap_start", [
        sc("phase", 3), sc("st", 6), sc("t", 0), sc("nav", 99),
        "function angel:angel/stop_walking",
        "scoreboard players set #dur angel.mon 10",
        "function angel:angel/pose_wrap_open",
        f"data modify storage angel:mon walk set value {{speed:{C['wrap_speed']},stop:9.0d}}",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.roar hostile @a ~ ~ ~ 12 0.5",
        'bossbar set angel:fight/angel name {"text":"ANGEL  -  it is closing in","color":"red"}',
    ])
    put("st_wrap_in", [
        "tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]",
        "execute if score #t angel.fight matches 1 run function angel:angel/walk_go",
        "execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..16] run function angel:fight/wrap_clamp",
        "execute if score #st angel.fight matches 6 if score #t angel.fight matches 100.. run function angel:fight/wrap_clamp",
    ])
    put("wrap_clamp", [
        sc("st", 7), sc("t", 0), sc("wt", C["wrap_ticks"]),
        "function angel:angel/stop_walking",
        "function angel:fight/wrap_follow",
        "scoreboard players set #dur angel.mon 8",
        "function angel:angel/pose_wrapping",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.sonic_charge hostile @a ~ ~ ~ 10 0.6",
        'bossbar set angel:fight/wrap players @e[tag=angel.giant,type=minecraft:player]',
        "bossbar set angel:fight/wrap visible true",
        'bossbar set angel:fight/angel name {"text":"ANGEL  -  break loose: hit the core","color":"red"}',
        'function angel:fight/bark {id:"7_14"}',
    ])
    put("wrap_follow", [
        "# keeps the monster 8 blocks from the giant, on the side it came from",
        "execute at @e[tag=angel.giant,limit=1] facing entity @e[type=minecraft:marker,tag=angel.root,limit=1] feet run tp @e[type=minecraft:marker,tag=angel.root,limit=1] ^ ^ ^8",
        "tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]",
        "rotate @e[type=minecraft:marker,tag=angel.root,limit=1] facing entity @e[tag=angel.giant,limit=1] feet",
        "function angel:angel/sync",
    ])
    put("st_wrapped", [
        "scoreboard players remove #wt angel.fight 1",
        "execute store result bossbar angel:fight/wrap value run scoreboard players get #wt angel.fight",
        "function angel:fight/wrap_follow",
        "execute as @e[tag=angel.giant,type=minecraft:player] if score #wt angel.fight matches 1.. run effect give @s minecraft:slowness 2 3 true",
        "execute if score #t angel.fight matches 20.. run function angel:fight/wrap_beep",
        "execute if score #wt angel.fight matches ..100 if score #t angel.fight matches 10 run function angel:fight/wrap_beep",
        "execute if score #t angel.fight matches 20.. run scoreboard players set #t angel.fight 0",
        f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{{color:[1.0,0.1,0.1],scale:2.5}} ~ ~{FH * 0.075:.2f} ~ 1.5 1.5 1.5 0 3 force",
        "execute if score #wt angel.fight matches ..0 run function angel:fight/self_destruct",
    ])
    put("wrap_beep", [
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.note_block.bell hostile @a ~ ~ ~ 8 0.7",
        "execute if score #wt angel.fight matches ..100 at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.note_block.bell hostile @a ~ ~ ~ 8 1.6",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run particle minecraft:flash{color:[1.0,0.2,0.1,1.0]} ~ ~12 ~ 0 0 0 0 1 force",
    ])
    put("self_destruct", [
        "execute at @e[tag=angel.giant,limit=1] run function angel:fight/cross_flash",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run particle minecraft:explosion_emitter ~ ~10 ~ 6 6 6 0 8 force",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 16 0.5",
        sc("lost_reason", 2),
        "function angel:fight/lost_start",
    ])

    # ============================================================ winning
    put("won_start", [
        "# the core is broken",
        sc("phase", 4), sc("st", 8), sc("pt", 0),
        "function angel:angel/stop_walking",
        "bossbar set angel:fight/wrap visible false",
        "bossbar set angel:fight/angel visible false",
        "execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 12 0.8",
        'function angel:fight/bark {id:"7_15"}',
        'function angel:fight/bark {id:"7_16"}',
        'function angel:fight/bark {id:"7_17"}',
        'function angel:fight/bark {id:"7_18"}',
    ])
    put("won_tick", [
        "scoreboard players add #pt angel.fight 1",
        "execute if score #pt angel.fight matches 2 run function angel:angel/pose_dying",
        "execute if score #pt angel.fight matches ..130 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~2 ~ 1.5 1.5 1.5 0 2 force",
        "# the pillar of light stands up out of the body, the body is gone, the pillar fades",
        f"execute if score #pt angel.fight matches 135 at @e[type=minecraft:marker,tag=angel.root,limit=1] run function angel:fight/pillar",
        "execute if score #pt angel.fight matches 150 run function angel:angel/remove",
        "execute if score #pt angel.fight matches 150 run tag @e[tag=angel.mon] add angel.fight",
        "execute if score #pt angel.fight matches 240.. if function angel:fight/queue_empty run function angel:fight/won_final",
        "execute if score #pt angel.fight matches 1500.. run function angel:fight/won_final",
    ])
    put("won_final", [
        "# back to human scale at a safe spot, everything cleaned up, then the story takes over",
        "execute as @e[tag=angel.giant] run function angel:fight/leave_giant",
        "function angel:fight/stop_quiet",
        "scoreboard players set #test angel.fight 0",
        "function angel:fight/hand_won",
    ])
    if story_hand_exists:
        put("hand_won", ['function angel:story/fight_done {result:"won"}'])
    else:
        put("hand_won", ["# angel:story/fight_done did not exist when the pack was built: nothing to call",
                         "data modify storage angel:fight handoff set value \"won\""])

    # ============================================================ losing
    put("lost_start", [
        "# giant health 0, or the self-destruct went off. #lost_reason: 1 health, 2 countdown",
        "execute if score #phase angel.fight matches 4.. run return 0",
        sc("phase", 5), sc("pt", 0), sc("st", 8),
        "execute unless score #lost_reason angel.fight matches 2 run scoreboard players set #lost_reason angel.fight 1",
        "function angel:angel/stop_walking",
        "bossbar set angel:fight/wrap visible false",
        "execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness",
        "data modify storage angel:fight q set value []",
        "scoreboard players reset #7_19 angel.barks", "scoreboard players reset #7_20 angel.barks",
        'function angel:fight/bark {id:"7_19"}',
        'function angel:fight/bark {id:"7_20"}',
        "execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.death hostile @a ~ ~ ~ 8 0.7",
        "execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:blindness 12 0 true",
        "execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:slowness 12 6 true",
    ])
    put("lost_tick", [
        "scoreboard players add #pt angel.fight 1",
        "execute if score #pt angel.fight matches ..60 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~2 ~ 1.5 1.5 1.5 0 2 force",
        "execute if score #pt angel.fight matches 140.. if function angel:fight/queue_empty run function angel:fight/restart",
        "execute if score #pt angel.fight matches 1200.. run function angel:fight/restart",
    ])
    put("restart", [
        "# after the defeat bark: restore, put the giant back at the launch, and begin again a moment later",
        "execute as @e[tag=angel.giant] run tag @s add angel.pending",
        "execute as @e[tag=angel.giant] run function angel:fight/leave_giant",
        "function angel:fight/stop_quiet",
        sc("lost_reason", 0),
        "schedule function angel:fight/restart_go 60t",
    ])
    put("restart_go", [
        "execute as @e[tag=angel.pending,limit=1] run function angel:fight/start",
    ])

    # ============================================================ test mode: a stand-in for the player
    put("test/on", [
        "# an armor stand stands in for the player: it is the giant. Drive the fight with the test/ functions.",
        "kill @e[tag=angel.test]",
        sc("test", 1),
        f'summon minecraft:armor_stand {ox} {oy} {oz} {{Tags:["angel.giant","angel.test"],Invulnerable:1b,ShowArms:1b}}',
    ])
    put("test/start", ["function angel:fight/test/on", "execute as @e[tag=angel.test,limit=1] run function angel:fight/start"])
    put("test/off", ["function angel:fight/stop", "kill @e[tag=angel.test]", sc("test", 0)])
    put("test/giant_at", ["# macro: x y z", "$tp @e[tag=angel.test,limit=1] $(x) $(y) $(z)"])
    put("test/set", ["# macro: name value  -> scoreboard #name angel.fight", "$scoreboard players set #$(name) angel.fight $(value)"])
    put("test/hit_core", ["# simulates a player's left click on the core box",
                          "data modify entity @e[type=minecraft:interaction,tag=angel.core,limit=1] attack set value {player:[I;1,2,3,4],timestamp:1L}"])
    put("test/hit_body", ["data modify entity @e[type=minecraft:interaction,tag=angel.body,limit=1] attack set value {player:[I;1,2,3,4],timestamp:1L}"])
    put("test/hurt", ["# macro: dmg", "$scoreboard players set #dmg angel.fight $(dmg)", "function angel:fight/hurt"])
    put("test/status", [
        'tellraw @a [{"text":"phase "},{"score":{"name":"#phase","objective":"angel.fight"}},{"text":" st "},{"score":{"name":"#st","objective":"angel.fight"}},{"text":" t "},{"score":{"name":"#t","objective":"angel.fight"}},{"text":" gh "},{"score":{"name":"#gh","objective":"angel.fight"}},{"text":" ch "},{"score":{"name":"#ch","objective":"angel.fight"}},{"text":" wt "},{"score":{"name":"#wt","objective":"angel.fight"}}]',
    ])
    return F
