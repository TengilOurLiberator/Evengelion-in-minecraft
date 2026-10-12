"""The cage as scenes 6 and 7 need it: lights, eyes, the people, the cockpit in front of the face, the cage after the fight.

The lists in sets/hq.py (CAGE_LIGHTS, BOOTH_LIGHTS, EYES_LEFT, EYES_RIGHT) are in the set's local coordinates; the set stands at x 3000.
"""
from context import cast_look, cast_mount, cast_remove, cast_scale, cast_summon, tp_player
from core import NS, OBJ, P, PA, TAG, fn, num, sset
import launch_geo

GENDO_SCALE = 2.0                 # the commander at the front edge of the booth: twice life size (scene 5 does the same)
DIRTY_MINE = "#l.cage"          # 1 once scenes 6 / 7 have switched the cage lights or the eyes; the restore function puts them back
DIRTY_ENGINE = "#hq.dirty"      # the engine's flag of the same meaning (hq_cage.py): its reset_all runs on stop when this is 1
CAGE_CHUNKS = [(x, z) for x in range(3056, 3136, 16) for z in range(16, 144, 16)]        # the cage: x 3064..3128, z 24..137


def _setblocks(origin, cells):
    return [f"setblock {x + origin[0]} {y + origin[1]} {z + origin[2]} {b}" for (x, y, z, b) in cells]


def register(ctx):
    """Write the cage functions (once per build): story/launch/cage_lights_on, eyes_on, eyes_off."""
    if "story/launch/cage_lights_on" in ctx.extra_functions:
        return
    mod = launch_geo.hq_module(ctx)
    probe = ctx.probe("hq")
    o = probe.o
    dirty = [sset(DIRTY_MINE, 1), sset(DIRTY_ENGINE, 1)]       # "the story has touched the set": restore (here) and the engine's story/hq/reset_all
    # every lamp (the booth's and the lights on the giant's face included), then the eyes
    ctx.extra_functions["story/launch/cage_lights_on"] = dirty + _setblocks(o, mod.CAGE_LIGHTS)
    eyes = [(x, y, z) for (x, y, z) in mod.EYES_LEFT + mod.EYES_RIGHT]
    ns = lambda b: b if ":" in b.split("[")[0] else "minecraft:" + b
    EYE_ON, EYE_OFF = ns(mod.EYE_ON), ns(mod.EYE_OFF)        # the set decides what a lit and a dark eye are
    # the eyes' own glow (hidden light blocks on the brow and the bridge end, built as air: hq.EYE_GLOW) is switched with the eyes
    glow = [(x, y, z, b if ":" in b.split("[")[0] else "minecraft:" + b) for (x, y, z, b) in getattr(mod, "EYE_GLOW", [])]
    glow_off = [(x, y, z, (probe.name(o[0] + x, y, z) or "minecraft:air")) for (x, y, z, b) in glow]
    ctx.extra_functions["story/launch/eyes_on"] = dirty + _setblocks(o, [(x, y, z, EYE_ON) for (x, y, z) in eyes]) + _setblocks(o, glow)
    ctx.extra_functions["story/launch/eyes_off"] = _setblocks(o, [(x, y, z, EYE_OFF) for (x, y, z) in eyes]) + _setblocks(o, glow_off)
    # the set as it was built: what the voxel build holds at each lamp (a dead lamp panel, or air for a hidden light block)
    off = [(x, y, z, (probe.name(o[0] + x, y, z) or "minecraft:air")) for (x, y, z, b) in mod.CAGE_LIGHTS]
    ctx.extra_functions["story/launch/cage_off"] = ([sset(DIRTY_MINE, 0)] + _setblocks(o, off)
                                                    + _setblocks(o, [(x, y, z, EYE_OFF) for (x, y, z) in eyes]) + _setblocks(o, glow_off))
    for (cx, cz) in CAGE_CHUNKS:
        ctx.forceloads.add((cx, cz))           # halt removes them again


def forceload_cage():
    return [f"forceload add {x} {z}" for (x, z) in CAGE_CHUNKS]


