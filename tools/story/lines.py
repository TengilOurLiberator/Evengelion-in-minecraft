"""The spoken lines: parsed from script.md, timed from voices/durations.json, matched to the sound events in
pack/angel-resources/assets/angel/sounds.json, and written as `angel:say/<id_underscored>` functions.

Two kinds of function per line:

  angel:say/file/<key>   plays the pre-rendered file (voices/final -> the resource pack): the sound for the player, positioned at the speaker's entity
                         when the character is present in person (#present_<id> == 1 and the entity exists), otherwise at the player (telephone, radio,
                         public address, base); sets #talking 1 and #line_left to the duration (the tick function counts it down and sets #talking back
                         to 0); sets #lastspoke / #speaker for the four characters (BASE leaves them alone); works silently when the recording does not
                         exist yet (the text is then shown in chat so a tester can follow).  The fight's barks, the BASE lines and the fallback use this.
  angel:say/<key>        what the story's `say` step runs.  BASE: the same as file/<key>.  MISATO, RITSUKO, GENDO, REI: THE HANDSHAKE WITH THE VOICE BRIDGE
                         (characters_bridge): while the bridge's heartbeat is alive the line is not played by the game but CUED -- see below -- and otherwise
                         the file plays exactly as it always did.

The handshake (all scores on angel.story):

  #bridge_hb     written by the bridge (set to 20 every quarter second); the tick function counts it down.  Above 0 = a bridge is connected.
  #live_ok       1 (default): a connected bridge performs the lines; 0: the pre-rendered files always play (angel:story/bridge_off / bridge_on)
  say/<key>      #line = scene * 100 + number.  If the bridge is connected and #live_ok is 1: #live 1, #cue_n += 1, #cue = #cue_n * 1000 + #line (ONE
                 number the bridge reads in one command), #talking 1, #lastspoke / #speaker, and #line_left = the file's duration + 3 s (the WATCHDOG:
                 with nobody to answer the line is released by the clock).  Otherwise #live 0 and say/file/<key> runs.
  the bridge     reads #cue, performs the line, and when its audio is about to start runs  `function angel:say/claim {n:<#cue_n>,ticks:<real length>}`
                 which writes #cue_ack = n and #line_left = the REAL duration in ticks (+ the 4-tick tail every line has).
  t_line (tick)  counts #line_left down and sets #talking 0 at zero: the ENGINE owns the end of a line, so a bridge that dies mid-line cannot hold the
                 story -- the clock releases it when the reported duration is up.  A cue that is not claimed within ACK_TICKS (14 = 0.7 s) or whose bridge
                 stops answering (#bridge_hb 0) is taken over by the game: say/fallback plays the pre-rendered file at once (#cue_fb 1; the bridge then
                 skips the cue).
"""
import json
import os
import re

from core import (CFG, CHARACTERS, DURATIONS, NS, OBJ, P, SCRIPT, SOUNDS, T, sset, PA, dispatch_tree)

LINE_RE = re.compile(r"^\*\*(?P<spk>[A-Z]+)\*\*\s+`(?P<id>\d+\.\d+)`\s*(?P<rest>.*)$")
DIR_RE = re.compile(r"\s*\*\((?P<dir>[^)]*)\)\*\s*$")
WORDS_PER_SEC = 2.5
MIN_PAD = 0.5

ACK_TICKS = 14               # a live cue the bridge has not claimed after this many ticks is played by the game itself
WATCHDOG_TICKS = 60          # margin added to the file's duration while a cue waits for its claim
HB_TICKS = 20                # the bridge writes #bridge_hb = HB_TICKS; the game counts it down; alive while above 0


class Line:
    # Which lines a scene's own timing reads (Line.seconds / Line.ticks while the scenes are being built).  A scene that schedules something relative to a
    # line's length ties that line to its pre-rendered duration: it must be VERBATIM (sim.check_timing_bound).
    tracking = False
    touched = set()

    def __init__(self, lid, speaker, text, direction, section):
        self.id = lid                      # "1.04"
        self.speaker = speaker             # "misato" | "ritsuko" | "gendo" | "rei" | "base"
        self.text = text
        self.direction = direction
        self.scene = int(lid.split(".")[0])
        self.num = int(lid.split(".")[1])
        self.section = section             # stage-direction context ("If you stand there:" ...)
        self._seconds = None
        self.estimated = False
        self.event = None                  # sound event name or None when there is no recording
        self.has_sound = False

    @property
    def seconds(self):
        if Line.tracking:
            Line.touched.add(self.id)
        return self._seconds

    @seconds.setter
    def seconds(self, v):
        self._seconds = v

    @property
    def key(self):
        return self.id.replace(".", "_")

    @property
    def code(self):
        """#line: scene * 100 + number (unique: scene 7 has 20 lines)"""
        return self.scene * 100 + self.num

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

    @property
    def live_capable(self):
        return self.speaker in CHARACTERS


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


