"""Shared helpers for the story generator: constants, the file writer (with a manifest so that only our own files are
ever removed), command snippets, and a binary-tree dispatcher for tick-driven lookups.

Everything the generator writes lives in the datapack under   data/angel/function/story/   and   data/angel/function/say/
(plus advancement / predicate files in subfolders named `story`, should any be needed).
"""
import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
PACK = os.path.join(ROOT, "datapack", "angel")
MANIFEST = os.path.join(HERE, "build_manifest.json")
ANCHORS = os.path.join(TOOLS, "world", "anchors.json")
SCRIPT = os.path.join(ROOT, "script.md")
DURATIONS = os.path.join(ROOT, "voices", "durations.json")
SOUNDS = os.path.join(ROOT, "pack", "angel-resources", "assets", "angel", "sounds.json")

NS = "angel"
OBJ = "angel.story"          # the scoreboard objective that holds all story state and the bridge contract
TAG = "angel.story"          # every entity we summon carries this tag, so start / stop / reload can sweep them

CHARACTERS = ["misato", "ritsuko", "gendo", "rei"]          # the bridge's ids 1..4
CAST_IDS = ["misato", "ritsuko", "gendo", "rei", "rei_uniform", "medic1", "medic2"]
DISPLAY_NAMES = {"misato": "Misato", "ritsuko": "Ritsuko", "gendo": "your father", "rei": "Rei"}

TPS = 20


class Config:
    """Build-time switches. `dry` replaces the player by a mannequin tagged angel.testplayer (for the scratch server)."""
    dry = False
    gap = 0.4                # seconds of silence between two recorded lines in a block
    answer_est = 6.0         # how long the offline simulator assumes a spoken answer takes
    subtitles_default = 0    # 1: show every recorded line as chat text too (flat-screen testing)


CFG = Config()


def T(sec):
    """seconds -> ticks"""
    return int(round(float(sec) * TPS))


def num(v, nd=3):
    """compact decimal, never scientific notation, ALWAYS with a decimal point: a whole-number x or z written as "131" is taken by the
    game for a block coordinate and moved to the middle of the block (131.5); "131.0" is exactly 131."""
    v = float(v)
    if v == int(v):
        return f"{int(v)}.0"
    s = f"{v:.{nd}f}".rstrip("0").rstrip(".")
    if s in ("-0", "", "-"):
        return "0.0"
    return s if "." in s else s + ".0"


def fnum(v, nd=5):
    """an SNBT float literal"""
    return num(v, nd) + "f"


# --------------------------------------------------------------------------------------------------- selectors
def P(extra=""):
    """The one player (Shinji). In dry mode a mannequin stands in for him."""
    if CFG.dry:
        return "@e[type=minecraft:mannequin,tag=angel.testplayer,limit=1" + ("," + extra if extra else "") + "]"
    return "@a[limit=1" + ("," + extra if extra else "") + "]"


def blind(seconds):
    """Blindness for `seconds` (whole seconds are all the command takes; it fades back over the last one): the story's fade through darkness."""
    return f"effect give @a minecraft:blindness {int(math.ceil(seconds))} 0 true"


def PA():
    """Selector for commands that only accept real players (title, playsound, effect, give): always @a."""
    return "@a"


# --------------------------------------------------------------------------------------------------- commands
def sset(name, value):
    return f"scoreboard players set {name} {OBJ} {int(value)}"


def sadd(name, value=1):
    return f"scoreboard players add {name} {OBJ} {int(value)}"


def ssub(name, value=1):
    return f"scoreboard players remove {name} {OBJ} {int(value)}"


def sop(a, op, b):
    return f"scoreboard players operation {a} {OBJ} {op} {b} {OBJ}"


def sc(name, rng):
    """score condition fragment:   if score #x angel.story matches 3..5"""
    return f"if score {name} {OBJ} matches {rng}"


def fn(path):
    return f"function {NS}:{path}"


def at_xyz(x, y, z, yaw=None, pitch=None):
    """execute fragment that moves the context to a point (and optionally turns it)."""
    s = f"positioned {num(x)} {num(y)} {num(z)}"
    if yaw is not None:
        s += f" rotated {num(yaw, 2)} {num(pitch or 0, 2)}"
    return s