def forceload_cage_off():
    return [f"forceload remove {x} {z}" for (x, z) in CAGE_CHUNKS]


def lights_on():
    return fn("story/launch/cage_lights_on")


# ------------------------------------------------------------------------------------------------ the people
def cast_for_cockpit(ctx):
    """Cage as the boy sees it from the giant's eyes: everyone gone, then Misato and Ritsuko on their marks looking up, Gendo in the booth."""
    a = ctx.anchor
    cm, sm, bo = a("hq.captain_mark"), a("hq.scientist_mark"), a("hq.booth")
    return [fn("cast/remove_all"),
            "function angel:cast/gurney_remove",
            cast_summon("misato", cm["x"], cm["y"], cm["z"], cm["yaw"]),
            cast_summon("ritsuko", sm["x"], sm["y"], sm["z"], sm["yaw"]),
            cast_summon("gendo", bo["x"], bo["y"], bo["z"], bo["yaw"]), cast_scale("gendo", GENDO_SCALE),
            cast_look("misato", "player"), cast_look("ritsuko", "player"), cast_look("gendo", "player")]


def cast_for_ending(ctx):
    """The cage after the fight: Misato and Ritsuko on their marks, Gendo in the booth, Rei on the gurney at gurney_mark."""
    a = ctx.anchor
    cm, sm, bo, gm = a("hq.captain_mark"), a("hq.scientist_mark"), a("hq.booth"), a("hq.gurney_mark")
    return [fn("cast/remove_all"),
            "function angel:cast/gurney_remove",
            cast_summon("misato", cm["x"], cm["y"], cm["z"], cm["yaw"]),
            cast_summon("ritsuko", sm["x"], sm["y"], sm["z"], sm["yaw"]),
            cast_summon("gendo", bo["x"], bo["y"], bo["z"], bo["yaw"]), cast_scale("gendo", GENDO_SCALE),
            # the gurney, then Rei on it: gurney, summon, mount, lie (tools/cast/README.md)
            f"execute positioned {num(gm['x'])} {num(gm['y'])} {num(gm['z'])} rotated {num(gm['yaw'], 2)} 0 run function angel:cast/gurney {{}}",
            cast_summon("rei", gm["x"], gm["y"] + 0.82, gm["z"], gm["yaw"]),
            cast_mount("rei", "gurney"),
            f'function angel:cast/pose {{id:"rei",pose:"lying"}}',
            cast_look("misato", "player"), cast_look("ritsuko", "player"), cast_look("gendo", "player")]


# ------------------------------------------------------------------------------------------------ the seat and the moves
SEAT_TAGS = f'"angel.seat","angel.seat_passenger","{TAG}","angel.launch","angel.lseat"'


def summon_seat(feet):
    """The invisible seat: the rider's feet end 0.6 below it (measured by the engine)."""
    return (f'summon minecraft:item_display {num(feet[0])} {num(feet[1] + 0.6)} {num(feet[2])} {{Tags:[{SEAT_TAGS}],teleport_duration:0,'
            f'item_display:"none"}}')


def sit_at(feet, turn_south=False, flat=False):
    """Put the player on a fresh seat at `feet` (any earlier seat is gone first). With turn_south, a player who looks away from
    the south (more than 100 degrees) is turned to face it; one who already looks about that way is not touched.
    Commands are meant to run in one tick."""
    x, y, z = feet
    cmds = [sset("#ride", 0), f"ride {P()} dismount", "kill @e[tag=angel.lseat]", summon_seat(feet)]
    if turn_south:
        cmds += [f"execute as {P()} if entity @s[y_rotation=-100..100] run tp @s {num(x)} {num(y)} {num(z)}",
                 f"execute as {P()} unless entity @s[y_rotation=-100..100] run tp @s {num(x)} {num(y)} {num(z)} 0 0"]
    else:
        cmds.append(tp_player(x, y, z))
    cmds += [f"ride {P()} mount @e[tag=angel.lseat,limit=1]", sset("#ride", 1)]
    return cmds


def leave_seat():
    return [sset("#ride", 0), f"ride {P()} dismount", "kill @e[tag=angel.lseat]"]