def file_function(ln):
    """The commands of angel:say/file/<key>: the pre-rendered file, exactly as the line has always played."""
    out = [f"# {ln.id} {ln.speaker.upper()} ({ln.seconds:.2f}s{', estimated' if ln.estimated else ''}) {ln.text}"]
    out += [sset("#talking", 1), sset("#line_left", ln.ticks), sset("#line", ln.code), sset("#live", 0)]
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


def say_function(ln):
    """The commands of angel:say/<key> (what a `say` step and the story's nags run)."""
    if not ln.live_capable:
        return [f"# {ln.id} {ln.speaker.upper()}: the base computer is never performed by the bridge", f"function {NS}:say/file/{ln.key}"]
    live = f"execute if score #live {OBJ} matches 1 run "
    return [f"# {ln.id} {ln.speaker.upper()} ({ln.seconds:.2f}s) {ln.text}",
            sset("#line", ln.code),
            f"function {NS}:say/live_try",                                   # #live 1 and the cue issued when a bridge is connected, else #live 0
            live + sset("#talking", 1),
            live + sset("#line_left", ln.ticks + WATCHDOG_TICKS),            # the watchdog until the bridge claims the cue (then the real length)
            live + sset("#lastspoke", ln.charid),
            live + sset("#speaker", ln.charid),
            f"execute if score #live {OBJ} matches 0 run function {NS}:say/file/{ln.key}"]


def handshake_functions():
    """The functions shared by every live-capable line: {path: [lines]}."""
    f = {}
    f["say/live_try"] = [sset("#live", 0),
                         f"execute if score #live_ok {OBJ} matches 1 if score #bridge_hb {OBJ} matches 1.. run function {NS}:say/cue"]
    f["say/cue"] = [sset("#live", 1), sset("#cue_fb", 0), sset("#cue_wait", 0), sset("#cue_ack", -1), f"scoreboard players add #cue_n {OBJ} 1",
                    f"execute if score #cue_n {OBJ} matches 1000000.. run {sset('#cue_n', 1)}",
                    f"scoreboard players operation #cue {OBJ} = #cue_n {OBJ}",
                    f"scoreboard players operation #cue {OBJ} *= #c1000 {OBJ}",
                    f"scoreboard players operation #cue {OBJ} += #line {OBJ}",
                    f"scoreboard players operation #cue_t {OBJ} = #tick {OBJ}"]               # (the game tick of the cue and of the claim: the latency, measurable in the game)
    # tick: a live line the bridge has not claimed.  The game takes it over when the bridge has gone, or has not answered within ACK_TICKS.
    f["say/unclaimed"] = [f"scoreboard players add #cue_wait {OBJ} 1",
                          f"execute if score #live {OBJ} matches 1 unless score #bridge_hb {OBJ} matches 1.. run function {NS}:say/fallback",
                          f"execute if score #live {OBJ} matches 1 if score #cue_wait {OBJ} matches {ACK_TICKS}.. run function {NS}:say/fallback"]
    f["say/fallback"] = [sset("#live", 0), sset("#cue_fb", 1), f"function {NS}:say/fb/root"]
    f["say/claim"] = [f"$execute if score #live {OBJ} matches 1 if score #talking {OBJ} matches 1 if score #cue_n {OBJ} matches $(n) "
                      f"unless score #cue_ack {OBJ} matches $(n) run function {NS}:say/claimed " + "{n:$(n),ticks:$(ticks)}"]
    f["say/claimed"] = [f"$scoreboard players set #cue_ack {OBJ} $(n)", f"$scoreboard players set #line_left {OBJ} $(ticks)",
                        f"scoreboard players operation #ack_t {OBJ} = #tick {OBJ}"]
    return f


def write_lines(out, lines):
    for ln in lines.values():
        out.function(f"say/file/{ln.key}", file_function(ln))
        out.function(f"say/{ln.key}", say_function(ln))
    for path, body in handshake_functions().items():
        out.function(path, body)
    # the game's own takeover of an unclaimed cue: #line (scene * 100 + number) -> the file
    dispatch_tree(out, "say/fb", "#line", {ln.code: [f"function {NS}:say/file/{ln.key}"] for ln in lines.values() if ln.live_capable})
