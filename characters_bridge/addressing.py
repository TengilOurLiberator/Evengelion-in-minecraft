"""Who is Shinji talking to? Pure functions, no I/O, so they can be tested without a game.

Order of rules (first that gives an answer wins):
  1. a name spoken in the utterance ("Misato", "Doctor Akagi", "Father, ...", "Rei"), if that character can hear him
  2. gaze: the in-person character he is looking at (a cone around where his head points)
     2a'. (only while the story holds for an answer) the character who asked the question
     2b. a phone/intercom conversation in progress: the last speaker, if they are voice-only
     2c. otherwise the nearest in-person character within address_range
  3. whoever spoke last, if they can still hear him
  4. last resort: any voice-only character, else the nearest in-person one at any distance
  nobody present -> None (silence)
"""
import os
import math
import os
import re

import os
from config import ALIASES, CHARACTERS, IN_PERSON, SETTINGS, VOICE_ONLY

_NOT_VOCATIVE = {"my", "your", "the", "a", "his", "her", "our", "that", "this", "their", "said", "says", "about", "like"}


def _tokens(text):
    """[(token, start_in_chars)] lower-cased, keeping hyphenated names whole, plus the text for comma checks."""
    return [(m.group(0).lower(), m.start()) for m in re.finditer(r"[A-Za-z][A-Za-z'-]*", text)]


def _fuzzy(token, word):
    if len(token) < 5 or len(word) < 5 or abs(len(token) - len(word)) > 1:
        return False
    # one-letter difference (speech-to-text slips: Misato/Mizato, Ritsuko/Ritzuko, Gendo/Gando)
    from difflib import SequenceMatcher
    return SequenceMatcher(None, token, word).ratio() >= 0.83


def mentions(text, who):
    """Position (token index) of the first spoken address of `who` in text, or None."""
    toks = _tokens(text)
    words = [t for t, _ in toks]
    if not words:
        return None
    al = ALIASES[who]
    for i, (w, start) in enumerate(toks):
        prev = words[i - 1] if i else ""
        if w in al["strong"] or any(_fuzzy(w, s) for s in al["strong"] if len(s) >= 5):
            return i
        if w in al["kin"] and prev not in _NOT_VOCATIVE:
            return i
        if w in al["weak"]:
            after = text[start + len(w):start + len(w) + 2].lstrip()
            comma_after = after.startswith(",")
            at_edge = i == 0 or i == len(words) - 1
            if at_edge or comma_after:
                return i
    # two-word weak aliases ("ray ayanami", "mr sato")
    low = " ".join(words)
    for s in al["weak"]:
        if " " in s and s in low:
            return low[:low.index(s)].count(" ")
    return None


def named(text, can_hear):
    """The earliest-mentioned character among those who can hear him, or None."""
    hits = [(mentions(text, c), c) for c in CHARACTERS if c in can_hear]
    hits = [(i, c) for i, c in hits if i is not None]
    return min(hits)[1] if hits else None


def look_vector(yaw, pitch):
    y, p = math.radians(yaw), math.radians(pitch)
    return (-math.sin(y) * math.cos(p), -math.sin(p), math.cos(y) * math.cos(p))


def gaze_candidates(player, rotation, chars, cfg=SETTINGS):
    """[(angle_degrees, distance, id)] for in-person characters inside the gaze cone, best first."""
    if not player or not rotation:
        return []
    eye = (player[0], player[1] + cfg["eye_height"], player[2])
    look = look_vector(*rotation)
    out = []
    for c, pos in chars.items():
        target = (pos[0], pos[1] + cfg["body_height"], pos[2])
        d = (target[0] - eye[0], target[1] - eye[1], target[2] - eye[2])
        dist = math.sqrt(sum(v * v for v in d))
        if dist < 0.05 or dist > cfg["gaze_range"]:
            continue
        cos = max(-1.0, min(1.0, sum(a * b for a, b in zip(look, d)) / dist))
        angle = math.degrees(math.acos(cos))
        if angle <= cfg["gaze_degrees"] + math.degrees(math.atan2(0.5, dist)):
            out.append((angle, dist, c))
    return sorted(out)


def horizontal_distance(a, b):
    return math.hypot(a[0] - b[0], a[2] - b[2])


def resolve(text, present, player=None, rotation=None, chars=None, last_speaker=None, cfg=SETTINGS, asker=None):
    """-> (character id | None, reason). `present` is {id: 0|1|2}; `chars` {id: pos} for in-person ones.
    `asker`: while the story holds for an answer, the character who put the question; they are who he is most likely
    answering when he neither names nor looks at anyone."""
    chars = chars or {}
    can_hear = [c for c in CHARACTERS if present.get(c, 0) > 0]
    if not can_hear:
        return None, "nobody is present"

    c = named(text, can_hear)
    if c:
        return c, "named in the utterance"

    if os.environ.get("ANGEL_COMMENTARY") == "1":
        # he is recording and talks to his audience: answer only when the story is waiting for him, or he says a name
        if asker and present.get(asker, 0) > 0:
            return asker, "the one who asked"
        return None, "commentary (no name spoken, no question pending)"

    gaze = gaze_candidates(player, rotation, chars, cfg)
    if gaze:
        return gaze[0][2], f"looking at them ({gaze[0][0]:.0f} deg, {gaze[0][1]:.1f} blocks)"

    if asker and present.get(asker, 0) > 0:
        return asker, "the one who asked"

    if last_speaker and present.get(last_speaker) == VOICE_ONLY:
        return last_speaker, "answering the voice on the line"

    if player and chars:
        near = sorted((horizontal_distance(player, p), c) for c, p in chars.items())
        if near and near[0][0] <= cfg["address_range"]:
            return near[0][1], f"nearest ({near[0][0]:.1f} blocks)"

    if last_speaker and present.get(last_speaker, 0) > 0:
        return last_speaker, "spoke last"

    voices = [c for c in can_hear if present[c] == VOICE_ONLY]
    if voices:
        return voices[0], "only a voice is available"
    if player and chars:
        near = sorted((horizontal_distance(player, p), c) for c, p in chars.items())
        if near:
            return near[0][1], f"nearest, far away ({near[0][0]:.1f} blocks)"
    in_person = [c for c in can_hear if present[c] == IN_PERSON]
    return (in_person[0], "somebody is here") if in_person else (can_hear[0], "somebody can hear")
