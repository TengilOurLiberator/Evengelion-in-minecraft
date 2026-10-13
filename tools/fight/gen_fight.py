"""Generates the fight's functions (namespace angel, folder fight/).  See README.md for the design.

Everything about the boss fight is numbers in the preset tables FULL and VIDEO (below; CFG is the chosen one) so the lead can tune it and rebuild.
"""
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import model  # noqa: E402
import gen_angel  # noqa: E402  (BODY_H; gen_angel reads this module's CFG lazily)

FH = 30                                    # monster height in the fight
K = FH / 100.0

# ====================================================================================================================== presets
# Every number of the fight lives in one of the two tables below; CFG (the dict the generator, estimate.py and selftest.py read) is filled from one of them.
#   "video"  (the default)  the paced fight for the film: a first-time player finishes in about 2:15, and the rules a player can SEE: no hidden guard on the
#                           core, one visible state (vulnerable / shielded), a feedback for every kind of swing, a generous target.
#   "full"                  EXACTLY the numbers and the behaviour of the earlier build (about 5 minutes for a first-time player, the 1.2 s core guard, the faint
#                           dotted barrier): a `full` build reproduces the earlier functions byte for byte.
# Choose with `build_fight.py --pace full|video` (estimate.py takes the same switch) or the environment variable ANGEL_PACE; --pace wins.
FULL = dict(
    giant_hp=100,           # the giant's health (points)
    core_hp=60,             # hits on the core to win (was 40: a scripted player who never dodged won in 63 s; 60 with the 1.2 s core guard below)
    crack_at=30,            # core hits left when the core cracks (phase B)
    wrap_at=10,             # core hits left when the monster wraps itself round the giant
    wrap_ticks=320,         # the self-destruct countdown (16 s) + wrap_bonus per landed hit.  No core guard in the wrap: every hit that connects counts.
                            # One hit per 1.5 s: 10 hits take 15 s, the bar loses 15 s and regains 9 x 0.5 s before the last: 5.5 s to spare; stopping for 6 s in all loses
    wrap_bonus=10,          # ticks (0.5 s) added to the countdown by each landed hit while wrapped (never above wrap_ticks)
    wrap_dist=10.0,         # blocks between the giant's feet and the wrapped monster's root (its beak stays about 4.9 blocks from the eyes; the arms go round the sides)
    wrap_tight_at=160,      # ticks left when the monster squeezes (pose wrap_tight)
    wrap_wait=100,          # the countdown does not start until the bark 7.14 has begun; at most this many ticks of waiting (the line may queue behind another)
    wrap_crack_hits=(8, 6, 4, 2),   # hits left at which the core shows crack 1, 2, 3, 4 (white slivers of light)
    shove=0.8, shove_ticks=6,       # back-off: the monster is thrown back 0.8 x 6 = 4.8 blocks along the avenue in the first 6 ticks, before it turns and walks away
    beam_dmg=25, thrust_dmg=15,
    beam_charge=40, beam_charge_b=34,       # ticks of charging (eyes lit) before the beam
    beam_recover=24,
    thrust_windup=26, thrust_recover=44,
    cd_beam=150, cd_beam_b=105, cd_thrust=100, cd_thrust_b=70,       # cooldown after an attack
    hit_cd=24,              # ticks between two counted core hits: the core's guard, 1.2 s after each LANDED hit (a hit inside it sparks and does nothing; blocked and body hits do not arm it).
                            # 0 = no guard at all: the guard code is not even generated
    backoff_hits=8,         # the monster disengages after this many landed core hits (not in the wrap phase)
    backoff_dist=30,        # blocks it retreats along the avenue (never beyond the avenue's far end, ARENA angel z; if it cannot, it sidesteps to the other side)
    backoff_min=10,         # less room than this to retreat: it sidesteps instead
    backoff_stagger=30,     # ticks of stagger (and of turning its back) before it walks off
    backoff_speed=0.45,     # blocks per tick while retreating
    backoff_cd=50,          # ticks after the retreat until it may attack again (the first thing it does is the eye beam, the player being far)
    backoff_hold=300,       # most ticks it holds its ground, barrier up, waiting for the player (it lets the barrier down after its first attack)
    near=12.5,              # blocks: from the giant's shoulders (22 up) to the core centre: the barrier cancels inside this
    reach_up=22.0,
    giant_inv=20,           # invulnerability ticks after a hit
    regen_wait=160, regen_every=20, regen_amt=2,
    speed_a=0.30, speed_b=0.42, wrap_speed=0.9,
    stand_off=17.0, thrust_range=24, beam_range=140,
    intro_ticks=500, intro_after_step=120,
    scale=16, step_height=2.6, move_speed=0.30, jump=1.0, gravity=0.12, safe_fall=48, reach_entity=18,
    reach_block=20, atk_dmg=20, atk_kb=2, kb_res=0.6,
    # ---- the features of the video preset, all OFF here (these keys change nothing in a `full` build)
    core_box=0.15,          # the core's interaction box edge as a fraction of the monster's height (4.5 blocks at height 30)
    near_box=0.0,           # > 0: a second, larger "near miss counts" interaction box around the core (edge as a fraction of the height); a click on it is a core hit
    visible=False,          # True: the two states made visible - a persistent bright octagon + dimmed core while shielded, a pulsing red core + halo while vulnerable -
                            #       and a feedback for every swing (flinch on a landed hit, ringing flare + counters on a blocked one, thud + core flash on a body hit);
                            #       the barrier coming down is marked (sound + flash).  Adds the scores #vuln #blk_n #blk_why #blk_tot #hit_n (README)
    beam_first=False,       # True: the first attack after a back-off is always the eye beam (while the giant is within beam_range)
)

VIDEO = dict(
    FULL,
    core_hp=42,             # hits to win (60 in `full`).  NOTE: the story's guide (s07) reads #ch against 60 / 58..59 / ..57 - see README "Scores for the story": use #hit_n instead
    crack_at=22,            # the core cracks with 22 hits left (20 hits into the fight)
    backoff_hits=9,         # a back-off every 9 landed hits (8 in `full`): after hits 9, 18, 27
    backoff_dist=20,        # it retreats 20 blocks (30): a 4-second walk back for the player
    backoff_cd=30,          # 1.5 s between its arrival and the first attack (50)
    backoff_speed=0.5,      # blocks per tick while retreating (0.45)
    cd_thrust=120, cd_thrust_b=90,      # arm thrust cooldown, phase A / B (100 / 70): the dodging costs a first-time player less
    intro_after_step=80,    # the Angel starts 4 s after the first steps (6 s): the walk-up is shorter
    hit_cd=0,               # NO guard on the core: every swing that connects while the giant is in reach and the barrier is down counts
    core_box=0.20,          # 6 blocks (4.5): a swing aimed at the core registers from farther off
    near_box=0.35,          # 10.5 blocks: a swing aimed at the chest registers as a core hit
    visible=True,
    beam_first=True,
    # --- the look of the two states and of the feedback (video only)
    shield_dist=6.0,        # blocks in front of the core, toward the giant's eyes, where the octagon stands
    shield_bar=0.9,         # thickness of the octagon's bars, blocks
    halo_small=3.6, halo_big=5.2, halo_period=20,   # the pulsing halo cubes round the vulnerable core: edge (blocks) at the dim and the bright half of the pulse, ticks per pulse
    dim_light=4,            # display brightness (0..15) of the dimmed core
    flinch_back=0.7, flinch_ticks=3,                # a landed hit throws the monster back this many blocks for this many ticks
    drop_pitch=1.8,         # the barrier-down cue: sfx.barrier played this high (the rising tone is at 1.0, a blocked swing's ring at 1.0)
    block_pitch=1.4,        # the ring of a swing blocked by the barrier
    crack_marks=(0.4, 0.8),     # crack progress: slivers of light 1 and 2 open at this fraction of the way to the crack (phase 1) and to the wrap (phase 2)
)

PRESETS = {"full": FULL, "video": VIDEO}
CFG = {}                    # filled by set_pace(); modules keep a reference to this dict, so it is updated in place
PACE = ""


def set_pace(name):
    """Selects the preset: fills CFG (in place) from PRESETS[name]."""
    global PACE
    if name not in PRESETS:
        raise SystemExit(f"unknown pace {name!r}: choose one of {', '.join(PRESETS)}")
    CFG.clear()
    CFG.update(PRESETS[name])
    PACE = name


