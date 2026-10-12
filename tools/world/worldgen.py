"""The world's own data: the biomes (one per set, plus the void), the day clock and its timeline, the dimension type.

Adapted from Genesis (tools/build_datapack.py): the world is the ordinary overworld made by the flat generator, so
the dimension type is overridden in place (data/minecraft/dimension_type/overworld.json) rather than a new
dimension being declared. Differences from Genesis: the biomes carry no spawns, no precipitation and no features, and
the day clock/timeline are plain vanilla copies, ready for the story to script.

server.properties must point the flat generator at the void biome and, for a true void, give it no layers:

    level-type=minecraft\\:flat
    generator-settings={"biome"\\:"angel\\:void","features"\\:false,"lakes"\\:false,"layers"\\:[],"structure_overrides"\\:[]}

How the look of a set is made (Minecraft 26.3)
---------------------------------------------
A biome file has an "attributes" block of *environment attributes* ("minecraft:visual/sky_color", ".../fog_color",
".../fog_start_distance", ".../fog_end_distance", ...). The client reads them at the camera's position (blended over the
biomes round it), then the dimension's timelines (data/angel/timeline/sky.json, driven by the clock angel:day) modify the
result: at night the vanilla timeline multiplies sky_color by #000000 and fog_color by #0f0f16, in the day by #ffffff.
So a set's colours are the biome's colours times the timeline's multiplier for the clock time the story holds there
(SKY_TICKS below). Water, grass and foliage colours stay in the biome's "effects" block.

Structure templates carry no biomes, so each set's placement chain ends by `fillbiome`-ing the set's box (plus a margin, so
the colours do not snap at the edge) with the set's biome: see biome_items().
"""
import copy
import math
import os

import mcdata

NS = "angel"
CLOCK = f"{NS}:day"

# What each set's sky looks like while the story holds the player there: the time on the day clock (6000 noon, 18000 midnight).
# The clock is paused; `angel:world/sky_<set>` sets it. The multiplier the vanilla timeline applies at that time is part of
# the look (see above): at 6000 sky and fog colours are used as written, at 18000 they are darkened to near black.
SKY_TICKS = {"outskirts": 6000, "city": 18000, "geofront": 6000, "hq": 6000}
SKY_DEFAULT = 6000
if os.environ.get("ANGEL_ATMOSPHERE") == "off":           # the way the world looked before the atmosphere work (for before/after pictures)
    SKY_TICKS = {"outskirts": 6000, "city": 18000, "geofront": 18000, "hq": 18000}

# The city is the one set that sees night (and, in the last scene, the dawn), so the dimension's timeline (a copy of the vanilla
# day, see timeline()) is bent to the city's night: its fog at midnight is NIGHT_FOG (the timeline's multiplier is NIGHT_FOG
# divided by the city biome's fog colour, so the biome keeps a colour that is right for the day) and the moonlight is weaker,
# so that the set's rim and the far mountains melt into the dark. Sets held at noon (every other set) never see this.
NIGHT_FOG = "#05070c"
NIGHT_SKY_LIGHT_FACTOR = 0.10          # vanilla 0.24

GAMERULES = [("advance_weather", "false"), ("spawn_mobs", "false"), ("spawn_monsters", "false"), ("spawn_phantoms", "false"),
             ("spawn_wandering_traders", "false"), ("spawn_patrols", "false"), ("spawn_wardens", "false"),
             ("max_block_modifications", "10000000"), ("max_command_sequence_length", "1000000"),
             ("send_command_feedback", "false"), ("log_admin_commands", "false"), ("locator_bar", "false")]

SPAWN_CATEGORIES = ["ambient", "axolotls", "creature", "misc", "monster", "underground_water_creature", "water_ambient", "water_creature"]

# ---------------------------------------------------------------- the look of each set
# keys of "attr" are environment attributes without the "minecraft:visual/" prefix; "effects" is the biome's effects block.
ATMOSPHERE = {
    "void": {            # everything that is not a set: what the world looked like before, so nothing there changes
        "attr": {"sky_color": "#78a7ff"},
        "effects": {"water_color": "#3f76e4"},
        "temperature": 0.8,
    },
    "outskirts": {       # summer noon, hot and clear
        "attr": {"sky_color": "#3f86f5", "fog_color": "#dfe9ee", "fog_start_distance": 90.0, "fog_end_distance": 320.0,
                 "cloud_color": "#fff4f8ff", "water_fog_color": "#1c78b8"},
        "effects": {"water_color": "#2fa6e2", "grass_color": "#78cf2a", "foliage_color": "#4cb82c", "dry_foliage_color": "#c9a233"},
        "temperature": 0.9,
    },
    "city": {            # deep night (the colours below are the day's: the timeline darkens sky to black and fog to NIGHT_FOG)
        "attr": {"sky_color": "#78a7ff", "fog_color": "#d5e0ec", "fog_start_distance": 30.0, "fog_end_distance": 230.0,
                 "cloud_color": "#00ffffff"},
        "effects": {"water_color": "#1b3a73"},
        "temperature": 0.8,
    },
    "geofront": {        # the lit cavern: dusty late-afternoon gold; sky and fog the same colour, so beyond fog is glow, not night
        "attr": {"sky_color": "#e0aa55", "fog_color": "#e0aa55", "fog_start_distance": 100.0, "fog_end_distance": 300.0,
                 "cloud_color": "#00ffffff", "sky_light_factor": 0.0},
        "effects": {"water_color": "#3f76e4"},
        "temperature": 0.8,
    },
    "hq": {              # the interior: black, slightly cold; the sky does not light it
        "attr": {"sky_color": "#000000", "fog_color": "#000000", "fog_start_distance": 30.0, "fog_end_distance": 140.0,
                 "cloud_color": "#00ffffff", "ambient_light_color": "#0e131e", "sky_light_factor": 0.0},
        "effects": {"water_color": "#3f76e4"},
        "temperature": 0.8,
    },
}

