"""The spoken lines: parsed from script.md, timed from voices/durations.json, matched to the sound events in
pack/angel-resources/assets/angel/sounds.json, and written as `angel:say/<id_underscored>` functions.

A line function:
  * plays the sound for the player, positioned at the speaker's entity when the character is present in person
    (#present_<id> == 1 and the entity exists), otherwise at the player (telephone, radio, public address, base);
  * sets #talking 1 and #line_left to the duration (the tick function counts it down and sets #talking back to 0);
  * sets #lastspoke / #speaker for the four characters (BASE leaves them alone);
  * works silently when the recording does not exist yet (the text is then shown in chat so a tester can follow).
"""
import json
import os
import re

from core import (CFG, CHARACTERS, DURATIONS, NS, OBJ, P, SCRIPT, SOUNDS, T, sset, PA)

LINE_RE = re.compile(r"^\*\*(?P<spk>[A-Z]+)\*\*\s+`(?P<id>\d+\.\d+)`\s*(?P<rest>.*)$")
DIR_RE = re.compile(r"\s*\*\((?P<dir>[^)]*)\)\*\s*$")
WORDS_PER_SEC = 2.5
MIN_PAD = 0.5


class Line:
    def __init__(self, lid, speaker, text, direction, section):
        self.id = lid                      # "1.04"
        self.speaker = speaker             # "misato" | "ritsuko" | "gendo" | "rei" | "base"
        self.text = text
        self.direction = direction
        self.scene = int(lid.split(".")[0])
        self.num = int(lid.split(".")[1])
        self.section = section             # stage-direction context ("If you stand there:" ...)
        self.seconds = None
        self.estimated = False
        self.event = None                  # sound event name or None when there is no recording
        self.has_sound = False

    @property
    def key(self):
        return self.id.replace(".", "_")

    @property
    def ticks(self):
        # a few ticks of tail so the next line never starts over the last syllable
        return T(self.seconds) + 4

    @property
    def fn(self):
        return f"{NS}:say/{self.key}"

    @property
    def charid(self):
        return CHARACTERS.index(self.speaker) + 1 if self.speaker in CHARACTERS else 0


def parse_script(path=SCRIPT):
    lines = {}
    order = []
    section = ""
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.rstrip("\n")
            if raw.startswith("> "):
                section = raw[2:].strip()
            m = LINE_RE.match(raw)
            if not m:
                continue
            rest = m.group("rest").strip()
            direction = ""
            d = DIR_RE.search(rest)
            if d:
                direction = d.group("dir").strip()
                rest = rest[:d.start()].strip()
            ln = Line(m.group("id"), m.group("spk").lower(), rest, direction, section)
            lines[ln.id] = ln
            order.append(ln.id)
    return lines, order


def load_lines(warn=print):
    lines, order = parse_script()
    with open(DURATIONS, encoding="utf-8") as f:
        durations = json.load(f)
    sounds = {}
    if os.path.isfile(SOUNDS):
        with open(SOUNDS, encoding="utf-8") as f:
            sounds = json.load(f)
    for lid in order:
        ln = lines[lid]
        if lid in durations:
            ln.seconds = float(durations[lid])
        else:
            words = len(re.findall(r"[A-Za-z0-9']+", ln.text))
            ln.seconds = round(max(1.0, words / WORDS_PER_SEC + MIN_PAD), 2)
            ln.estimated = True
            warn(f"warning: line {lid} ({ln.speaker}) has no duration in voices/durations.json; "
                 f"estimated {ln.seconds:.2f}s from {words} words")
        ev = f"line.{ln.speaker}.{ln.key}"
        if ev in sounds:
            ln.event = f"{NS}:{ev}"
            ln.has_sound = True
        else:
            warn(f"note: line {lid} has no sound event {ev} yet; it will run silently (text shown in chat)")
    return lines, order


COLORS = {"misato": "gold", "ritsuko": "aqua", "gendo": "red", "rei": "light_purple", "base": "gray"}
NAMES = {"misato": "Misato", "ritsuko": "Ritsuko", "gendo": "Gendo", "rei": "Rei", "base": "NERV"}


def say_function(ln):
    """The commands of angel:say/<key>."""
    out = [f"# {ln.id} {ln.speaker.upper()} ({ln.seconds:.2f}s{', estimated' if ln.estimated else ''}) {ln.text}"]
    out += [sset("#talking", 1), sset("#line_left", ln.ticks), sset("#line", ln.scene * 100 + ln.num)]
    if ln.speaker in CHARACTERS:
        out += [sset("#lastspoke", ln.charid), sset("#speaker", ln.charid)]
    if ln.has_sound:
        out.append(sset("#played", 0))
        if ln.speaker in CHARACTERS:
            tagsel = f"@e[tag=angel.{ln.speaker},tag=angel.char,limit=1]"
            # in person: the sound comes from the character (volume 2.5 reaches 40 blocks; the minimum volume keeps a far voice, like
            # the commander's in the booth, audible and in the right direction)
            out.append(f"execute if score #present_{ln.speaker} {OBJ} matches 1 as {tagsel} at @s "
                       f"store success score #played {OBJ} run playsound {ln.event} voice {PA()} ~ ~1.6 ~ 2.5 1 0.7")
        out.append(f"execute if score #played {OBJ} matches 0 at {P()} "
                   f"run playsound {ln.event} voice {PA()} ~ ~ ~ 1 1 1")
    show_text = "tellraw @a " + json.dumps({"text": f"<{NAMES[ln.speaker]}> {ln.text or '(' + ln.direction + ')'}",
                                            "color": COLORS[ln.speaker]}, ensure_ascii=True)
    if ln.has_sound:
        out.append(f"execute if score #subtitles {OBJ} matches 1 run {show_text}")
    else:
        out.append(show_text)
    return out


def write_lines(out, lines):
    for ln in lines.values():
        out.function(f"say/{ln.key}", say_function(ln))
