"""EVERY command string the bridge sends to the game lives here, with the parsing of its answer.

This module is the contract with the "angel" datapack. If the datapack changes, change it here and
nowhere else (fake_rcon.py, the text-mode stand-in for the server, reads its patterns from here too).

Scoreboard objective ``angel.story`` holds these fake players:

  read by the bridge
    #beat                 current story beat number
    #wait                 0 nothing pending | 1 story holds for ANY spoken answer | 2 story holds until the player AGREES
    #speaker              who asked: 1 misato, 2 ritsuko, 3 gendo, 4 rei
    #talking              1 while a recorded scripted line plays (the bridge stays quiet / stops talking)
    #present_<id>         0 absent | 1 present in person | 2 voice only (phone/intercom/radio)
    #lastspoke            OPTIONAL: id (1-4) of the character whose recorded line played last
  written by the bridge
    #bridge_speaking      OPTIONAL signal: id (1-4) of the character the bridge is voicing now, 0 when it stops

Entities: characters carry tags ``angel.char`` and ``angel.<id>``. The player is the first player online.
Functions the bridge runs: ``angel:story/answered`` and ``angel:story/consented``.
"""
import json
import re

from config import CHARACTERS

OBJECTIVE = "angel.story"
TAG_CHAR = "angel.char"

FN_ANSWERED = "function angel:story/answered"      # after the speaker has answered while #wait == 1
FN_CONSENTED = "function angel:story/consented"    # the player agreed while #wait == 2

PLAYER = "@a[limit=1]"                              # Shinji: the one player


def tag_of(who):
    return f"angel.{who}"


# ----- scoreboard ----------------------------------------------------------------------------------------------
def score_get(name):
    return f"scoreboard players get {name} {OBJECTIVE}"


def score_set(name, value):
    return f"scoreboard players set {name} {OBJECTIVE} {int(value)}"


SCORE_BEAT, SCORE_WAIT, SCORE_SPEAKER, SCORE_TALKING = "#beat", "#wait", "#speaker", "#talking"
SCORE_LASTSPOKE, SCORE_BRIDGE_SPEAKING = "#lastspoke", "#bridge_speaking"


def score_present(who):
    return f"#present_{who}"


def parse_score(reply):
    """'#beat has 5 [angel.story]' -> 5. Anything else (unset score, unknown objective, no reply) -> None."""
    m = re.search(r"\bhas (-?\d+)", reply or "")
    return int(m.group(1)) if m else None


# ----- positions -----------------------------------------------------------------------------------------------
# Run as the player and from the player's position, so "nearest" is nearest to Shinji and an absent
# (unloaded) character simply returns nothing.
def character_pos(who):
    return (f"execute as {PLAYER} at @s run "
            f"data get entity @e[tag={tag_of(who)},sort=nearest,limit=1] Pos")


def player_pos():
    return f"data get entity {PLAYER} Pos"


def player_rotation():
    return f"data get entity {PLAYER} Rotation"


def parse_pos(reply):
    m = re.search(r"\[\s*(-?[\d.eE+-]+)d,\s*(-?[\d.eE+-]+)d,\s*(-?[\d.eE+-]+)d\s*\]", reply or "")
    return tuple(float(v) for v in m.groups()) if m else None


def parse_rotation(reply):
    """-> (yaw, pitch) in degrees, Minecraft convention (yaw 0 = south/+Z, 90 = west/-X; pitch + = down)."""
    m = re.search(r"\[\s*(-?[\d.eE+-]+)f,\s*(-?[\d.eE+-]+)f\s*\]", reply or "")
    return (float(m.group(1)), float(m.group(2))) if m else None


# ----- speech output -------------------------------------------------------------------------------------------
def subtitle(name, text, color="white"):
    """A line in the game chat (the player is in a headset; this is mostly for debugging and for flat-screen)."""
    return "tellraw @a " + json.dumps({"text": f"<{name}> {text}", "color": color}, ensure_ascii=False)


def bridge_speaking(who):
    """who: character id, or None when the bridge has stopped talking."""
    return score_set(SCORE_BRIDGE_SPEAKING, CHARACTERS.index(who) + 1 if who else 0)