BIOME_MARGIN = 64          # blocks of the set's biome round its box (4 chunks): the colours blend out over this
BIOME_STAGE = 224          # the biome area is filled in squares of at most this many blocks (14 chunks: 196 loaded at once)
BIOME_BAND = 128           # and in bands this high (a fillbiome may touch only max_block_modifications blocks)
BIOME_Y = (-64, 319)       # the whole build height: the camera may be above or below the set's box
BIOME_MS_PER_CELL = 0.0002  # server milliseconds per 4x4x4 cell of fillbiome (a guess until measured; see livecheck.py)


def biome_id(name):
    if os.environ.get("ANGEL_ATMOSPHERE") == "off":
        return f"{NS}:void"
    return f"{NS}:{name}"


def _rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def _attr_value(key, value, name):
    return f"minecraft:visual/{key}", value


def biome(name):
    a = ATMOSPHERE[name]
    attrs = {"minecraft:gameplay/natural_mob_spawns": {
        "argument": {"spawn_costs": {}, "spawns_by_category": {c: [] for c in SPAWN_CATEGORIES}}, "modifier": "overlay"}}
    for k, v in a["attr"].items():
        k, v = _attr_value(k, v, name)
        attrs[k] = v
    return {"attributes": attrs, "carvers": [], "downfall": 0.0, "effects": a["effects"], "features": [],
            "has_precipitation": False, "temperature": a["temperature"]}


def timeline():
    """angel:sky: the vanilla day, with the city's night (see NIGHT_FOG). ANGEL_ATMOSPHERE=off leaves it as vanilla."""
    day = copy.deepcopy(mcdata.vanilla("timeline/day.json"))
    day["clock"] = CLOCK
    if os.environ.get("ANGEL_ATMOSPHERE") == "off":
        return day
    day_fog = _rgb(ATMOSPHERE["city"]["attr"]["fog_color"])
    mul = "#" + "".join(f"{min(255, round(t * 255 / d)):02x}" for t, d in zip(_rgb(NIGHT_FOG), day_fog))
    for k in day["tracks"]["minecraft:visual/fog_color"]["keyframes"]:
        if k["ticks"] in (13670, 22330):                 # the night plateau
            k["value"] = mul
    for k in day["tracks"]["minecraft:visual/sky_light_factor"]["keyframes"]:
        if k["ticks"] in (13140, 22860):
            k["value"] = NIGHT_SKY_LIGHT_FACTOR
    return day


def files():
    """{path relative to the pack root: json value}"""
    dim = copy.deepcopy(mcdata.vanilla("dimension_type/overworld.json"))
    dim["default_clock"] = CLOCK
    dim["timelines"] = [f"{NS}:sky"]

    day = timeline()

    out = {f"data/{NS}/worldgen/biome/{name}.json": biome(name) for name in ATMOSPHERE}
    out.update({
        f"data/{NS}/world_clock/day.json": {},
        f"data/{NS}/timeline/sky.json": day,
        "data/minecraft/dimension_type/overworld.json": dim,
    })
    return out


def init_lines():
    """The commands that put a fresh world in order. Call `function angel:world/init` once from the pack's load function."""
    return (["scoreboard objectives add angel_world dummy", "difficulty peaceful"]
            + [f"gamerule minecraft:{g} {v}" for g, v in GAMERULES]
            + [f"time of {CLOCK} set {SKY_DEFAULT}", f"time of {CLOCK} pause", "weather clear"])


def sky_lines(set_name):
    """Time and weather for a set (angel:world/sky_<set>): safe to call from the story, moves nobody."""
    return [f"time of {CLOCK} set {SKY_TICKS.get(set_name, SKY_DEFAULT)}", f"time of {CLOCK} pause",
            "execute in minecraft:overworld run weather clear"]


