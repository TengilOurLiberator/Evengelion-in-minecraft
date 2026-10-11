"""What the game says about itself: block ids and their state properties, the command tree, the data version.

The big vanilla reports (made by the server jar's data generator: `java -DbundlerMainClass=net.minecraft.data.Main
-jar server.jar --reports`) are reduced once into small files in tools/world/mcdata/ so this project does not
depend on another project's folder after the first run. To refresh them for a newer game version delete the
files there; they are rebuilt from the first reports folder found:

    $env:ANGEL_MCREPORTS, D:\\genesis-vr\\work\\mcdata\\out\\reports (read only)

DataVersion comes from the server jar (version.json: world_version).
"""
import json
import os
import re
import zipfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
CACHE = os.path.join(HERE, "mcdata")
REPORT_DIRS = [os.environ.get("ANGEL_MCREPORTS", ""), r"D:\genesis-vr\work\mcdata\out\reports"]
JARS = [os.path.join(ROOT, "server", "versions", "26.3", "server-26.3.jar"), os.path.join(ROOT, "server", "server.jar"),
        r"D:\genesis-vr\server\server.jar"]
FALLBACK_DATA_VERSION = 5023            # 26.3


def _reports():
    for d in REPORT_DIRS:
        if d and os.path.isfile(os.path.join(d, "blocks.json")):
            return d
    raise FileNotFoundError("no vanilla data reports found: set ANGEL_MCREPORTS to a folder holding blocks.json and commands.json")


def _cached(name, make):
    path = os.path.join(CACHE, name)
    if not os.path.isfile(path):
        os.makedirs(CACHE, exist_ok=True)
        data = make()
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            json.dump(data, f, separators=(",", ":"), sort_keys=True)
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def blocks():
    """{ 'minecraft:oak_stairs': {'facing': ['north', ...], ...}, ... }: every block and the values each property can take."""
    def make():
        with open(os.path.join(_reports(), "blocks.json"), encoding="utf-8") as f:
            raw = json.load(f)
        return {k: v.get("properties", {}) for k, v in raw.items()}
    return _cached("blocks.json", make)


def block_defaults():
    """{ 'minecraft:oak_door': {'facing': 'north', ...} }: the default state of every block (a world file stores a
    block whose properties are all default as just its name)."""
    def make():
        with open(os.path.join(_reports(), "blocks.json"), encoding="utf-8") as f:
            raw = json.load(f)
        out = {}
        for k, v in raw.items():
            out[k] = next((s.get("properties", {}) for s in v["states"] if s.get("default")), {})
        return out
    return _cached("block_defaults.json", make)


def commands():
    """The command tree (the commands.json report)."""
    def make():
        with open(os.path.join(_reports(), "commands.json"), encoding="utf-8") as f:
            return json.load(f)
    return _cached("commands.json", make)


def registry(name):
    """Entry names of a registry, e.g. registry('minecraft:game_rule')."""
    def make():
        with open(os.path.join(_reports(), "registries.json"), encoding="utf-8") as f:
            raw = json.load(f)
        return {k: sorted(v["entries"]) for k, v in raw.items()}
    return _cached("registries.json", make).get(name, [])


def version():
    """{'id': '26.3', 'world_version': 5023, ...} from the server jar."""
    def make():
        for jar in JARS:
            if os.path.isfile(jar):
                with zipfile.ZipFile(jar) as z:
                    return json.loads(z.read("version.json"))
        return {"id": "26.3", "world_version": FALLBACK_DATA_VERSION}
    return _cached("version.json", make)


def vanilla(rel):
    """A vanilla data file from the server jar, parsed, e.g. vanilla('dimension_type/overworld.json')."""
    for jar in JARS:
        if os.path.isfile(jar):
            with zipfile.ZipFile(jar) as z:
                try:
                    return json.loads(z.read("data/minecraft/" + rel))
                except KeyError:
                    continue
    raise FileNotFoundError(f"data/minecraft/{rel} is in none of the server jars")


def data_version():
    return int(version()["world_version"])


_STATE = re.compile(r"^([a-z0-9_.\-]+:[a-z0-9_./\-]+)(?:\[([^\]]*)\])?$")


def parse_block(text):
    """'minecraft:oak_stairs[facing=east,half=top]' -> ('minecraft:oak_stairs', {'facing': 'east', 'half': 'top'}).
    Raises ValueError for anything else (block entity data in braces is not supported: use commands for that)."""
    m = _STATE.match(text)
    if not m:
        raise ValueError(f"cannot read the block {text!r} (expected namespace:name[prop=value,...])")
    props = {}
    if m.group(2):
        for part in m.group(2).split(","):
            if "=" not in part:
                raise ValueError(f"bad state property {part!r} in {text!r}")
            k, v = part.split("=", 1)
            k, v = k.strip(), v.strip()
            if k in props:
                raise ValueError(f"property {k!r} given twice in {text!r}")
            props[k] = v
    return m.group(1), props


def check_block(text, table=None):
    """None when the block exists and every property and value is valid for it, else a message."""
    table = blocks() if table is None else table
    try:
        name, props = parse_block(text)
    except ValueError as e:
        return str(e)
    if name not in table:
        return f"unknown block {name}"
    allowed = table[name]
    for k, v in props.items():
        if k not in allowed:
            return f"{name} has no property {k!r} (it has: {', '.join(allowed) or 'none'})"
        if v not in allowed[k]:
            return f"{name}: {k}={v} is not valid (one of {', '.join(allowed[k])})"
    return None