# --------------------------------------------------------------------------------------------------- output
class Out:
    """Collects files in memory, then writes them under the pack and removes what an earlier build wrote and this one did not."""

    def __init__(self, base=PACK):
        self.base = base
        self.files = {}

    def put(self, rel, text):
        self.files[rel] = text if isinstance(text, str) else json.dumps(text, indent=1)

    def function(self, path, lines):
        if isinstance(lines, str):
            lines = [lines]
        self.files[f"data/{NS}/function/{path}.mcfunction"] = "\n".join(lines) + "\n"

    def has_function(self, path):
        return f"data/{NS}/function/{path}.mcfunction" in self.files

    def write(self, manifest=MANIFEST):
        written = 0
        for rel, text in self.files.items():
            path = os.path.join(self.base, *rel.split("/"))
            data = text.encode("utf-8")
            os.makedirs(os.path.dirname(path), exist_ok=True)
            if os.path.isfile(path) and os.path.getsize(path) == len(data):
                with open(path, "rb") as f:
                    if f.read() == data:
                        continue
            with open(path, "wb") as f:
                f.write(data)
            written += 1
        removed = 0
        if os.path.isfile(manifest):
            with open(manifest, encoding="utf-8") as f:
                old = json.load(f).get("files", [])
            for rel in old:
                if rel not in self.files:
                    path = os.path.join(self.base, *rel.split("/"))
                    if os.path.isfile(path):
                        os.remove(path)
                        removed += 1
                    d = os.path.dirname(path)
                    while os.path.abspath(d) != os.path.abspath(self.base) and os.path.isdir(d) and not os.listdir(d):
                        os.rmdir(d)
                        d = os.path.dirname(d)
        with open(manifest, "w", encoding="utf-8") as f:
            json.dump({"files": sorted(self.files)}, f, indent=0)
        return written, removed


# --------------------------------------------------------------------------------------------------- dispatch trees
def dispatch_tree(out, base, key, items, leaf=8):
    """Write functions so that `function angel:<base>/root` runs items[value] (a list of command lines) when the score
    `key` equals value.  `items` is {int: [lines]}.  Cost per call: a few comparisons, not one per item."""
    keys = sorted(items)
    counter = [0]

    def node(ks):
        idx = counter[0]
        counter[0] += 1
        name = f"{base}/n{idx}"
        lines = []
        if len(ks) <= leaf:
            for k in ks:
                for ln in items[k]:
                    lines.append(f"execute if score {key} {OBJ} matches {k} run {ln}" if not ln.startswith("execute ")
                                 else f"execute if score {key} {OBJ} matches {k} {ln[len('execute '):]}")
        else:
            half = len(ks) // 2
            for part in (ks[:half], ks[half:]):
                child = node(part)
                lines.append(f"execute if score {key} {OBJ} matches {part[0]}..{part[-1]} run function {NS}:{child}")
        out.function(name, lines)
        return name

    if not keys:
        out.function(f"{base}/root", ["# (empty)"])
        return
    root = node(keys)
    # make the root addressable under a stable name
    out.function(f"{base}/root", [f"function {NS}:{root}"])


def range_tree(out, base, key, ranges, leaf=6):
    """Like dispatch_tree, but over ranges: ranges = [(lo, hi, line)] sorted, non overlapping.  `function angel:<base>/root` runs the
    line of the range that contains the score."""
    counter = [0]

    def node(rs):
        idx = counter[0]
        counter[0] += 1
        name = f"{base}/n{idx}"
        lines = []
        if len(rs) <= leaf:
            for lo, hi, ln in rs:
                lines.append(f"execute if score {key} {OBJ} matches {lo}..{hi} run {ln}")
        else:
            half = len(rs) // 2
            for part in (rs[:half], rs[half:]):
                child = node(part)
                lines.append(f"execute if score {key} {OBJ} matches {part[0][0]}..{part[-1][1]} run function {NS}:{child}")
        out.function(name, lines)
        return name

    if not ranges:
        out.function(f"{base}/root", ["# (empty)"])
        return
    out.function(f"{base}/root", [f"function {NS}:{node(ranges)}"])


# --------------------------------------------------------------------------------------------------- tiny vector / quaternion maths
def qmul(a, b):
    ax, ay, az, aw = a
    bx, by, bz, bw = b
    return (aw * bx + ax * bw + ay * bz - az * by,
            aw * by - ax * bz + ay * bw + az * bx,
            aw * bz + ax * by - ay * bx + az * bw,
            aw * bw - ax * bx - ay * by - az * bz)


def qaxis(axis, deg):
    h = math.radians(deg) / 2
    s, c = math.sin(h), math.cos(h)
    return {"x": (s, 0, 0, c), "y": (0, s, 0, c), "z": (0, 0, s, c)}[axis]


def qrot(q, v):
    x, y, z, w = q
    # v' = q * v * q^-1
    p = qmul(qmul(q, (v[0], v[1], v[2], 0.0)), (-x, -y, -z, w))
    return (p[0], p[1], p[2])


QI = (0.0, 0.0, 0.0, 1.0)


def vadd(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def vsub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def yaw_to_dir(yaw):
    """Minecraft yaw (0 = south/+z, 90 = west/-x) -> unit (dx, dz)"""
    r = math.radians(yaw)
    return (-math.sin(r), math.cos(r))


def dir_to_yaw(dx, dz):
    return math.degrees(math.atan2(-dx, dz))


def angdiff(a, b):
    """smallest signed difference a - b in degrees"""
    return (a - b + 180.0) % 360.0 - 180.0


def local_to_world(origin, yaw, pitch, lx, ly, lz):
    """The point `^lx ^ly ^lz` from `origin` facing (yaw, pitch): +x = left, +y = up, +z = forward."""
    q = qmul(qaxis("y", -yaw), qaxis("x", pitch))
    d = qrot(q, (lx, ly, lz))
    return (origin[0] + d[0], origin[1] + d[1], origin[2] + d[2])
