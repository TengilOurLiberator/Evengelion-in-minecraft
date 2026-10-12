"""Everything a scene module needs besides the Scene itself: anchors, lines, rigs, routes, the voxel probes, small command helpers."""
import json
import re

from core import ANCHORS, CAST_IDS, NS, OBJ, P, PA, TAG, fn, num, sset
from lines import load_lines
from models import car_rig, cartrain_rig, aircraft_rig, Rig
from movers import Route


class Context:
    def __init__(self, warn=print):
        self.warn = warn
        self.lines, self.line_order = load_lines(warn)
        with open(ANCHORS, encoding="utf-8") as f:
            self.anchors = json.load(f)
        self.used_anchors = set()
        self.scenes = []
        self.flags = set()
        self.routes = {}
        self.rigs = {}
        self.rig_variants = {}
        self.prompt_variants = []
        self.forceloads = set()
        self.extra_functions = {}
        self.fx_tick = []
        self.fx_flags = set()
        self.fx_scheduled = []
        self._probes = {}
        self.missing_anchors = []
        # --- additions of the scene-4/5 phase (all optional; scenes 1 to 3 never touch them)
        self.halt_extra = []              # commands appended to angel:story/halt
        self.stop_extra = []              # commands run by angel:story/stop and angel:story/start after the halt (e.g. restore blocks)
        self.load_extra = []              # commands appended to angel:story/load
        self.cards = {}                   # (text, small) -> index, see cards.py
        self.turns = []                   # smooth turns of characters (lead.py)
        self.helpers = {}                 # per-module caches (hq_cage etc.)
        self.objectives = []              # objective.Objective, index = k of angel:story/ob/b<k>
        self.prompt_loud = set()          # prompt texts drawn in yellow (the consent wait)
        self.enter_hooks = {}             # scene number -> commands run when the scene is entered (jump or hand-over): see system.py
        from audio import Audio
        self.audio = Audio(self)

    # ------------------------------------------------------------------ anchors
    def anchor(self, name):
        """{x, y, z, yaw, pitch} of a named place (names are '<set>.<anchor>', see tools/world/anchors.json)."""
        self.used_anchors.add(name)
        a = self.anchors.get(name)
        if a is None:
            self.missing_anchors.append(name)
            raise KeyError(f"anchor {name!r} does not exist in anchors.json")
        return a

    def xyz(self, name, dy=0.0):
        a = self.anchor(name)
        return (a["x"], a["y"] + dy, a["z"])

    def probe(self, set_name):
        if set_name not in self._probes:
            from world_probe import Probe
            self._probes[set_name] = Probe(set_name)
        return self._probes[set_name]

    # ------------------------------------------------------------------ prompts
    def prompt_variant(self, text):
        if text not in self.prompt_variants:
            self.prompt_variants.append(text)
        return self.prompt_variants.index(text)

    # ------------------------------------------------------------------ objectives
    def ob_index(self, obj):
        """index of an objective in the registry (the same objective twice is one entry)"""
        key = obj.key()
        for k, o in enumerate(self.objectives):
            if o.key() == key:
                return k
        self.objectives.append(obj)
        return len(self.objectives) - 1

    def ob_begin(self, obj):
        """the command that makes `obj` the current objective (for scene code that switches objectives from its own tick, e.g. the fight's guide)"""
        return f"function {NS}:story/ob/b{self.ob_index(obj)}"

    # ------------------------------------------------------------------ rigs and routes
    def rig(self, name, factory=None):
        if name not in self.rigs:
            self.rigs[name] = factory() if factory else {"car": car_rig, "cartrain": lambda: cartrain_rig("cartrain")}[name]()
        return self.rigs[name]

    def register_rig(self, rig):
        self.rigs[rig.name] = rig
        return rig

    def spawn_variant(self, rig, variant, motions=None, seats=True):
        """Register a way of spawning `rig` (door open, on its side ...); returns the function that does it, to be called at the pose."""
        self.rig_variants[(rig.name, variant)] = (rig, motions, seats)
        self.rigs.setdefault(rig.name, rig)
        return f"{NS}:story/rig/{rig.name}/spawn_{variant}"

    def rig_spawn(self, rig, variant, pose, motions=None, seats=True):
        """Commands that put a rig at pose = (x, y, z, yaw, pitch)."""
        fnname = self.spawn_variant(rig, variant, motions, seats)
        x, y, z, yaw, pitch = pose
        return [f"execute positioned {num(x)} {num(y)} {num(z)} rotated {num(yaw, 2)} {num(pitch, 2)} run function {fnname}"]

    def rig_place(self, rig, pose):
        x, y, z, yaw, pitch = pose
        return [f"execute positioned {num(x)} {num(y)} {num(z)} rotated {num(yaw, 2)} {num(pitch, 2)} run function {NS}:story/rig/{rig.name}/follow"]

    def new_route(self, name, rig):
        if name in self.routes:
            raise ValueError(f"route {name} exists")
        r = Route(name, rig.name, len(self.routes) + 1)
        self.routes[name] = r
        self.rigs.setdefault(rig.name, rig)
        return r

    def preload(self, x, z):
        """forceload commands for the chunk holding (x, z); halt removes them again"""
        cx, cz = int(x) // 16 * 16, int(z) // 16 * 16
        pts = []
        for dx in (-16, 0, 16):
            for dz in (-16, 0, 16):
                self.forceloads.add((cx + dx, cz + dz))
                pts.append((cx + dx, cz + dz))
        return [f"forceload add {px} {pz}" for px, pz in pts]

    def preload_rect(self, x1, z1, x2, z2):
        """forceload a rectangle (inclusive block coordinates) as one command; halt removes the chunks again.  The whole cage is a
        rectangle of 48 chunks: loading it keeps every setblock and summon of a scene in a loaded chunk wherever the player stands."""
        for cx in range(int(x1) // 16 * 16, int(x2) // 16 * 16 + 1, 16):
            for cz in range(int(z1) // 16 * 16, int(z2) // 16 * 16 + 1, 16):
                self.forceloads.add((cx, cz))
        return [f"forceload add {int(x1)} {int(z1)} {int(x2)} {int(z2)}"]

    def all_scheduled(self):
        out = list(self.fx_scheduled)
        for s in self.scenes:
            out += s.scheduled
        return out


# --------------------------------------------------------------------------------------------------- command helpers
def cast_summon(cid, x, y, z, yaw=0.0):
    """Summon a character at a place, turned to `yaw`."""
    return f'execute positioned {num(x)} {num(y)} {num(z)} rotated {num(yaw, 2)} 0 run function {NS}:cast/summon {{id:"{cid}"}}'


def cast_scale(cid, scale):
    """Make a character bigger or smaller (the `scale` attribute; a fresh summon is back at 1.0, so call it after every summon)."""
    return f'function {NS}:cast/scale {{id:"{cid}",scale:{num(scale, 3)}}}'


def cast_remove(cid):
    return f'function {NS}:cast/remove {{id:"{cid}"}}'


def cast_look(cid, mode="player"):
    return f'function {NS}:cast/look {{id:"{cid}",mode:"{mode}"}}'


def cast_mount(cid, role):
    return f'function {NS}:cast/mount {{id:"{cid}",tag:"angel.seat_{role}"}}'


def cast_pose(cid, pose):
    return f'function {NS}:cast/pose {{id:"{cid}",pose:"{pose}"}}'


def tp_player(x, y, z):
    """Move the player without touching his head: no rotation is passed, so none is forced."""
    return f"tp {P()} {num(x)} {num(y)} {num(z)}"


def ride_passenger():
    return [f"ride {P()} mount @e[tag=angel.seat_passenger,limit=1]", sset("#ride", 1)]


def dismount_player():
    return [sset("#ride", 0), f"ride {P()} dismount"]


def title(main, sub=None, color="white", fade_in=15, stay=60, fade_out=25):
    cmds = [f"title {PA()} times {fade_in} {stay} {fade_out}"]
    if sub:
        cmds.append(f'title {PA()} subtitle {json.dumps({"text": sub, "color": "gray"}, ensure_ascii=True)}')
    cmds.append(f'title {PA()} title {json.dumps({"text": main, "color": color}, ensure_ascii=True)}')
    return cmds


def actionbar(text, color="gray"):
    return f'title {PA()} actionbar {json.dumps({"text": text, "color": color}, ensure_ascii=True)}'


def play_at(sound, x, y, z, vol=1.0, pitch=1.0, minvol=0.0, source="master"):
    return f"playsound {sound} {source} {PA()} {num(x)} {num(y)} {num(z)} {num(vol)} {num(pitch)} {num(minvol)}"


def play_player(sound, vol=1.0, pitch=1.0, source="master"):
    return f"execute at {P()} run playsound {sound} {source} {PA()} ~ ~ ~ {num(vol)} {num(pitch)} 0"
