"""Sky and weather for each set, as the world generator defines them (tools/world/worldgen.py SKY_TICKS), without the teleport that
`angel:world/enter_<set>` also does: that one turns the player's head to the set's start direction, and the story never does that."""
import sys

from core import TOOLS

CLOCK = "angel:day"
SKY_TICKS = {"outskirts": 6000, "city": 18000, "geofront": 18000, "hq": 18000}


def sky(set_name):
    ticks = SKY_TICKS.get(set_name, 6000)
    return [f"time of {CLOCK} set {ticks}", f"time of {CLOCK} pause", "execute in minecraft:overworld run weather clear"]
