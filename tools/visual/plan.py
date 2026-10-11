"""Plans: what to do and where to take pictures.

A plan is JSON (a file, or a name in tools\\visual\\plans\\<name>.json):

    {"name": "gallery", "fov": 90, "render": 24, "width": 1600, "height": 900,
     "setup": [<step>, ...],                       # once, after the world is placed and the player has joined
     "shots": [{"name": "outskirts_start",        # file name (without .png)
                "steps": [<step>, ...],
                "settle": 4,                       # minimum seconds to wait (default 4)
                "max": 25}]}                       # longest wait for the picture to stop changing (default 25)

A step is one of
    "gamemode spectator Tester"                    a server command, over RCON (as the console, so use `execute as Tester`)
    {"enter": "outskirts"}                         function angel:world/enter_<set> as the test player (time, weather, teleport)
    {"tp": "outskirts.street", "off": [0,2,0],     stand there: an anchor name from tools\\world\\anchors.json, or [x,y,z];
       "yaw": 90, "pitch": 5, "look_at": [x,y,z]}  yaw/pitch default to the anchor's; look_at turns the head toward a point
    {"at": "outskirts.angel_spawn", "off": [0,0,0], "yaw": 90, "run": "function angel:angel/summon {height:60}"}
                                                   run a command at that place with that rotation
    {"fn": "visual/cage_lights_on"}                one of the helper functions made for the scratch world (see hqdata.py)
    {"clean": true}                                remove cast and monster (what is loaded around the player)
    {"query": "data get entity @e[tag=angel.rei,limit=1] Pos"}   run a command and print + keep its answer (manifest "queries")
    {"wait": 2.5}                                  seconds
    {"scale": 16}                                  eye-height multiplier used by look_at (the giant is 16)

Anchors are feet positions; the camera is 1.62 * scale higher.
"""
import json
import math
import os
import re
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
PLANS = os.path.join(HERE, "plans")
ANCHORS = os.path.join(ROOT, "tools", "world", "anchors.json")
PLAYER = "Tester"
ERR = re.compile(r"Unknown|Incorrect|Expected|Could not|No entity was found|Failed|not loaded|Invalid|Unrecognized|error", re.I)


def load(plan):
    path = plan if os.path.isfile(plan) else os.path.join(PLANS, plan + ".json")
    return json.load(open(path, encoding="utf-8"))


def look_angles(frm, to):
    dx, dy, dz = to[0] - frm[0], to[1] - frm[1], to[2] - frm[2]
    yaw = math.degrees(math.atan2(-dx, dz))
    pitch = -math.degrees(math.atan2(dy, math.hypot(dx, dz)))
    return round(yaw, 2), round(pitch, 2)


class Runner:
    def __init__(self, srv, log):
        self.srv = srv
        self.anchors = json.load(open(ANCHORS))
        self.log = log
        self.scale = 1.0
        self.warnings = []
        self.queries = []
        self.pos = None

    def say(self, *a):
        self.log(" ".join(str(x) for x in a))

    def cmd(self, c, where=""):
        out = self.srv.cmd(c)
        if out and ERR.search(out):
            self.warnings.append((where, c, out))
            self.say("   !! ", c[:120], "->", out[:160])
        return out

    def resolve(self, ref, off=(0, 0, 0)):
        if isinstance(ref, str):
            a = self.anchors[ref]
            p = (a["x"], a["y"], a["z"], a["yaw"], a["pitch"])
        else:
            p = (ref[0], ref[1], ref[2], 0.0, 0.0)
        return (p[0] + off[0], p[1] + off[1], p[2] + off[2], p[3], p[4])

    def run(self, step, where=""):
        if isinstance(step, str):
            return self.cmd(step, where)
        if "enter" in step:
            self.cmd(f"execute as {PLAYER} run function angel:world/enter_{step['enter']}", where)
        elif "tp" in step:
            x, y, z, yaw, pitch = self.resolve(step["tp"], step.get("off", (0, 0, 0)))
            yaw = step.get("yaw", yaw)
            pitch = step.get("pitch", pitch)
            if "look_at" in step:
                yaw, pitch = look_angles((x, y + 1.62 * self.scale, z), step["look_at"])
            self.cmd(f"execute in minecraft:overworld run tp {PLAYER} {x:.3f} {y:.3f} {z:.3f} {yaw:.2f} {pitch:.2f}", where)
            far = self.pos is None or math.dist(self.pos, (x, y, z)) > 150
            self.pos = (x, y, z)
            # a far jump: give the server time to load the chunks round the new place, or the setblock / summon
            # commands that follow (inside functions their failures are silent) land in unloaded chunks
            # (and the server lights chunks lazily on first load: a set seen for the first time looks dark/blue for
            # up to ~15 s, so a far jump waits long)
            time.sleep(step.get("pause", 16.0 if far else 1.0))
        elif "at" in step:
            x, y, z, yaw, pitch = self.resolve(step["at"], step.get("off", (0, 0, 0)))
            yaw = step.get("yaw", yaw)
            self.cmd(f"execute in minecraft:overworld positioned {x:.3f} {y:.3f} {z:.3f} rotated {yaw:.2f} 0 run {step['run']}", where)
        elif "fn" in step:
            self.cmd(f"execute in minecraft:overworld run function angel:{step['fn']}", where)
        elif "clean" in step:
            self.cmd("function angel:cast/remove_all", where)
            self.cmd("function angel:angel/remove", where)
        elif "query" in step:
            out = self.srv.cmd(step["query"])
            self.queries.append((where, step["query"], out))
            self.say("   ?  ", step["query"][:100], "->", (out or "")[:300])
        elif "wait" in step:
            time.sleep(step["wait"])
        elif "scale" in step:
            self.scale = float(step["scale"])
        else:
            raise ValueError("unknown step " + json.dumps(step))
