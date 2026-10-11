"""The world's own data: the void biome, the day clock and its timeline, the dimension type.

Adapted from Genesis (tools/build_datapack.py): the world is the ordinary overworld made by the flat generator, so
the dimension type is overridden in place (data/minecraft/dimension_type/overworld.json) rather than a new
dimension being declared. Differences from Genesis: the biome is empty (no spawns, no precipitation, no features) and
the day clock/timeline are plain vanilla copies, ready for the story to script.

server.properties must point the flat generator at this biome and, for a true void, give it no layers:

    level-type=minecraft\\:flat
    generator-settings={"biome"\\:"angel\\:void","features"\\:false,"lakes"\\:false,"layers"\\:[],"structure_overrides"\\:[]}
"""
import copy

import mcdata

NS = "angel"
CLOCK = f"{NS}:day"

# What each set's sky looks like when the player enters it: the time on the day clock (6000 noon, 18000 midnight).
# The story will script the sky properly later; these are the starting points.
SKY_TICKS = {"outskirts": 6000, "city": 18000, "geofront": 18000, "hq": 18000}
SKY_DEFAULT = 6000

GAMERULES = [("advance_weather", "false"), ("spawn_mobs", "false"), ("spawn_monsters", "false"), ("spawn_phantoms", "false"),
             ("spawn_wandering_traders", "false"), ("spawn_patrols", "false"), ("spawn_wardens", "false"),
             ("max_block_modifications", "10000000"), ("max_command_sequence_length", "1000000"),
             ("send_command_feedback", "false"), ("log_admin_commands", "false"), ("locator_bar", "false")]


def files():
    """{path relative to the pack root: json value}"""
    spawn_categories = ["ambient", "axolotls", "creature", "misc", "monster", "underground_water_creature", "water_ambient", "water_creature"]
    biome = {
        "attributes": {
            "minecraft:gameplay/natural_mob_spawns": {
                "argument": {"spawn_costs": {}, "spawns_by_category": {c: [] for c in spawn_categories}},
                "modifier": "overlay"},
            "minecraft:visual/sky_color": "#78a7ff"},
        "carvers": [], "downfall": 0.0, "effects": {"water_color": "#3f76e4"}, "features": [],
        "has_precipitation": False, "temperature": 0.8}

    dim = copy.deepcopy(mcdata.vanilla("dimension_type/overworld.json"))
    dim["default_clock"] = CLOCK
    dim["timelines"] = [f"{NS}:sky"]

    day = copy.deepcopy(mcdata.vanilla("timeline/day.json"))
    day["clock"] = CLOCK

    return {
        f"data/{NS}/worldgen/biome/void.json": biome,
        f"data/{NS}/world_clock/day.json": {},
        f"data/{NS}/timeline/sky.json": day,
        "data/minecraft/dimension_type/overworld.json": dim,
    }


def init_lines():
    """The commands that put a fresh world in order. Call `function angel:world/init` once from the pack's load function."""
    return (["scoreboard objectives add angel_world dummy", "difficulty peaceful"]
            + [f"gamerule minecraft:{g} {v}" for g, v in GAMERULES]
            + [f"time of {CLOCK} set {SKY_DEFAULT}", f"time of {CLOCK} pause", "weather clear"])


def enter_lines(set_name, anchor):
    """Sky and weather for a set, and the player taken to its start anchor (a dict with x y z yaw pitch) when it has one."""
    lines = [f"time of {CLOCK} set {SKY_TICKS.get(set_name, SKY_DEFAULT)}", f"time of {CLOCK} pause",
             "execute in minecraft:overworld run weather clear"]
    if anchor:
        # whole-number x and z are block coordinates: stand in the middle of the block, not on its corner
        x, z = (float(anchor[k]) + (0.5 if float(anchor[k]) == int(float(anchor[k])) else 0.0) for k in ("x", "z"))
        lines.append("execute in minecraft:overworld run tp @s {} {} {} {} {}".format(
            _num(x), _num(anchor["y"]), _num(z), _num(anchor["yaw"]), _num(anchor["pitch"])))
    return lines


def _num(v):
    v = float(v)
    return str(int(v)) if v == int(v) else f"{v:.4f}".rstrip("0").rstrip(".")
