"""What the bridge knows about the story ahead of time: the script (every character line with its direction), the policy (verbatim or
adaptable), the pre-rendered take of every line, and the step listing of the scenes (`build_story.py --steps`), which tells it which line the
story will cue next.

The listing is written by the story builder; it is regenerated here when it is missing or older than the story's sources.
"""
import json
import os
import subprocess
import sys
import threading

import line_policy
from config import CHARACTERS, NAMES, PROJECT

TOOLS_VOICES = os.path.join(PROJECT, "tools", "voices")
if TOOLS_VOICES not in sys.path:
    sys.path.append(TOOLS_VOICES)

STORY_TOOLS = os.path.join(PROJECT, "tools", "story")
FINAL_DIR = os.path.join(PROJECT, "voices", "final")
STEPS_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cache", "steps.json")
PY = sys.executable


def code_to_id(code):
    """#line (scene * 100 + number) -> '2.03'"""
    return f"{code // 100}.{code % 100:02d}"


def id_to_code(lid):
    s, n = lid.split(".")
    return int(s) * 100 + int(n)


class Line:
    def __init__(self, rec):
        self.id = rec["id"]
        self.speaker = rec["speaker"].lower()
        self.text = rec["text"]
        self.direction = rec["direction"]
        self.nonverbal = rec["nonverbal"]
        self.scene = int(self.id.split(".")[0])

    @property
    def human(self):
        return self.speaker in CHARACTERS

    @property
    def verbatim(self):
        return (not self.human) or line_policy.is_verbatim(self.id) or self.nonverbal

    @property
    def words(self):
        import re
        return re.findall(r"[A-Za-z0-9']+", self.text)

    @property
    def keep(self):
        return line_policy.keep_words(self.id)


class Book:
    """The script and the pre-rendered takes."""

    def __init__(self, script_path=None):
        import script_lines
        self.lines = {}
        self.order = []
        for rec in script_lines.parse(script_path or os.path.join(PROJECT, "script.md")):
            ln = Line(rec)
            self.lines[ln.id] = ln
            self.order.append(ln.id)
        self._wav = {}
        self._lock = threading.Lock()

    def human(self):
        return [self.lines[i] for i in self.order if self.lines[i].human]

    def final_path(self, lid):
        return os.path.join(FINAL_DIR, self.lines[lid].speaker.upper(), lid + ".wav")

    def verbatim_wav(self, lid):
        """The pre-rendered TTS take of the line (effects and loudness included), float32 mono 48 kHz; None if there is none yet."""
        with self._lock:
            if lid in self._wav:
                return self._wav[lid]
        p = self.final_path(lid)
        if not os.path.isfile(p):
            return None
        import soundfile as sf
        data, sr = sf.read(p, dtype="float32", always_2d=True)
        wav = data.mean(axis=1)
        if sr != 48000:
            from math import gcd
            from scipy.signal import resample_poly
            g = gcd(48000, sr)
            wav = resample_poly(wav, 48000 // g, sr // g).astype("float32")
        with self._lock:
            self._wav[lid] = wav
        return wav

    def verbatim_seconds(self, lid):
        w = self.verbatim_wav(lid)
        return len(w) / 48000.0 if w is not None else None


# ---- the step listing ---------------------------------------------------------------------------------------------
def _stale(path):
    if not os.path.isfile(path):
        return True
    t = os.path.getmtime(path)
    for root, _, files in os.walk(STORY_TOOLS):
        for f in files:
            if f.endswith(".py") and os.path.getmtime(os.path.join(root, f)) > t:
                return True
    return os.path.getmtime(os.path.join(PROJECT, "script.md")) > t


def load_steps(path=STEPS_JSON, rebuild=None, log=print):
    """-> {scene: [step dict]}; rebuilds the listing with build_story.py --steps when it is missing or older than the story's sources."""
    if rebuild or (rebuild is None and _stale(path)):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        log("   writing the story's step listing (build_story.py --steps) ...")
        r = subprocess.run([PY, os.path.join(STORY_TOOLS, "build_story.py"), "--steps", path, "--steps-only", "--quiet"],
                           capture_output=True, text=True, cwd=STORY_TOOLS)
        if r.returncode or not os.path.isfile(path):
            raise RuntimeError("could not write the step listing:\n" + (r.stdout + r.stderr)[-1500:])
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    steps = {int(k): v for k, v in data.items() if not k.startswith("_")}
    steps["_meta"] = data.get("_meta", {})
    return steps


class Story:
    """The scenes as a graph of steps, for looking ahead."""

    def __init__(self, steps):
        self.meta = steps.pop("_meta", {}) if isinstance(steps, dict) else {}
        self.steps = steps

    def get(self, scene, i):
        s = self.steps.get(scene)
        return s[i] if s is not None and 0 <= i < len(s) else None

    def successors(self, scene, i):
        """[(scene, step)] that can follow step i of `scene` (a branch has two, a hand-over goes to the next scene's step 0)."""
        st = self.get(scene, i)
        if st is None:
            return []
        k = st["kind"]
        if k == "goto":
            return [(scene, st["target"])]
        if k == "branch":
            return [(scene, st["target"]), (scene, i + 1)]
        if k == "handover":
            return [(st["to"], 0)] if st["to"] in self.steps else []
        return [(scene, i + 1)] if self.get(scene, i + 1) is not None else []

    def ahead(self, scene, i, max_lines=8, max_steps=4000):
        """Walk forward from (scene, i) (the step now current): the character-or-base lines the story will cue, in walking order, as
        [{'line': id, 'scene': s, 'step': j, 'blocked': bool, 'wait_before': (scene, step) or None}].  `blocked` = a wait lies between now and the
        line (what the player will say there is not known yet).  Both ways of a branch are followed."""
        out, seen = [], set()
        frontier = [((scene, i), False, None)]
        steps = 0
        while frontier and len(out) < max_lines and steps < max_steps:
            nxt = []
            for pos, blocked, wait_pos in frontier:
                if pos in seen:
                    continue
                seen.add(pos)
                steps += 1
                st = self.get(*pos)
                if st is None:
                    continue
                if st["kind"] == "say" and st["line"]:
                    out.append({"line": st["line"], "scene": pos[0], "step": pos[1], "blocked": blocked, "wait_before": wait_pos})
                if st["kind"] == "wait":
                    blocked, wait_pos = True, pos
                for s in st.get("nudge_lines", []) + st.get("nag_lines", []):
                    out.append({"line": s, "scene": pos[0], "step": pos[1], "blocked": True, "wait_before": pos, "nudge": True})
                for succ in self.successors(*pos):
                    nxt.append((succ, blocked, wait_pos))
            frontier = nxt
        return out

    def segment(self, scene, i, max_lines=12):
        """The lines the story says from step i on until the next wait (or the end of the walk): [line ids]. Follows hand-overs, not waits."""
        out, pos, seen = [], (scene, i), set()
        while pos and pos not in seen and len(out) < max_lines:
            seen.add(pos)
            st = self.get(*pos)
            if st is None or st["kind"] == "wait":
                break
            if st["kind"] == "say" and st["line"]:
                out.append(st["line"])
            succ = self.successors(*pos)
            pos = succ[0] if succ else None
            if st["kind"] == "branch":
                pos = succ[1] if len(succ) > 1 else succ[0]          # the main line of the story (the branch not taken)
        return out
