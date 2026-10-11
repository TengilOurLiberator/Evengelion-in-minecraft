"""What scenes 6 and 7 change on the player and in the world, and the way back.

Scenes 6 and 7 make the player a 16x giant, give him levitation, ride him on a seat, wrap his head in display glass, move the sky clock and
run the boss fight.  `angel:story/halt` (called by `stop`, `start` and the beginning of every scene) kills every entity tagged angel.story,
clears the story's timers, beds and music, but knows nothing of attributes, effects, the clock rate or the fight.  So `register()` adds
`function angel:story/launch/restore` to the engine's `ctx.halt_extra`, and writes that function.
"""
from core import P, num, sset

RESTORE = "story/launch/restore"

# the attributes angel:fight/become_giant changes (become_human sets them back to their defaults, and so does this)
ATTRIBUTES = ("scale", "step_height", "movement_speed", "jump_strength", "gravity", "safe_fall_distance", "fall_damage_multiplier",
              "entity_interaction_range", "block_interaction_range", "attack_damage", "attack_knockback", "knockback_resistance")


def players():
    """Selector for every player the restore affects: all players on a real server, the mannequin in the dry test build."""
    from core import CFG
    return P() if CFG.dry else "@a"


def register(ctx, geo):
    """Write story/launch/restore (and reset_player) and hook it into halt.  `geo` supplies the places of the rescue boxes (launch_geo)."""
    import launch_audio
    call = f"function angel:{RESTORE}"
    if call not in ctx.halt_extra:
        ctx.halt_extra.append(call)
    if RESTORE in ctx.extra_functions:
        return
    ap = players()
    ctx.extra_functions["story/launch/reset_player"] = (
        [f"attribute @s minecraft:{a} base reset" for a in ATTRIBUTES]
        + ["effect clear @s minecraft:levitation", "effect clear @s minecraft:slow_falling", "effect clear @s minecraft:slowness",
           "tag @s remove angel.giant"])
    L = ["# angel:story/launch/restore: everything scenes 6 and 7 can leave on the player and in the world (called by story/halt)",
         f"execute as {ap} run function angel:story/launch/reset_player",
         "time of angel:day rate 1.0"]
    L += launch_audio.stop_sfx_cmds()
    # the fight, but only when one is going on (its stop clears the giant's blindness, which a scene's fade may be using)
    L += ["execute if score #run angel.fight matches 1 run function angel:fight/stop_quiet",
          "bossbar set angel:fight/giant players", "bossbar set angel:fight/angel players", "bossbar set angel:fight/wrap players"]
    # the cage lights and the eyes, if scenes 6 / 7 switched them on (only when that part of the world is loaded; the flag stays set otherwise)
    L.append(f"execute if score #l.cage angel.story matches 1 if loaded {geo.CAGE_PROBE[0]} {geo.CAGE_PROBE[1]} {geo.CAGE_PROBE[2]} "
             f"run function angel:story/launch/cage_off")
    # nothing of ours may be left standing
    L.append("kill @e[tag=angel.launch]")
    # a player left high in the launch shaft or in mid-air in the cockpit would fall as a human: put him down
    sx, sy, sz, dx, dy, dz = geo.SHAFT_BOX
    px, py, pz = geo.PAD_FEET
    L.append(f"execute as {ap} if entity @s[x={sx},y={sy},z={sz},dx={dx},dy={dy},dz={dz}] run tp @s {num(px)} {num(py)} {num(pz)}")
    cx, cy, cz, cdx, cdy, cdz = geo.COCKPIT_BOX
    fx, fy, fz = geo.FACE_FEET
    L.append(f"execute as {ap} if entity @s[x={cx},y={cy},z={cz},dx={cdx},dy={cdy},dz={cdz}] run tp @s {num(fx)} {num(fy)} {num(fz)}")
    ctx.extra_functions[RESTORE] = L