set_pace(os.environ.get("ANGEL_PACE", "").strip().lower() or "video")

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
    G = C["hit_cd"] > 0              # the core guard exists (full); without it (video) none of its code is generated
    V = bool(C["visible"])           # video: the two visible states (persistent octagon + dimmed core / pulsing core + halo), a feedback for every kind of swing, the barrier-down cue
    FB = V
    NB = C["near_box"] > 0           # the second, larger "near miss counts" box (video)
    cbx = C["core_box"]              # the core's interaction box, fraction of the height

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
        "scoreboard players set #16 angel.fight 16",
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
    tag_giant = [
        "execute unless score #test angel.fight matches 1 run tag @a remove angel.giant",
        "execute if entity @s[type=minecraft:player] run tag @s add angel.giant",
        "execute unless entity @e[tag=angel.giant] run tag @a[limit=1] add angel.giant",
        "execute if entity @s[tag=angel.pending] run tag @s add angel.giant",
        "tag @e[tag=angel.pending] remove angel.pending",
        "execute as @e[tag=angel.giant] run function angel:fight/become_giant",
        "scoreboard players add #attempt angel.fight 1",
    ]
    init_scores = [
        sc("gh", C["giant_hp"]), sc("ch", C["core_hp"]), sc("phase", 0), sc("st", 0), sc("t", 0), sc("cd", 0),
        sc("ginv", 0), sc("gcalm", 0), sc("hitcd", 0), sc("cd09", 0), sc("steps", 0), sc("it", 0), sc("nav", 99),
        sc("t20", 0), sc("pt", 0), sc("gap", 0), sc("bt", C["beam_charge"]), sc("locked", 0), sc("sl", 30),
        sc("wt", C["wrap_ticks"]), sc("dmg", 0), sc("blocked1", 0), sc("destroy", 1),
        sc("bo", 0), sc("bar", 0), sc("barp", 0), sc("hold", 0), sc("hold_t", 0), sc("hb", 0), sc("blockcd", 0), sc("sparkcd", 0), sc("barsnd", 0), sc("wallt", 0),
        sc("wgo", 0), sc("wwait", 0), sc("wstage", 0), sc("shud", 0), sc("hbt", 0), sc("whits", 0),
    ]
    if not G:                                   # (full keeps #hitcd in the list; without a guard the score does not exist)
        init_scores.remove(sc("hitcd", 0))
    if V:
        # the scores of the video preset: vs (look applied: 0 none, 1 vulnerable, 2 shielded), vuln (1: a swing at the core counts), vp (pulse phase), ptcd (core-point
        # cooldown), fl (a flinch is out), blk_n / blk_why / blk_tot (blocked swings, see README), hit_n (landed core hits this attempt)
        init_scores += [sc("vs", 0), sc("vuln", 0), sc("vp", 0), sc("ptcd", 0), sc("fl", 0), sc("blk_n", 0), sc("blk_why", 0), sc("blk_tot", 0), sc("hit_n", 0),
                        sc("inreach", 0)]
    boss_init = [
        "bossbar set angel:fight/giant players @e[tag=angel.giant,type=minecraft:player]",
        "bossbar set angel:fight/angel players @e[tag=angel.giant,type=minecraft:player]",
        "bossbar set angel:fight/angel name {\"text\":\"ANGEL\",\"color\":\"red\"}",
        "bossbar set angel:fight/wrap players",
        "bossbar set angel:fight/giant visible true",
        "bossbar set angel:fight/angel visible true",
        "bossbar set angel:fight/wrap visible false",
        "bossbar set angel:fight/giant color green",
        "bossbar set angel:fight/wrap color red",
    ]
    put("start", [
        "# function angel:fight/start   (as the player, who has just arrived at city.launch_top)",
        "function angel:fight/stop_quiet",
    ] + tag_giant + init_scores + [
        sc("ck", 0),
        "scoreboard players reset * angel.barks",
        "data modify storage angel:fight q set value []",
        "data modify storage angel:fight played set value []",
        "kill @e[tag=angel.fight]",
        f'summon minecraft:marker {ox} {oy} {oz} {{Tags:["angel.fight","angel.origin"]}}',
        f"execute positioned {ax} {ay} {az} rotated 0 0 run function angel:angel/summon {{height:{FH}}}",
        "tag @e[tag=angel.mon] add angel.fight",
        "function angel:angel/core_stage {stage:0}",
    ] + boss_init + [
        "function angel:fight/bark {id:\"7_01\"}",
        "function angel:fight/bark {id:\"7_02\"}",
        sc("run", 1),
    ])
    # the CHECKPOINT start: after a loss once the core has cracked (#ck 1, set by core_crack), the fight resumes at the crack instead of at the launch:
    # the giant healed and put back where it stood when the core cracked, the monster summoned where it stood then, the core at its crack health
    # (phase 2, the hunched pause), the intro lines not repeated.  Phase sequence seen from outside: 5 (lost) -> 0 (run 0, about 3 s) -> 2 (-> 3 ...).
    put("start_ck", [
        "# function angel:fight/start_ck   (as the pending giant, from restart_ck_go)",
        "function angel:fight/stop_quiet",
    ] + tag_giant + init_scores + [
        sc("ck", 1), sc("steps", 1), sc("ch", C["crack_at"]), sc("phase", 1),
        "scoreboard players reset * angel.barks",
        ] + [f"scoreboard players set #7_{i:02d} angel.barks 1" for i in range(1, 9)] + [
        "data modify storage angel:fight q set value []",
        "data modify storage angel:fight played set value []",
        "kill @e[tag=angel.fight]",
        f'summon minecraft:marker {ox} {oy} {oz} {{Tags:["angel.fight","angel.origin"]}}',
        f'summon minecraft:marker {ox} {oy} {oz} {{Tags:["angel.fight","angel.ckpos"]}}',
        f"data modify entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos set value [{ox}d,{oy}d,{oz}d]",   # (inside the loaded chunks: x 0 would be an unloaded chunk)
        "execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[0] double 0.1 run scoreboard players get #ckgx angel.fight",
        "execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[1] double 0.1 run scoreboard players get #ckgy angel.fight",
        "execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[2] double 0.1 run scoreboard players get #ckgz angel.fight",
        "tp @e[tag=angel.giant] @e[type=minecraft:marker,tag=angel.ckpos,limit=1]",
        "execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[0] double 0.1 run scoreboard players get #ckmx angel.fight",
        "execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[1] double 0.1 run scoreboard players get #ckmy angel.fight",
        "execute store result entity @e[type=minecraft:marker,tag=angel.ckpos,limit=1] Pos[2] double 0.1 run scoreboard players get #ckmz angel.fight",
        f"execute at @e[type=minecraft:marker,tag=angel.ckpos,limit=1] rotated 0 0 run function angel:angel/summon {{height:{FH}}}",
        "tag @e[tag=angel.mon] add angel.fight",
        "kill @e[type=minecraft:marker,tag=angel.ckpos]",
        "rotate @e[type=minecraft:marker,tag=angel.root,limit=1] facing entity @e[tag=angel.giant,limit=1] feet",
        "function angel:angel/sync",
        "execute as @e[tag=angel.giant] at @s run rotate @s facing entity @e[type=minecraft:marker,tag=angel.root,limit=1] feet",
        "execute as @e[tag=angel.giant,type=minecraft:player] at @s run rotate @s ~ 20",
        "execute as @e[tag=angel.giant] run effect clear @s minecraft:blindness",
        "execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness",
    ] + boss_init + [
        sc("run", 1),
        "# the same state as the moment the core cracked (core_crack: phase 2, the hunched pause, barks 7.12 and 7.13)",
        "function angel:fight/core_crack",
    ])
    put("ck_save", [
        "# called when the core cracks: where the monster and the giant stand (x10, so they fit a score) for the checkpoint restart",
        sc("ck", 1),
        "execute store result score #ckmx angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[0] 10",
        "execute store result score #ckmy angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[1] 10",
        "execute store result score #ckmz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[2] 10",
        "execute store result score #ckgx angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[0] 10",
        "execute store result score #ckgy angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[1] 10",
        "execute store result score #ckgz angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[2] 10",
    ])
    put("stop_quiet", [
        "# cleans up everything of the fight except the player's scale",
        sc("run", 0), sc("phase", 0), sc("bar", 0), sc("hold", 0), sc("hb", 0),
    ] + ([sc("vs", 0), sc("vuln", 0), sc("fl", 0), "schedule clear angel:fight/flinch_back", "schedule clear angel:fight/shield_calm"] if V else []) + [
        "stopsound @a * angel:sfx.heartbeat", "stopsound @a * angel:sfx.beam_charge",
        "schedule clear angel:fight/fx_fade", "schedule clear angel:fight/fx_clear", "schedule clear angel:fight/restart_go", "schedule clear angel:fight/restart_ck_go",
        "stopsound @a * minecraft:entity.warden.heartbeat",
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
        sc("ck", 0),
    ])

    # ============================================================ barks (queue)
    ids = [f"7_{i:02d}" for i in range(1, 21)]
    put("bark", [
        "# function angel:fight/bark {id:\"7_04\"}: queues a line, once per attempt",
        "$execute if score #$(id) angel.barks matches 1 run return 0",
        "$scoreboard players set #$(id) angel.barks 1",
        "$data modify storage angel:fight q append value {id:\"$(id)\"}",
    ])
    put("bark_front", [
        "# like bark, but the line goes to the FRONT of the queue (the wrap's 7.14: the countdown waits for it)",
        "$execute if score #$(id) angel.barks matches 1 run return 0",
        "$scoreboard players set #$(id) angel.barks 1",
        "$data modify storage angel:fight q prepend value {id:\"$(id)\"}",
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
        "# the line has begun (the wrap's countdown waits for #began_7_14)",
        "$scoreboard players set #began_$(id) angel.barks 1",
        "data remove storage angel:fight q[0]",
        sc("gap", 10),
    ])
    lines = script_lines()
    for i in ids:
        real = os.path.join(pack_function_dir, "say", f"{i}.mcfunction")
        if os.path.isfile(real):
            # barks are pre-rendered and spoken by the game itself (instant, the same length every time): never cued to the voice bridge
            put(f"say/{i}", [f"function angel:say/file/{i}"])
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
    ] + (["execute if score #hitcd angel.fight matches 1.. run scoreboard players remove #hitcd angel.fight 1"] if G else []) + [
        "execute if score #cd09 angel.fight matches 1.. run scoreboard players remove #cd09 angel.fight 1",
        "execute if score #blockcd angel.fight matches 1.. run scoreboard players remove #blockcd angel.fight 1",
        "execute if score #sparkcd angel.fight matches 1.. run scoreboard players remove #sparkcd angel.fight 1",
        "execute if score #barsnd angel.fight matches 1.. run scoreboard players remove #barsnd angel.fight 1",
    ] + (["execute if score #ptcd angel.fight matches 1.. run scoreboard players remove #ptcd angel.fight 1"] if FB else []) + ([] if V else [
        "# the raised barrier (after a back-off) pulses as a wall of light",
        "execute if score #bar angel.fight matches 1 run scoreboard players add #barp angel.fight 1",
        "execute if score #barp angel.fight matches 24.. run function angel:fight/bar_pulse",
    ]) + [
        "scoreboard players add #gcalm angel.fight 1",
        "scoreboard players add #t20 angel.fight 1",
        "execute if score #t20 angel.fight matches 20.. run function angel:fight/second",
        "execute store result bossbar angel:fight/giant value run scoreboard players get #gh angel.fight",
        "execute store result bossbar angel:fight/angel value run scoreboard players get #ch angel.fight",
        "execute if score #steps angel.fight matches 0 at @e[type=minecraft:marker,tag=angel.origin,limit=1] unless entity @e[tag=angel.giant,distance=..8] run function angel:fight/first_steps",
    ] + ([
        "# the two states, drawn: the octagon of light and the dimmed core while shielded, the burning core and its halo while vulnerable (and #vuln)",
        "function angel:fight/vis_tick",
    ] if V else [
        "# the barrier, drawn in light while the giant is too far to cancel it",
        "execute if score #wallt angel.fight matches 1.. run scoreboard players remove #wallt angel.fight 1",
        "execute unless score #wallt angel.fight matches 1.. run function angel:fight/wall_hint",
    ]))
    put("second", [
        sc("t20", 0),
        f"execute if score #gcalm angel.fight matches {C['regen_wait']}.. if score #gh angel.fight matches ..{C['giant_hp'] - 1} run scoreboard players add #gh angel.fight {C['regen_amt']}",
        f"execute if score #gh angel.fight matches {C['giant_hp'] + 1}.. run scoreboard players set #gh angel.fight {C['giant_hp']}",
        "execute if score #gh angel.fight matches 60.. run bossbar set angel:fight/giant color green",
        "execute if score #gh angel.fight matches 30..59 run bossbar set angel:fight/giant color yellow",
        "execute if score #gh angel.fight matches ..29 run bossbar set angel:fight/giant color red",
        "# low health: the giant's heartbeat (a 10 s file: replayed when it has run out, cut when health comes back)",
        "execute if score #hb angel.fight matches 1.. run scoreboard players remove #hb angel.fight 1",
        f"execute if score #gh angel.fight matches ..{C['giant_hp'] // 4} unless score #hb angel.fight matches 1.. unless score #phase angel.fight matches 3 run function angel:fight/heartbeat",
        f"execute if score #gh angel.fight matches {C['giant_hp'] // 4 + 1}.. if score #hb angel.fight matches 1.. run function angel:fight/heartbeat_stop",
    ])
    put("heartbeat", [
        sc("hb", 10),
        "execute at @e[tag=angel.giant,limit=1] run playsound angel:sfx.heartbeat master @a ~ ~ ~ 2 1 0.6",
    ])
    put("heartbeat_stop", [sc("hb", 0), "stopsound @a * angel:sfx.heartbeat"])
    put("first_steps", [sc("steps", 1), 'function angel:fight/bark {id:"7_03"}'])

    # ============================================================ hurting the giant
    put("hurt", [
        "# #dmg angel.fight = points. Shared invulnerability window; the real player also takes a token hit for the flash",
        "execute if score #phase angel.fight matches 4.. run return 0",
        "execute if score #ginv angel.fight matches 1.. run return 0",
        "scoreboard players operation #gh angel.fight -= #dmg angel.fight",
        sc("ginv", C["giant_inv"]), sc("gcalm", 0),
        "execute at @e[tag=angel.giant,limit=1] run playsound angel:sfx.giant_hit hostile @a ~ ~ ~ 2 1",
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
    ] + (["execute as @e[type=minecraft:interaction,tag=angel.nearbox] if data entity @s attack run function angel:fight/near_hit"] if NB else []))
    if NB:
        put("near_hit", [
            "# a swing that hit the larger 'near miss' box round the core is a swing at the core (the core box lies inside it, so this box is hit first)",
            "data remove entity @s attack",
            "execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run function angel:fight/core_hit",
        ])
    cy = FH * cbx / 2           # the core's centre above the foot of its hit box
    if not V:
        put("core_hit", [
            "# one click on the core box.  Three outcomes: landed (in reach, core not guarded), guarded (in reach, 1.2 s after a landed hit: sparks, a dull clank,",
            "# nothing else) and blocked (beyond arm's length, or the barrier is up after a back-off: the octagon of light).",
            "# Only a LANDED hit arms the guard (#hitcd); blocked, guarded and body hits never do.",
            "data remove entity @s attack",
            "execute if score #phase angel.fight matches 4.. run return 0",
            "# the wrap (phase 3): no guard, no reach, no barrier - every click that connects counts",
            "execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit",
            "execute if score #bar angel.fight matches 1 run return run function angel:fight/core_blocked",
            f"# the giant's reach point is {C['reach_up']} up; the box's foot is half its height below the core centre",
            f"execute store success score #inreach angel.fight positioned ~ ~-{C['reach_up'] - cy:.2f} ~ if entity @e[tag=angel.giant,distance=..{C['near']}]",
            "execute if score #inreach angel.fight matches 1 if score #hitcd angel.fight matches 1.. run return run function angel:fight/core_guarded",
            "execute if score #inreach angel.fight matches 1 run return run function angel:fight/core_land",
            "function angel:fight/core_blocked",
        ])
        put("core_blocked", [
            "# beyond arm's length (or the barrier is raised): the hit stops on the wall of light.  Rate-limited so that flailing is not a wall of noise",
            "execute if score #blockcd angel.fight matches 1.. run return 0",
            sc("blockcd", 6),
            "execute if score #blocked1 angel.fight matches 0 run function angel:fight/first_blocked",
            sc("wallt", 30),
            f"execute positioned ~ {cy:.2f} ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_flash",
        ])
        put("core_guarded", [
            "# a hit on the core inside its guard: a few sparks and a dull clank.  No damage, no counter, does not re-arm the guard",
            "scoreboard players add #guarded angel.fight 1",
            "execute if score #sparkcd angel.fight matches 1.. run return 0",
            sc("sparkcd", 4),
            f"particle minecraft:electric_spark ~ ~{cy:.2f} ~ 1 1 1 0.3 14 force",
            f"particle minecraft:smoke ~ ~{cy:.2f} ~ 0.6 0.6 0.6 0.01 5 force",
            # a dull metal clank (a vanilla stand-in: angel:sfx.barrier is a 3.6 s tone, which would turn a click into a note).  Volume 2.2: the
            # server only sends a playsound to players within 16 x volume blocks of the origin, measured from the player's FEET (core ~ 22 away)
            f"playsound minecraft:block.iron_trapdoor.close hostile @a ~ ~{cy:.2f} ~ 2.2 0.5",
        ])
    else:
        # ---- the video rules.  One swing that hit the core box (or the box round it) has exactly two outcomes, decided by ONE test, #vuln (kept by vis_state):
        # the barrier is down AND the giant is within arm's length -> LANDED, and nothing else can swallow it (there is no guard); otherwise BLOCKED.
        put("core_hit", [
            "# one swing that hit the core (the core box, or the larger box round it).  Two outcomes, judged by ONE test (#vuln, see vis_state): the barrier is down and the",
            "# giant is within arm's length -> LANDED (it always counts: there is no guard); otherwise BLOCKED (the octagon flares, a ringing tone, #blk_n / #blk_why).",
            "# The wrap (phase 3) is separate: every swing that connects counts.",
            "data remove entity @s attack",
            "execute if score #phase angel.fight matches 4.. run return 0",
            "execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit",
            "function angel:fight/vis_state",
            "execute if score #vuln angel.fight matches 1 run return run function angel:fight/core_land",
            "function angel:fight/core_blocked",
        ])
        put("core_blocked", [
            "# a swing the barrier stopped: the giant is too far (#blk_why 1) or the back-off barrier is up (#blk_why 2).  Every one is counted (#blk_n since the last landed hit /",
            "# barrier change, #blk_tot in all); the effects are rate-limited so that flailing is not a wall of noise",
            "scoreboard players add #blk_n angel.fight 1",
            "scoreboard players add #blk_tot angel.fight 1",
            "execute if score #bar angel.fight matches 1 run scoreboard players set #blk_why angel.fight 2",
            "execute unless score #bar angel.fight matches 1 run scoreboard players set #blk_why angel.fight 1",
            "execute if score #blockcd angel.fight matches 1.. run return 0",
            sc("blockcd", 6),
            "execute if score #blocked1 angel.fight matches 0 run function angel:fight/first_blocked",
            "# the octagon flares white and rings (at the core box's foot, the tone is a 3.6 s sound: at most one per 2 s)",
            "function angel:fight/shield_flare",
            "execute unless score #barsnd angel.fight matches 1.. run function angel:fight/barrier_tone",
        ])
    put("first_blocked", [sc("blocked1", 1), 'function angel:fight/bark {id:"7_06"}', 'function angel:fight/bark {id:"7_07"}',
                          'function angel:fight/bark {id:"7_08"}'])
    if not V:
        put("core_land", [
            "# within arm's length the fields cancel and the hit lands on the core.  This (and only this) arms the core's guard",
        ] + ([sc("hitcd", C["hit_cd"])] if G else []) + [
            "scoreboard players remove #ch angel.fight 1",
            "execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0",
            f"particle minecraft:flash{{color:[1.0,0.55,0.45,1.0]}} ~ ~{cy:.2f} ~ 0 0 0 0 1 force",
            f"particle minecraft:crit ~ ~{cy:.2f} ~ 1.2 1.2 1.2 0.4 30 force",
            f"particle minecraft:dust{{color:[1.0,0.1,0.1],scale:2.5}} ~ ~{cy:.2f} ~ 1.4 1.4 1.4 0 24 force",
            "playsound angel:sfx.giant_punch hostile @a ~ ~ ~ 3 1",
            'function angel:fight/bark {id:"7_08"}',
            "# back-off: every backoff_hits landed hits (the wrap phase excluded) the monster disengages",
            "execute if score #phase angel.fight matches 1..2 run scoreboard players add #bo angel.fight 1",
            "execute if score #st angel.fight matches 3 run function angel:fight/begin_stagger",
            f"execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..{C['crack_at']} run function angel:fight/core_crack",
            f"execute if score #phase angel.fight matches 1..2 if score #ch angel.fight matches ..{C['wrap_at']} run function angel:fight/wrap_start",
            f"execute if score #phase angel.fight matches 1..2 if score #bo angel.fight matches {C['backoff_hits']}.. if score #ch angel.fight matches 1.. run function angel:fight/backoff_check",
        ])
    else:
        # crack progress: in phase 1 the slivers of light 1 and 2 open at crack_marks of the way to the crack, in phase 2 at the same fractions of the way to the wrap
        # (the crack and core_stage_1 close them again); the wrap's own cracks open 1 to 4 at wrap_crack_hits hits left
        span1, span2 = C["core_hp"] - C["crack_at"], C["crack_at"] - C["wrap_at"]
        m1, m2 = C["crack_marks"]
        t1, t2 = C["core_hp"] - math.ceil(m1 * span1), C["core_hp"] - math.ceil(m2 * span1)
        u1, u2 = C["crack_at"] - math.ceil(m1 * span2), C["crack_at"] - math.ceil(m2 * span2)
        put("core_land", [
            "# a swing that connects while the barrier is down and the giant is within arm's length.  It ALWAYS counts: there is no guard, nothing else gates it",
            "scoreboard players remove #ch angel.fight 1",
            "execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0",
            "scoreboard players add #hit_n angel.fight 1",
            sc("blk_n", 0), sc("blk_why", 0),
            f"particle minecraft:flash{{color:[1.0,0.55,0.45,1.0]}} ~ ~{cy:.2f} ~ 0 0 0 0 1 force",
            f"particle minecraft:crit ~ ~{cy:.2f} ~ 1.2 1.2 1.2 0.4 30 force",
            f"particle minecraft:dust{{color:[1.0,0.1,0.1],scale:2.5}} ~ ~{cy:.2f} ~ 1.4 1.4 1.4 0 24 force",
            "playsound angel:sfx.giant_punch hostile @a ~ ~ ~ 3 1",
            'function angel:fight/bark {id:"7_08"}',
            "# crack progress (slivers of light across the core)",
            f"execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..{t1} run function angel:angel/core_crack_1",
            f"execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..{t2} run function angel:angel/core_crack_2",
            f"execute if score #phase angel.fight matches 2 if score #ch angel.fight matches ..{u1} run function angel:angel/core_crack_1",
            f"execute if score #phase angel.fight matches 2 if score #ch angel.fight matches ..{u2} run function angel:angel/core_crack_2",
            "# back-off: every backoff_hits landed hits (the wrap phase excluded) the monster disengages",
            "execute if score #phase angel.fight matches 1..2 run scoreboard players add #bo angel.fight 1",
            "execute if score #st angel.fight matches 3 run function angel:fight/begin_stagger",
            f"execute if score #phase angel.fight matches 1 if score #ch angel.fight matches ..{C['crack_at']} run function angel:fight/core_crack",
            f"execute if score #phase angel.fight matches 1..2 if score #ch angel.fight matches ..{C['wrap_at']} run function angel:fight/wrap_start",
            f"execute if score #phase angel.fight matches 1..2 if score #bo angel.fight matches {C['backoff_hits']}.. if score #ch angel.fight matches 1.. run function angel:fight/backoff_check",
            "# the monster flinches (not when it is staggering, thrown back, retreating or wrapped: its own motion says it)",
            "execute if score #st angel.fight matches 0..4 run function angel:fight/flinch",
        ])
        put("flinch", [
            "# a landed hit throws the monster back flinch_back blocks for flinch_ticks ticks (the parts glide: teleport_duration 2).  Not twice at once, not while it is wrapped",
            "execute if score #fl angel.fight matches 1 run return 0",
            "execute if score #phase angel.fight matches 3.. run return 0",
            sc("fl", 1),
            f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s run tp @s ^ ^ ^-{C['flinch_back']}",
            "function angel:angel/sync",
            f"schedule function angel:fight/flinch_back {C['flinch_ticks']}t",
        ])
        put("flinch_back", [
            sc("fl", 0),
            "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
            "execute if score #phase angel.fight matches 3.. run return 0",
            "# (a back-off that began meanwhile moves it by itself)",
            "execute if score #st angel.fight matches 9..10 run return 0",
            f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s run tp @s ^ ^ ^{C['flinch_back']}",
            "function angel:angel/sync",
        ])
    # ---- the wrap's hit: the same for the core box and the (big) body box
    cyw = FH * cbx / 2
    put("wrap_hit", [
        "# a landed hit while the monster is wrapped round the giant (phase 3).  No guard, no reach: it always counts.  Feedback: the core flashes and cracks further",
        "# (crack 1..4 as the hits left fall), the wrap shudders (pose wrap_hit), sfx.giant_punch, the countdown bar jumps back (wrap_bonus), the hits left on the action bar",
        "execute if score #phase angel.fight matches 4.. run return 0",
        "scoreboard players remove #ch angel.fight 1",
        "execute if score #ch angel.fight matches ..-1 run scoreboard players set #ch angel.fight 0",
        "scoreboard players add #whits angel.fight 1",
        ] + (["scoreboard players add #hit_n angel.fight 1"] if V else []) + [
        f"execute if score #st angel.fight matches 7 run scoreboard players add #wt angel.fight {C['wrap_bonus']}",
        f"execute if score #wt angel.fight matches {C['wrap_ticks'] + 1}.. run scoreboard players set #wt angel.fight {C['wrap_ticks']}",
        "execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run function angel:fight/wrap_hit_fx",
        "execute if score #st angel.fight matches 7 run scoreboard players set #shud angel.fight 4",
        "execute if score #st angel.fight matches 7 run function angel:angel/pose_wrap_hit",
        ] + [f"execute if score #ch angel.fight matches ..{h} run function angel:angel/core_crack_{i + 1}" for i, h in enumerate(C["wrap_crack_hits"])] + [
        'execute as @e[tag=angel.giant,type=minecraft:player] run title @s actionbar [{"text":"CORE  ","color":"red","bold":true},{"score":{"name":"#ch","objective":"angel.fight"},"color":"white","bold":true},{"text":"  to go","color":"gray"}]',
        "execute if score #ch angel.fight matches ..0 run function angel:fight/won_start",
    ])
    put("wrap_hit_fx", [
        "# at the core box's foot: its centre is cy up",
        f"particle minecraft:flash{{color:[1.0,0.55,0.45,1.0]}} ~ ~{cyw:.2f} ~ 0 0 0 0 1 force",
        f"particle minecraft:crit ~ ~{cyw:.2f} ~ 1.6 1.6 1.6 0.5 40 force",
        f"particle minecraft:electric_spark ~ ~{cyw:.2f} ~ 2.2 2.2 2.2 0.5 30 force",
        f"particle minecraft:dust{{color:[1.0,0.1,0.1],scale:3.0}} ~ ~{cyw:.2f} ~ 1.8 1.8 1.8 0 30 force",
        f"particle minecraft:end_rod ~ ~{cyw:.2f} ~ 1.2 1.2 1.2 0.35 14 force",
        "playsound angel:sfx.giant_punch hostile @a ~ ~ ~ 3 1",
    ])
    if not V:
        put("body_hit", [
            "# the body box only sparks: no damage, and it does not arm the core's guard.  (While the monster is wrapped round the giant it is the big box and counts as a core hit)",
            "data remove entity @s attack",
            "execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit",
            "execute if score #sparkcd angel.fight matches 1.. run return 0",
            sc("sparkcd", 4),
            "particle minecraft:crit ~ ~ ~ 1 1 1 0.2 6 force",
            "particle minecraft:electric_spark ~ ~ ~ 1.5 1.5 1.5 0.2 8 force",
            "playsound minecraft:block.anvil.hit hostile @a ~ ~ ~ 2 1.8",
            'function angel:fight/bark {id:"7_08"}',
        ])
    else:
        bc = gen_angel.BODY_H * FH / 2           # the body box's centre above its foot
        put("body_hit", [
            "# the body box: no damage.  Small sparks and a dull thud say 'you hit it, but not there', and the core flashes once to point at the place to hit.",
            "# (While the monster is wrapped round the giant it is the big box and counts as a core hit)",
            "data remove entity @s attack",
            "execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit",
            "execute if score #sparkcd angel.fight matches 1.. run return 0",
            sc("sparkcd", 4),
            f"particle minecraft:crit ~ ~{bc:.2f} ~ 0.8 0.8 0.8 0.2 5 force",
            f"particle minecraft:electric_spark ~ ~{bc:.2f} ~ 1.0 1.0 1.0 0.15 6 force",
            # a dull thud, low (a vanilla sound; volume 2.5 so that it reaches a player whose feet are ~20 blocks from the body box)
            f"playsound minecraft:block.stone.hit hostile @a ~ ~{bc:.2f} ~ 2.5 0.5",
            'function angel:fight/bark {id:"7_08"}',
            "execute if score #ptcd angel.fight matches 0 run function angel:fight/core_point",
        ])
        put("core_point", [
            "# the core flashes once (at most one per 0.7 s) so that a swing at the body points him at the place to hit",
            sc("ptcd", 14),
            "execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~%.2f ~ run function angel:fight/core_point_at" % cy,
        ])
        put("core_point_at", [
            "particle minecraft:flash{color:[1.0,0.35,0.25,1.0]} ~ ~ ~ 0 0 0 0 1 force",
            "particle minecraft:end_rod ~ ~ ~ 1.4 1.4 1.4 0.12 14 force",
            "particle minecraft:dust{color:[1.0,0.1,0.1],scale:3.0} ~ ~ ~ 1.6 1.6 1.6 0 14 force",
        ])

    # ============================================================ barrier drawing
    R = 0.45 * FH
    ap = R * 0.9239
    wall_hint = ["# faint octagon of light, on the monster's side, facing the giant (every 10 ticks while the giant is far)",
                 "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
                 "execute if score #phase angel.fight matches 3.. run return 0",
                 sc("wallt", 10),
                 "# (with the barrier raised after a back-off it is drawn at any distance)",
                 "execute unless score #bar angel.fight matches 1 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~2.25 ~ unless entity @e[tag=angel.giant,distance=..60] run return 0",
                 f"execute unless score #bar angel.fight matches 1 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~{cy:.2f} ~ positioned ~ ~-{C['reach_up']} ~ if entity @e[tag=angel.giant,distance=..{C['near']}] run return 0",
                 f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~{cy:.2f} ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_dots"]
    put("wall_hint", wall_hint)
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

    wall = ["# the wall of light (no sound): 8 bars + 2 translucent squares, facing the giant"]
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
    put("wall_draw", wall)
    put("barrier_tone", [sc("barsnd", 40), "playsound angel:sfx.barrier hostile @a ~ ~ ~ 3 1"])
    put("wall_flash", ["# a hit stopped by the barrier: the octagon of light and its tone (the tone is a 3.6 s sound: at most one per 2 s, however hard the player flails)",
                       "execute unless score #barsnd angel.fight matches 1.. run function angel:fight/barrier_tone",
                       "function angel:fight/wall_draw"])
    put("bar_pulse", ["# while the barrier is up after a back-off, the octagon flares every 1.2 s (no sound)",
                      sc("barp", 0),
                      "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
                      f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~{cy:.2f} ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_draw"])
    put("fx_fade", ["execute as @e[type=minecraft:block_display,tag=angel.flash] run data merge entity @s {start_interpolation:0,interpolation_duration:9,transformation:{scale:[0f,0f,0f]}}"])
    put("fx_clear", ["kill @e[type=minecraft:block_display,tag=angel.flash]"])

    # ============================================================ the two visible states (video)
    # VULNERABLE (#vuln 1): the barrier is down and the giant is within arm's length (or the wrap): the core burns bright red, pulsing, in a soft halo, nothing in front of it.
    # SHIELDED  (#vuln 0): the back-off barrier is up, or the giant is too far: the core is dimmed and a bright octagon of light stands in front of the monster.
    # No third state.  vis_state computes #vuln (the same test core_hit judges a swing by) and switches the look when it changes; vis_tick (every tick) also keeps
    # the octagon / the halo on the core and pulses the halo.
    if V:
        for k in ("wall_hint", "wall_dots", "wall_draw", "barrier_tone", "wall_flash", "bar_pulse"):
            F.pop(k, None)             # the faint dotted octagon and its once-per-hit flash are replaced by the persistent one below
        D6 = C["shield_dist"]
        RS = 0.45 * FH                 # radius of the octagon (blocks)
        core_sel = "@e[type=minecraft:interaction,tag=angel.core,limit=1]"
        giant1 = "@e[tag=angel.giant,limit=1]"
        at_shield = f"positioned ~ ~{cy:.2f} ~ facing entity {giant1} eyes positioned ^ ^ ^{D6:g}"          # (the octagon's centre, from the core box's foot)
        put("vis_state", [
            "# the one test: can a swing at the core count right now?  #vuln 1 = the barrier is down AND the giant is within arm's length of the core (or the monster is wrapped).",
            "# On a change the look is switched (vis_hot / vis_dim).",
            "execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0",
            "execute if score #phase angel.fight matches 4.. run return 0",
            sc("inreach", 0),
            f"execute as {core_sel} at @s positioned ~ ~-{C['reach_up'] - cy:.2f} ~ store success score #inreach angel.fight if entity @e[tag=angel.giant,distance=..{C['near']}]",
            sc("vuln", 0),
            "execute if score #inreach angel.fight matches 1 if score #bar angel.fight matches 0 run scoreboard players set #vuln angel.fight 1",
            "execute if score #phase angel.fight matches 3 run scoreboard players set #vuln angel.fight 1",
            "execute if score #vuln angel.fight matches 1 unless score #vs angel.fight matches 1 run function angel:fight/vis_hot",
            "execute if score #vuln angel.fight matches 0 unless score #vs angel.fight matches 2 run function angel:fight/vis_dim",
        ])
        put("vis_tick", [
            "function angel:fight/vis_state",
            "execute if score #vs angel.fight matches 1 run function angel:fight/hot_tick",
            "execute if score #vs angel.fight matches 2 run function angel:fight/shield_follow",
        ])
        put("vis_off", [
            "# the fight is over (won or lost): nothing of either state is left standing",
            "kill @e[type=minecraft:block_display,tag=angel.shield]", "kill @e[type=minecraft:block_display,tag=angel.hot]",
            sc("vs", 0), sc("vuln", 0),
        ])
        cb = "execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s"
        hot_b = "{block:15,sky:15}"
        dim_b = "{block:%d,sky:%d}" % (C["dim_light"], C["dim_light"])
        # ---- the halo: two cubes of red glass (one turned 45 degrees about the vertical) that breathe between halo_small and halo_big
        hs, hb, per = C["halo_small"], C["halo_big"], C["halo_period"]

        def hot_tr(s, turned):
            h = s / 2
            return (-h * math.sqrt(2), -h, 0.0) if turned else (-h, -h, -h)

        def hot_summon(turned):
            tr = hot_tr(hs, turned)
            q = "0f,0.3827f,0f,0.9239f" if turned else "0f,0f,0f,1f"
            return (f'summon minecraft:block_display ~ ~ ~ {{Tags:["angel.fight","angel.hot","angel.hot{"b" if turned else "a"}"],block_state:"{model.VEIL}",view_range:16f,'
                    f'interpolation_duration:{per // 2},teleport_duration:2,brightness:{hot_b},'
                    f'transformation:{{translation:[{tr[0]:.3f}f,{tr[1]:.3f}f,{tr[2]:.3f}f],left_rotation:[{q}],scale:[{hs:.3f}f,{hs:.3f}f,{hs:.3f}f],right_rotation:[0f,0f,0f,1f]}}}}')

        def hot_merge(s, turned):
            tr = hot_tr(s, turned)
            return (f'execute as @e[type=minecraft:block_display,tag=angel.hot{"b" if turned else "a"}] run data merge entity @s {{start_interpolation:0,interpolation_duration:{per // 2},'
                    f'transformation:{{translation:[{tr[0]:.3f}f,{tr[1]:.3f}f,{tr[2]:.3f}f],scale:[{s:.3f}f,{s:.3f}f,{s:.3f}f]}}}}')
        put("vis_hot", [
            "# VULNERABLE: the core burns (stage block: whole = red concrete, cracked = magma), full bright; its glow strips and veil are back; a halo of red glass pulses round it; no octagon",
            sc("vs", 1), sc("vp", 0), sc("blk_n", 0), sc("blk_why", 0),
            "kill @e[type=minecraft:block_display,tag=angel.shield]",
            f'execute if score #phase angel.fight matches ..1 {cb[len("execute "):]} {{block_state:"{model.CORE}",brightness:{hot_b}}}',
            f'execute if score #phase angel.fight matches 2.. {cb[len("execute "):]} {{block_state:"{model.CORE_CRACKED}",brightness:{hot_b}}}',
            'execute as @e[type=minecraft:block_display,tag=angel.halo] run data merge entity @s {block_state:"minecraft:red_stained_glass"}',
            f'execute as @e[type=minecraft:block_display,tag=angel.coreglow] run data merge entity @s {{block_state:"{model.GLOW}",brightness:{hot_b}}}',
            f'execute as @e[type=minecraft:block_display,tag=angel.veil] run data merge entity @s {{block_state:"{model.VEIL}"}}',
            "kill @e[type=minecraft:block_display,tag=angel.hot]",
            f"execute as {core_sel} at @s positioned ~ ~{cy:.2f} ~ run function angel:fight/hot_make",
        ])
        put("hot_make", [hot_summon(False), hot_summon(True)])
        put("hot_tick", [
            "# follows the core and breathes (a pulse every halo_period ticks: the cubes grow to halo_big over half of it, shrink back over the other half)",
            f"execute as {core_sel} at @s positioned ~ ~{cy:.2f} ~ run tp @e[type=minecraft:block_display,tag=angel.hot] ~ ~ ~",
            "scoreboard players add #vp angel.fight 1",
            "execute if score #vp angel.fight matches 1 run function angel:fight/hot_big",
            f"execute if score #vp angel.fight matches {per // 2 + 1} run function angel:fight/hot_small",
            f"execute if score #vp angel.fight matches {per}.. run scoreboard players set #vp angel.fight 0",
        ])
        put("hot_big", [hot_merge(hb, False), hot_merge(hb, True),
                        f"execute as {core_sel} at @s positioned ~ ~{cy:.2f} ~ run particle minecraft:dust{{color:[1.0,0.1,0.1],scale:3.0}} ~ ~ ~ 1.8 1.8 1.8 0 8 force"])
        put("hot_small", [hot_merge(hs, False), hot_merge(hs, True)])
        put("vis_dim", [
            "# SHIELDED: the core is dimmed (dull terracotta, low light), the glow strips and veil are out, the halo is gone, and the octagon of light stands in front of the monster",
            sc("vs", 2),
            "kill @e[type=minecraft:block_display,tag=angel.hot]",
            f'{cb} {{block_state:"minecraft:red_terracotta",brightness:{dim_b}}}',
            'execute as @e[type=minecraft:block_display,tag=angel.halo] run data merge entity @s {block_state:"minecraft:gray_stained_glass"}',
            f'execute as @e[type=minecraft:block_display,tag=angel.coreglow] run data merge entity @s {{block_state:"minecraft:red_terracotta",brightness:{dim_b}}}',
            'execute as @e[type=minecraft:block_display,tag=angel.veil] run data merge entity @s {block_state:"minecraft:air"}',
            "kill @e[type=minecraft:block_display,tag=angel.shield]",
            f"execute as {core_sel} at @s {at_shield} run function angel:fight/shield_make",
        ])
        # ---- the octagon: 8 bars + 2 translucent squares (as the old flash), but PERSISTENT (tag angel.shield) and kept on the core by shield_follow
        def sdisp(block, tr, rot, sc3, kind):
            return (f'summon minecraft:block_display ~ ~ ~ {{Tags:["angel.fight","angel.shield","{kind}"],block_state:"{block}",view_range:16f,interpolation_duration:0,teleport_duration:2,'
                    f'brightness:{{block:15,sky:15}},transformation:{{translation:[{tr[0]:.3f}f,{tr[1]:.3f}f,{tr[2]:.3f}f],left_rotation:[0f,0f,{math.sin(rot / 2):.4f}f,{math.cos(rot / 2):.4f}f],'
                    f'scale:[{sc3[0]:.3f}f,{sc3[1]:.3f}f,{sc3[2]:.3f}f],right_rotation:[0f,0f,0f,1f]}}}}')
        apS = RS * 0.9239
        s_edgeS = 2 * RS * math.sin(math.pi / 8)
        thS = C["shield_bar"]
        sh = ["# the octagon of light: 8 bars + 2 translucent squares in the plane facing the giant; persistent until the state changes"]
        for i in range(8):
            a_ = math.radians(45 * i)
            c_ = (apS * math.cos(a_), apS * math.sin(a_))
            sz = (thS, s_edgeS, thS)
            h_ = (sz[0] / 2, sz[1] / 2, sz[2] / 2)
            tx = c_[0] - (math.cos(a_) * h_[0] - math.sin(a_) * h_[1])
            ty = c_[1] - (math.sin(a_) * h_[0] + math.cos(a_) * h_[1])
            sh.append(sdisp("minecraft:orange_concrete", (tx, ty, -h_[2]), a_, sz, "angel.sbar"))
        hhS = 0.7 * RS
        for rot_deg in (0, 45):
            a_ = math.radians(rot_deg)
            sz = (2 * hhS, 2 * hhS, 0.2)
            h_ = (hhS, hhS, 0.1)
            tx = -(math.cos(a_) * h_[0] - math.sin(a_) * h_[1])
            ty = -(math.sin(a_) * h_[0] + math.cos(a_) * h_[1])
            sh.append(sdisp("minecraft:orange_stained_glass", (tx, ty, -0.1), a_, sz, "angel.sfill"))
        sh.append("tp @e[type=minecraft:block_display,tag=angel.shield] ~ ~ ~ ~ ~")
        put("shield_make", sh)
        put("shield_follow", [f"execute as {core_sel} at @s {at_shield} run tp @e[type=minecraft:block_display,tag=angel.shield] ~ ~ ~ ~ ~"])
        put("shield_flare", [
            "# a swing hit the barrier (or it just went up / down): the octagon flares white for 3 ticks, with a burst of light",
            "execute unless entity @e[type=minecraft:block_display,tag=angel.sbar,limit=1] run return 0",
            'execute as @e[type=minecraft:block_display,tag=angel.sbar] run data merge entity @s {block_state:"minecraft:white_concrete"}',
            'execute as @e[type=minecraft:block_display,tag=angel.sfill] run data merge entity @s {block_state:"minecraft:white_stained_glass"}',
            f"execute as {core_sel} at @s {at_shield} run function angel:fight/shield_flare_fx",
            "schedule function angel:fight/shield_calm 3t",
        ])
        put("shield_flare_fx", [
            "particle minecraft:flash{color:[1.0,0.7,0.3,1.0]} ~ ~ ~ 0 0 0 0 1 force",
            "particle minecraft:end_rod ~ ~ ~ 5 5 5 0.25 36 force",
            "particle minecraft:electric_spark ~ ~ ~ 6 6 6 0.4 30 force",
        ])
        put("shield_calm", [
            'execute as @e[type=minecraft:block_display,tag=angel.sbar] run data merge entity @s {block_state:"minecraft:orange_concrete"}',
            'execute as @e[type=minecraft:block_display,tag=angel.sfill] run data merge entity @s {block_state:"minecraft:orange_stained_glass"}',
        ])
        put("barrier_tone", [sc("barsnd", 40), f"playsound angel:sfx.barrier hostile @a ~ ~ ~ 3 {C['block_pitch']:g}"])
        put("barrier_up", [sc("barsnd", 40), "# the barrier goes up (a back-off begins): the rising tone, lower than a blocked swing's ring and far lower than the drop cue",
                           "playsound angel:sfx.barrier hostile @a ~ ~ ~ 3 1"])
        put("drop_cue", [
            "# at the core box's foot: the barrier of a back-off comes down.  A high rising tone, a bright chime, a flash and a burst of light - 'you can hit it again'",
            "scoreboard players add #drops angel.fight 1",      # (a counter for the selftest: how often the cue ran)
            f"playsound angel:sfx.barrier hostile @a ~ ~ ~ 4 {C['drop_pitch']:g}",
            "playsound minecraft:block.beacon.activate hostile @a ~ ~ ~ 4 1.5",
            f"particle minecraft:flash{{color:[0.6,0.9,1.0,1.0]}} ~ ~{cy:.2f} ~ 0 0 0 0 1 force",
            f"particle minecraft:end_rod ~ ~{cy:.2f} ~ 3 3 3 0.2 40 force",
        ])

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
           "playsound angel:sfx.cross master @a ~ ~ ~ 8 1",
           "playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 12 0.5",
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
        "execute if score #st angel.fight matches 9 run function angel:fight/st_bo_stagger",
        "execute if score #st angel.fight matches 10 run function angel:fight/st_bo_retreat",
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
        "# (holding its ground after a back-off: it does not advance)",
        "execute if score #nav angel.fight matches 10.. unless score #hold angel.fight matches 1 run function angel:fight/nav",
        "execute unless score #walking angel.mon matches 1 if score #odd angel.fight matches 0 run function angel:fight/face_giant",
        "execute if score #cd angel.fight matches ..0 run function angel:fight/choose",
        "execute if score #hold angel.fight matches 1 run function angel:fight/hold_tick",
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
    put("choose", ([
        "# the first attack after a back-off (it is holding its ground, barrier up) is always the eye beam, wherever the giant stands: the player must meet the beam",
        f"execute if score #hold angel.fight matches 1 as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..{C['beam_range']}] run return run function angel:fight/begin_beam",
    ] if C["beam_first"] else []) + [
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
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound angel:sfx.beam_charge hostile @a ~ ~ ~ 8 1",
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
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound angel:sfx.beam_fire hostile @a ~ ~ ~ 9 1",
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
        "execute if score #hold angel.fight matches 1 run function angel:fight/bo_release",
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
        "execute if score #hold angel.fight matches 1 run function angel:fight/bo_release",
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
    # --- back-off: after every backoff_hits landed core hits it staggers, turns its back, retreats along the avenue (never past the
    # avenue's far end = angel_start; if there is no room it sidesteps to the other side of the avenue), keeps its barrier up and holds
    # its ground; its first attack (the eye beam, the player being far) ends the hold and lets the barrier down.  States: 9 stagger, 10 retreat.
    zmin10, zmax10 = int(az * 10), int(ARENA["zmax"] * 10)
    xl10, xr10, xc10 = int((ARENA["xmin"] + 1) * 10), int((ARENA["xmax"] - 1) * 10), int(ox * 10)
    d10 = int(C["backoff_dist"] * 10)
    stag = C["backoff_stagger"]
    put("backoff_check", [
        "# called after a landed core hit with the counter at its limit.  Not during the pause after the core cracked (the player's window): try again at the next hit",
        "execute if score #st angel.fight matches 5 if score #sl angel.fight matches 80.. run return 0",
        "execute if score #st angel.fight matches 9..10 run return 0",
        "function angel:fight/backoff_start",
    ])
    put("backoff_start", [
        sc("bo", 0), sc("st", 9), sc("t", 0), sc("locked", 0), sc("bar", 1), sc("barp", 0), sc("hold", 0), sc("hold_t", 0), sc("blockcd", 0), sc("barsnd", 0),
        "function angel:angel/stop_walking",
        "scoreboard players set #dur angel.mon 6",
        "function angel:angel/pose_stagger",
        "stopsound @a * angel:sfx.beam_charge",
        "function angel:fight/backoff_aim",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.hurt hostile @a ~ ~ ~ 8 0.6",
        ] + ([
        "# the barrier goes up: the persistent octagon is built and flares, with the rising tone (it stays until the hold ends)",
        sc("blk_n", 0), sc("blk_why", 0),
        "function angel:fight/vis_state",
        "function angel:fight/shield_flare",
        "execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run function angel:fight/barrier_up",
    ] if V else [
        "# the barrier goes up: the octagon flares at the core (and keeps pulsing until the hold ends)",
        f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~{cy:.2f} ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_flash",
    ]) + [
        'bossbar set angel:fight/angel name {"text":"ANGEL  -  barrier up, it is falling back","color":"red"}',
    ])
    put("backoff_aim", [
        "# the retreat point goes into the angel.target marker: backoff_dist along the avenue away from the giant, kept inside its far end;",
        "# with less than backoff_min of room it steps to the other side of the avenue instead (it still retreats what room there is)",
        "execute store result score #rx angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[0] 10",
        "execute store result score #rz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[2] 10",
        "execute store result score #gz angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[2] 10",
        "scoreboard players operation #tx angel.fight = #rx angel.fight",
        "scoreboard players operation #tz angel.fight = #rz angel.fight",
        # the giant is south of the monster (it comes up the avenue): retreat north, limit z = angel_start's
        f"execute if score #gz angel.fight >= #rz angel.fight run scoreboard players remove #tz angel.fight {d10}",
        "execute if score #gz angel.fight >= #rz angel.fight run scoreboard players operation #room angel.fight = #rz angel.fight",
        f"execute if score #gz angel.fight >= #rz angel.fight run scoreboard players remove #room angel.fight {zmin10}",
        f"execute if score #gz angel.fight >= #rz angel.fight if score #tz angel.fight matches ..{zmin10} run scoreboard players set #tz angel.fight {zmin10}",
        # the giant is north of it: retreat south, limit the avenue's near end
        f"execute if score #gz angel.fight < #rz angel.fight run scoreboard players add #tz angel.fight {d10}",
        f"execute if score #gz angel.fight < #rz angel.fight run scoreboard players set #room angel.fight {zmax10}",
        "execute if score #gz angel.fight < #rz angel.fight run scoreboard players operation #room angel.fight -= #rz angel.fight",
        f"execute if score #gz angel.fight < #rz angel.fight if score #tz angel.fight matches {zmax10}.. run scoreboard players set #tz angel.fight {zmax10}",
        f"execute if score #room angel.fight matches ..{int(C['backoff_min'] * 10) - 1} run function angel:fight/backoff_side",
        f"data modify entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos set value [{ox}d,{oy}d,0.0d]",
        "execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[0] double 0.1 run scoreboard players get #tx angel.fight",
        "execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] double 0.1 run scoreboard players get #tz angel.fight",
    ])
    put("backoff_side", [
        "# no room to retreat: to the other side of the avenue (the monster is on the east half -> west, and the reverse)",
        f"execute if score #rx angel.fight matches {xc10}.. run scoreboard players set #tx angel.fight {xl10}",
        f"execute unless score #rx angel.fight matches {xc10}.. run scoreboard players set #tx angel.fight {xr10}",
    ])
    put("bo_shove", [
        "# thrown back toward the retreat point (along the avenue, away from the giant), a little each tick, so that it has separated from the giant",
        "# before the arms are flung out and it turns its back (the parts teleport with teleport_duration 2: the slide is smooth)",
        f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s facing entity @e[type=minecraft:marker,tag=angel.target,limit=1] feet run tp @s ^ ^ ^{C['shove']}",
        "function angel:angel/sync",
    ])
    put("st_bo_stagger", [
        f"# it is thrown back {C['shove'] * C['shove_ticks']:.1f} blocks in the first {C['shove_ticks']} ticks, reels, then turns its back (8 degrees per tick) and walks off",
        f"execute if score #t angel.fight matches 1..{C['shove_ticks']} run function angel:fight/bo_shove",
        f"execute if score #t angel.fight matches {C['shove_ticks']}..{stag - 1} run function angel:fight/bo_turn",
        f"execute if score #t angel.fight matches {stag}.. run function angel:fight/bo_go",
    ])
    put("bo_turn", ["function angel:angel/turn", "function angel:angel/sync"])
    put("bo_go", [
        sc("st", 10), sc("t", 0),
        f"data modify storage angel:mon walk set value {{speed:{C['backoff_speed']},stop:1.5d}}",
        "function angel:angel/walk_go",
    ])
    put("st_bo_retreat", [
        "execute if score #arrived angel.walk matches 1 run function angel:fight/bo_end",
        f"execute if score #st angel.fight matches 10 if score #t angel.fight matches {int(C['backoff_dist'] / C['backoff_speed'] * 1.6) + 40}.. run function angel:fight/bo_end",
    ])
    put("bo_end", [
        "# arrived (or gave up): it turns to face the giant again (st_move does that), holds its ground, and attacks soon",
        sc("st", 0), sc("t", 0), sc("hold", 1), sc("hold_t", 0), sc("cd", C["backoff_cd"]),
        "execute unless score #arrived angel.walk matches 1 run function angel:angel/stop_walking",
        "execute unless score #arrived angel.walk matches 1 run scoreboard players set #dur angel.mon 20",
        "execute unless score #arrived angel.walk matches 1 run function angel:angel/pose_idle",
    ])
    put("hold_tick", [
        "scoreboard players add #hold_t angel.fight 1",
        f"execute if score #hold_t angel.fight matches {C['backoff_hold']}.. run function angel:fight/bo_release",
    ])
    put("bo_release", [
        "# the barrier comes down and the monster is free to advance again",
        sc("hold", 0), sc("bar", 0), sc("barp", 0), sc("nav", 99),
        'execute if score #phase angel.fight matches 1 run bossbar set angel:fight/angel name {"text":"ANGEL","color":"red"}',
        'execute if score #phase angel.fight matches 2 run bossbar set angel:fight/angel name {"text":"ANGEL  -  core cracked","color":"red"}',
    ] + ([
        "# the barrier comes down: a distinct cue (high tone, chime, flash and a burst of light) and the look follows at once (burning core if he is in reach, else the octagon of range)",
        sc("blk_n", 0), sc("blk_why", 0),
        "function angel:fight/vis_state",
        "execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run function angel:fight/drop_cue",
        "function angel:fight/shield_flare",
    ] if V else [
        "execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run playsound angel:sfx.barrier hostile @a ~ ~ ~ 3 0.6",
        f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:end_rod ~ ~{cy:.2f} ~ 3 3 3 0.1 30 force",
    ]))
    put("core_crack", [
        sc("phase", 2), sc("st", 5), sc("t", 0), sc("sl", 80),
        "# the checkpoint: a loss from here on restarts the fight at this point (start_ck), not at the launch",
        "function angel:fight/ck_save",
        "function angel:angel/stop_walking",
        "function angel:angel/core_stage {stage:1}",
        "function angel:angel/pose_regenerating",
        'execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.roar hostile @a ~ ~ ~ 10 0.7',
        'execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound angel:sfx.core_crack hostile @a ~ ~ ~ 6 1',
        f'execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:lava ~ ~{cy:.2f} ~ 1 1 1 0.2 30 force',
        'bossbar set angel:fight/angel name {"text":"ANGEL  -  core cracked","color":"red"}',
        'function angel:fight/bark {id:"7_12"}',
        'function angel:fight/bark {id:"7_13"}',
    ] + ([sc("vs", 0)] if V else []))      # (core_stage_1 repainted the core: the look is applied again at the next vis_state)
    # --- the wrap and the countdown
    # The monster runs at the giant (st 6, pose wrap_open), stops wrap_dist blocks in front of it and wraps round it (st 7, pose wrapping).  From then on:
    #   * the bark 7.14 ("Break loose!") is queued at the FRONT of the queue, the title tells the player what to do, the core flares; the countdown does NOT
    #     run until the line has begun (#began_7_14, set by bark_play), or wrap_wait ticks, whichever comes first (#wgo 0 -> 1)
    #   * every hit that connects counts (wrap_hit: no guard, no reach, the big body box is a core hit too) and adds wrap_bonus ticks to the bar
    #   * the heartbeat rises (the pause between beats goes from 26 ticks to 6), a ring of red light closes round the giant, the monster squeezes
    #     (pose wrap_tight) in the last wrap_tight_at ticks and the bell beeps in the last 5 s; a hit makes it shudder (pose wrap_hit, 4 ticks)
    put("wrap_start", [
        sc("phase", 3), sc("st", 6), sc("t", 0), sc("nav", 99), sc("bar", 0), sc("hold", 0), sc("bo", 0),
        sc("wgo", 0), sc("wwait", 0), sc("wstage", 0), sc("shud", 0), sc("hbt", 0),
        "function angel:angel/stop_walking",
        "function angel:fight/heartbeat_stop",
        "scoreboard players set #dur angel.mon 10",
        "function angel:angel/pose_wrap_open",
        f"data modify storage angel:mon walk set value {{speed:{C['wrap_speed']},stop:{C['wrap_dist']}d}}",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.roar hostile @a ~ ~ ~ 12 0.5",
        'bossbar set angel:fight/angel name {"text":"ANGEL  -  it is closing in","color":"red"}',
    ])
    put("st_wrap_in", [
        "tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]",
        "execute if score #t angel.fight matches 1 run function angel:angel/walk_go",
        f"execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..{C['wrap_dist'] + 3}] run function angel:fight/wrap_clamp",
        "execute if score #st angel.fight matches 6 if score #t angel.fight matches 100.. run function angel:fight/wrap_clamp",
    ])
    put("wrap_clamp", [
        sc("st", 7), sc("t", 0), sc("wt", C["wrap_ticks"]), sc("wgo", 0), sc("wwait", 0), sc("wstage", 0), sc("shud", 0), sc("hbt", 0),
        "function angel:angel/stop_walking",
        "function angel:fight/wrap_follow",
        "function angel:angel/pose_wrapping",
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.sonic_charge hostile @a ~ ~ ~ 10 0.6",
        'bossbar set angel:fight/wrap players @e[tag=angel.giant,type=minecraft:player]',
        "bossbar set angel:fight/wrap visible true",
        "bossbar set angel:fight/wrap color red",
        f"execute store result bossbar angel:fight/wrap value run scoreboard players get #wt angel.fight",
        'bossbar set angel:fight/angel name {"text":"ANGEL  -  break loose: hit the core","color":"red"}',
        "# the tell: what to do, big, at once; the core flares",
        "execute as @e[tag=angel.giant,type=minecraft:player] run title @s times 0 50 10",
        'execute as @e[tag=angel.giant,type=minecraft:player] run title @s subtitle {"text":"hit the core - keep swinging","color":"gold"}',
        'execute as @e[tag=angel.giant,type=minecraft:player] run title @s title {"text":"BREAK LOOSE","color":"red","bold":true}',
        "function angel:fight/wrap_flare",
        'function angel:fight/bark_front {id:"7_14"}',
    ])
    put("wrap_flare", [
        "# the core calls for the blow: a flash, a burst of light and a red ring round it",
        f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~{cy:.2f} ~ run function angel:fight/wrap_flare_at",
    ])
    put("wrap_flare_at", [
        "particle minecraft:flash{color:[1.0,0.3,0.2,1.0]} ~ ~ ~ 0 0 0 0 1 force",
        "particle minecraft:end_rod ~ ~ ~ 2.5 2.5 2.5 0.25 40 force",
        "particle minecraft:dust{color:[1.0,0.1,0.1],scale:4.0} ~ ~ ~ 3 3 3 0 60 force",
        "playsound minecraft:block.beacon.power_select hostile @a ~ ~ ~ 4 0.6",
    ])
    put("wrap_follow", [
        f"# keeps the monster wrap_dist ({C['wrap_dist']}) blocks from the giant, on the side it came from",
        f"execute at @e[tag=angel.giant,limit=1] facing entity @e[type=minecraft:marker,tag=angel.root,limit=1] feet run tp @e[type=minecraft:marker,tag=angel.root,limit=1] ^ ^ ^{C['wrap_dist']}",
        "tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]",
        "rotate @e[type=minecraft:marker,tag=angel.root,limit=1] facing entity @e[tag=angel.giant,limit=1] feet",
        "function angel:angel/sync",
    ])
    put("st_wrapped", [
        "# the countdown waits for the bark 7.14 to begin (or wrap_wait ticks)",
        "execute if score #wgo angel.fight matches 0 run function angel:fight/wrap_wait",
        "execute if score #wgo angel.fight matches 1 run scoreboard players remove #wt angel.fight 1",
        "execute store result bossbar angel:fight/wrap value run scoreboard players get #wt angel.fight",
        "function angel:fight/wrap_follow",
        "execute as @e[tag=angel.giant,type=minecraft:player] if score #wt angel.fight matches 1.. run effect give @s minecraft:slowness 2 3 true",
        f"execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{{color:[1.0,0.1,0.1],scale:2.5}} ~ ~{cy:.2f} ~ 1.5 1.5 1.5 0 3 force",
        "# the shudder of a hit lasts 4 ticks, then the stage pose comes back",
        "execute if score #shud angel.fight matches 2.. run scoreboard players remove #shud angel.fight 1",
        "execute if score #shud angel.fight matches 1 run function angel:fight/wrap_restore",
        "execute if score #wgo angel.fight matches 1 run function angel:fight/wrap_count",
        "execute if score #wt angel.fight matches ..0 run function angel:fight/self_destruct",
    ])
    put("wrap_wait", [
        "scoreboard players add #wwait angel.fight 1",
        "execute if score #began_7_14 angel.barks matches 1 run scoreboard players set #wgo angel.fight 1",
        f"execute if score #wwait angel.fight matches {C['wrap_wait']}.. run scoreboard players set #wgo angel.fight 1",
        "execute if score #wwait angel.fight matches 30 run function angel:fight/wrap_flare",
        "execute if score #wwait angel.fight matches 60 run function angel:fight/wrap_flare",
    ])
    put("wrap_count", [
        "# only while the countdown runs.  Bell beeps in the last 5 s (two a second)",
        "execute if score #wt angel.fight matches ..100 if score #t angel.fight matches 10 run function angel:fight/wrap_beep",
        "execute if score #wt angel.fight matches ..100 if score #t angel.fight matches 20.. run function angel:fight/wrap_beep",
        "execute if score #t angel.fight matches 20.. run scoreboard players set #t angel.fight 0",
        "# a heartbeat that quickens: the pause between beats is 6 + wt/16 ticks (26 at the start, 6 at the end)",
        "scoreboard players add #hbt angel.fight 1",
        "scoreboard players operation #hbp angel.fight = #wt angel.fight",
        "scoreboard players operation #hbp angel.fight /= #16 angel.fight",
        "scoreboard players add #hbp angel.fight 6",
        "execute if score #hbt angel.fight >= #hbp angel.fight run function angel:fight/wrap_beat",
        "# a ring of red light closes round the giant as the time runs down",
        "execute if score #t angel.fight matches 0 run function angel:fight/wrap_ring",
        "execute if score #t angel.fight matches 5 run function angel:fight/wrap_ring",
        "execute if score #t angel.fight matches 10 run function angel:fight/wrap_ring",
        "execute if score #t angel.fight matches 15 run function angel:fight/wrap_ring",
        "# the squeeze: the tight pose for the last wrap_tight_at ticks (not while it is shuddering from a hit)",
        f"execute if score #shud angel.fight matches 0 if score #wt angel.fight matches ..{C['wrap_tight_at']} unless score #wstage angel.fight matches 1 run function angel:fight/wrap_squeeze",
        f"execute if score #shud angel.fight matches 0 if score #wt angel.fight matches {C['wrap_tight_at'] + 1}.. if score #wstage angel.fight matches 1 run function angel:fight/wrap_loosen",
        "# the bar's colour: white in the last 5 s",
        "execute if score #wt angel.fight matches ..100 run bossbar set angel:fight/wrap color white",
        "execute if score #wt angel.fight matches 101.. run bossbar set angel:fight/wrap color red",
    ])
    put("wrap_squeeze", [sc("wstage", 1), "function angel:angel/pose_wrap_tight"])
    put("wrap_loosen", [sc("wstage", 0), "function angel:angel/pose_wrapping"])
    put("wrap_restore", [
        sc("shud", 0),
        "execute if score #wstage angel.fight matches 1 run function angel:angel/pose_wrap_tight",
        "execute unless score #wstage angel.fight matches 1 run function angel:angel/pose_wrapping",
    ])
    put("wrap_beat", [
        sc("hbt", 0),
        "execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.heartbeat master @a ~ ~ ~ 4 0.9",
        "execute if score #wt angel.fight matches ..200 at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.heartbeat master @a ~ ~ ~ 4 1.2",
        "execute if score #wt angel.fight matches ..100 at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.heartbeat master @a ~ ~ ~ 5 1.5",
    ])
    rings = {}
    for tag, r in (("9", 9.0), ("7", 7.0), ("5", 5.0), ("3", 3.5)):
        pts = []
        for i in range(12):
            a = math.radians(30 * i)
            pts.append(f"particle minecraft:dust{{color:[1.0,0.12,0.1],scale:2.2}} ~{r * math.cos(a):.2f} ~ ~{r * math.sin(a):.2f} 0.1 0.6 0.1 0 1 force")
        put(f"wrap_ring_{tag}", pts)
    put("wrap_ring", [
        "# the ring at the giant's chest (18 up), radius 9 / 7 / 5 / 3.5 as the time runs down",
        "execute if score #wt angel.fight matches 241.. at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_9",
        "execute if score #wt angel.fight matches 161..240 at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_7",
        "execute if score #wt angel.fight matches 81..160 at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_5",
        "execute if score #wt angel.fight matches ..80 at @e[tag=angel.giant,limit=1] positioned ~ ~18 ~ run function angel:fight/wrap_ring_3",
    ])
    put("wrap_beep", [
        "execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.note_block.bell hostile @a ~ ~ ~ 8 1.6",
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
        sc("phase", 4), sc("st", 8), sc("pt", 0), sc("bar", 0), sc("hold", 0),
    ] + (["function angel:fight/vis_off"] if V else []) + [
        "function angel:fight/heartbeat_stop",
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
    ] + (["function angel:fight/vis_off"] if V else []) + [
        "function angel:fight/heartbeat_stop",
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
        "# after the defeat bark: restore, put the giant back at the launch, and begin again a moment later.  Once the core has cracked (#ck) the fight",
        "# resumes at the crack instead (restart_ck): the monster is not rebuilt from the first five minutes",
        "execute if score #ck angel.fight matches 1 run return run function angel:fight/restart_ck",
        "execute as @e[tag=angel.giant] run tag @s add angel.pending",
        "execute as @e[tag=angel.giant] run function angel:fight/leave_giant",
        "function angel:fight/stop_quiet",
        sc("lost_reason", 0),
        "schedule function angel:fight/restart_go 60t",
    ])
    put("restart_ck", [
        "# the checkpoint restart: the giant stays giant (no trip back to the lift), the screen stays black for the pause, then start_ck puts everything",
        "# back where it was when the core cracked",
        "execute as @e[tag=angel.giant] run tag @s add angel.pending",
        "function angel:fight/stop_quiet",
        "execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:blindness 4 0 true",
        "execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:slowness 4 6 true",
        sc("lost_reason", 0),
        "schedule function angel:fight/restart_ck_go 60t",
    ])
    put("restart_ck_go", [
        "execute as @e[tag=angel.pending,limit=1] run function angel:fight/start_ck",
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
    if NB:
        put("test/hit_near", ["# simulates a click on the larger 'near miss' box round the core",
                              "data modify entity @e[type=minecraft:interaction,tag=angel.nearbox,limit=1] attack set value {player:[I;1,2,3,4],timestamp:1L}"])
    put("test/hurt", ["# macro: dmg", "$scoreboard players set #dmg angel.fight $(dmg)", "function angel:fight/hurt"])
    put("test/status", [
        'tellraw @a [{"text":"phase "},{"score":{"name":"#phase","objective":"angel.fight"}},{"text":" st "},{"score":{"name":"#st","objective":"angel.fight"}},{"text":" t "},{"score":{"name":"#t","objective":"angel.fight"}},{"text":" gh "},{"score":{"name":"#gh","objective":"angel.fight"}},{"text":" ch "},{"score":{"name":"#ch","objective":"angel.fight"}},{"text":" wt "},{"score":{"name":"#wt","objective":"angel.fight"}},{"text":" wgo "},{"score":{"name":"#wgo","objective":"angel.fight"}},{"text":" ck "},{"score":{"name":"#ck","objective":"angel.fight"}}]',
    ])
    return F