def enter_lines(set_name, anchor):
    """angel:world/enter_<set>: the set's sky, and the player taken to its start anchor (a dict with x y z yaw pitch) when it has one."""
    lines = [f"function {NS}:world/sky_{set_name}"]
    if anchor:
        # whole-number x and z are block coordinates: stand in the middle of the block, not on its corner
        x, z = (float(anchor[k]) + (0.5 if float(anchor[k]) == int(float(anchor[k])) else 0.0) for k in ("x", "z"))
        lines.append("execute in minecraft:overworld run tp @s {} {} {} {} {}".format(
            _num(x), _num(anchor["y"]), _num(z), _num(anchor["yaw"]), _num(anchor["pitch"])))
    return lines


# ---------------------------------------------------------------- putting a biome on a set

def _cuts(lo, hi, step):
    """Split lo..hi (inclusive) into pieces of at most `step` that start on multiples of 16."""
    out, a = [], lo
    while a <= hi:
        b = min(hi, (a // 16) * 16 + step - 1)
        out.append((a, b))
        a = b + 1
    return out


def biome_region(origin, size):
    """(x1, z1, x2, z2): the set's footprint plus the margin."""
    return (origin[0] - BIOME_MARGIN, origin[2] - BIOME_MARGIN,
            origin[0] + size[0] - 1 + BIOME_MARGIN, origin[2] + size[2] - 1 + BIOME_MARGIN)


def biome_items(set_name, origin, size):
    """The chain items (see compile.make_chain) that fill a set's box plus margin with its biome, full build height:
    square stages that are forceloaded one after the other, each filled in bands of BIOME_BAND blocks."""
    if os.environ.get("ANGEL_BIOME_FILL") == "off":           # for timing the placement without the biome stages
        return []
    x1, z1, x2, z2 = biome_region(origin, size)
    items = []
    bands = []
    y = BIOME_Y[0]
    while y <= BIOME_Y[1]:
        bands.append((y, min(BIOME_Y[1], y + BIOME_BAND - 1)))
        y += BIOME_BAND
    for i, (ax, bx) in enumerate(_cuts(x1, x2, BIOME_STAGE)):
        for j, (az, bz) in enumerate(_cuts(z1, z2, BIOME_STAGE)):
            cmds = [f"fillbiome {ax} {ya} {az} {bx} {yb} {bz} {biome_id(set_name)}" for ya, yb in bands]
            cells = ((bx - ax + 1) // 4 + 1) * ((bz - az + 1) // 4 + 1) * ((BIOME_Y[1] - BIOME_Y[0] + 1) // 4)
            items.append({"stage": (1, i, j), "ix": i, "iy": 0, "iz": j, "lo": (ax, BIOME_Y[0], az), "hi": (bx, BIOME_Y[1], bz),
                          "margin": 0, "ms": BIOME_MS_PER_CELL * cells, "cmds": cmds})
    return items


def probe_points(set_name, origin, size, anchors):
    """[(x, y, z)] where the set's biome must be found once it is placed: corners, centre, the margin's edge, above and below
    the box, and the set's anchors."""
    ox, oy, oz = origin
    sx, sy, sz = size
    m = BIOME_MARGIN - 4
    pts = []
    for fx in (0, 0.5, 1):
        for fz in (0, 0.5, 1):
            x, z = ox + int(round((sx - 1) * fx)), oz + int(round((sz - 1) * fz))
            pts.append((x, oy + sy // 2, z))
    pts += [(ox - m, oy + 4, oz - m), (ox + sx + m, oy + sy - 4, oz + sz + m), (ox - m, oy + sy // 2, oz + sz // 2),
            (ox + sx // 2, oy + sy + 100, oz + sz // 2), (ox + sx // 2, BIOME_Y[0] + 4, oz + sz // 2)]
    pts += [(int(math.floor(a["x"])), int(math.floor(a["y"])), int(math.floor(a["z"]))) for a in anchors.values()]
    seen, out = set(), []
    for p in pts:
        if p not in seen:
            seen.add(p)
            out.append(p)
    return out


def probe_lines(set_name, origin, size, anchors):
    """Commands that count the probe points holding the set's biome and say the result in the server log."""
    if os.environ.get("ANGEL_BIOME_FILL") == "off":
        return []
    pts = probe_points(set_name, origin, size, anchors)
    lines = ["scoreboard players set #bp angel_world 0"]
    lines += [f"execute in minecraft:overworld if biome {x} {y} {z} {biome_id(set_name)} run scoreboard players add #bp angel_world 1"
              for x, y, z in pts]
    lines += [f"execute if score #bp angel_world matches {len(pts)} run say [angel] biome {set_name}: all {len(pts)} probes found {biome_id(set_name)}",
              f"execute unless score #bp angel_world matches {len(pts)} run say [angel] BIOME CHECK FAILED for {set_name}: fewer than {len(pts)} probes found {biome_id(set_name)}"]
    return lines


def _num(v):
    v = float(v)
    return str(int(v)) if v == int(v) else f"{v:.4f}".rstrip("0").rstrip(".")
