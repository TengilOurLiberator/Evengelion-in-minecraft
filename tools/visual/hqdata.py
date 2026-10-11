"""Switches that the story will operate later, generated from tools/world/sets/hq.py (its CAGE_LIGHTS / BOOTH_LIGHTS /
EYES_* lists and the giant's raised hand), as helper functions in the scratch datapack: angel:visual/<name>."""
import importlib
import os
import sys

TOOLS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD = os.path.join(TOOLS, "world")


def _hq():
    for p in (WORLD, TOOLS):
        if p not in sys.path:
            sys.path.insert(0, p)
    import layout
    import voxel
    mod = importlib.import_module("sets.hq")
    origin, size = layout.SETS["hq"]
    w = voxel.World("hq", origin, size)
    mod.build(w)
    return mod, origin


def _cmds(origin, cells, block=None):
    ox, oy, oz = origin
    for c in cells:
        x, y, z = c[0], c[1], c[2]
        b = block or c[3]
        if not b.startswith("minecraft:"):
            b = "minecraft:" + b
        yield f"setblock {x + ox} {y + oy} {z + oz} {b}"


def functions():
    """{ 'visual/cage_lights_on': [lines], ... }"""
    hq, o = _hq()
    ox, oy, oz = o
    f = {}
    f["visual/cage_lights_on"] = list(_cmds(o, hq.CAGE_LIGHTS))
    f["visual/booth_lights_on"] = list(_cmds(o, hq.BOOTH_LIGHTS))
    f["visual/eyes_on"] = list(_cmds(o, hq.EYES_LEFT + hq.EYES_RIGHT, hq.EYE_ON))
    f["visual/eyes_off"] = list(_cmds(o, hq.EYES_LEFT + hq.EYES_RIGHT, hq.EYE_OFF))
    f["visual/cage_lights_off"] = [l.rsplit(" ", 1)[0] + " minecraft:air" for l in f["visual/cage_lights_on"]]
    # the hand: clear the lowered box (put the coolant back below its surface), then place the raised cells
    lo = hq.HAND["lowered"]
    x1, y1, z1, x2, y2, z2 = lo
    lines = [f"fill {x1 + ox} {y1 + oy} {z1 + oz} {x2 + ox} {y2 + oy} {z2 + oz} minecraft:air"]
    if y1 <= hq.SURF:
        lines.append(f"fill {x1 + ox} {y1 + oy} {z1 + oz} {x2 + ox} {min(y2, hq.SURF) + oy} {z2 + oz} minecraft:{hq.LIQUID}")
    for (x, y, z), b in hq.hand_cells(True, (hq.CX, hq.BRIDGE_Y, hq.SHIELD_Z)).items():
        lines.append(f"setblock {x + ox} {y + oy} {z + oz} {b if b.startswith('minecraft:') else 'minecraft:' + b}")
    f["visual/hand_raised"] = lines
    return f
