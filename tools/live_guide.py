"""A stopgap guide for a live session: marks the place the story is waiting for the player to reach.

    python tools\\live_guide.py

Every second it reads which step the story is on, looks in that step's poll function for the position it tests
the player against, and keeps one floating "Walk here" label with a column of light at that spot. Steps that
wait for something else (a line, a look, an answer) show nothing. The story's own objective system replaces this.
"""
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rcon import Rcon

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STORY = os.path.join(ROOT, "datapack", "angel", "data", "angel", "function", "story")
NEAR = re.compile(r"positioned (-?[\d.]+) (-?[\d.]+) (-?[\d.]+) if entity @a\[limit=1,distance=\.\.([\d.]+)\]")
LABEL = ('summon text_display {x} {y} {z} {{billboard:"center",see_through:1b,shadow:1b,background:1610612736,'
         'brightness:{{sky:15,block:15}},text:{{text:"\\u25bc  Walk here  \\u25bc",color:"yellow",bold:1b}},'
         'transformation:{{left_rotation:[0f,0f,0f,1f],right_rotation:[0f,0f,0f,1f],translation:[0f,0f,0f],'
         'scale:[{s}f,{s}f,{s}f]}},Tags:["angel.guide"]}}')


def score(r, name):
    m = re.search(r"has (-?\d+)", r.cmd(f"scoreboard players get {name} angel.story"))
    return int(m.group(1)) if m else None


def target(scene, step):
    """The first place this step's poll tests the player against, or None."""
    try:
        text = open(os.path.join(STORY, f"s{scene}", f"p{step}.mcfunction"), encoding="utf-8").read()
    except OSError:
        return None
    m = NEAR.search(text)
    return tuple(float(v) for v in m.groups()[:3]) if m else None


def main():
    r = Rcon()
    shown = None
    while True:
        try:
            scene, step = score(r, "#scene"), score(r, "#step")
            want = target(scene, step) if scene and step is not None else None
            if want != shown:
                r.cmd("kill @e[tag=angel.guide]")
                if want:
                    x, y, z = want
                    r.cmd(LABEL.format(x=x, y=y + 3.2, z=z, s=3))
                shown = want
                print(time.strftime("%H:%M:%S"), "scene", scene, "step", step, "->", want, flush=True)
            if want:
                x, y, z = want
                r.cmd(f"particle minecraft:end_rod {x} {y + 6} {z} 0.15 6 0.15 0 40 force @a")
        except (OSError, ConnectionError):
            time.sleep(3)
            try:
                r = Rcon()
            except OSError:
                pass
        time.sleep(1)


if __name__ == "__main__":
    main()
