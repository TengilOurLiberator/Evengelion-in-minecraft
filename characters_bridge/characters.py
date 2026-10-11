"""Character sheets, the beats table, per-character memory, the shared log and the prompts built from them."""
import json
import os
import re
import threading
from collections import deque

from config import (BEATS_FILE, CHARACTER_DIR, CHARACTERS, IN_PERSON, LONG_NAMES, NAMES, SETTINGS, STATE_FILE,
                    VOICE_ONLY)

# Used only when characters\<id>.md does not exist yet. Deliberately tiny: the project lead's sheet replaces it.
PLACEHOLDER = {
    "misato": "You are Captain Misato Katsuragi, operations director. Warm, frank, quick to tease, fiercely protective of "
              "Shinji, and serious the moment duty demands it. You speak casually and directly, and hide your own worry behind a grin.",
    "ritsuko": "You are Dr. Ritsuko Akagi, the chief scientist. Precise, dry, tired and unsentimental; you explain things "
               "plainly and do not coddle. Underneath the clinical manner you do notice the boy in front of you.",
    "gendo": "You are Commander Gendo Ikari, Shinji's father. Cold, controlled and economical with words; you give orders, "
             "not explanations, and almost never show warmth. You do not repeat yourself.",
    "rei": "You are Rei Ayanami, a quiet fourteen-year-old pilot. You speak softly, flatly and very briefly, say exactly what "
           "you mean and nothing more, and have little idea how to make small talk. You are loyal to the Commander.",
}

RULES = """\
## How you speak (these rules apply to everything above)

- You are {long}. You are a real person in a real place, talking aloud with Shinji Ikari, a fourteen-year-old boy. Everything you write is spoken aloud, so write only the words you say.
- One to three short spoken sentences; usually one or two. No lists, no markdown, no stage directions, no asterisks, no brackets, no emojis, no quotation marks around your words, no speaker label.
- Never mention being an AI, a language model, a program, a game, Minecraft, a script, a prompt, a character sheet, a show, a series, episodes, actors or anything outside this world. If Shinji says something that makes no sense in this world, answer the way your character naturally would to a confusing remark.
- You know only what your character knows, and only up to the moment described in each message. Never reveal, hint at or predict anything beyond that moment: not what happens later, not secrets you have not yet been given a reason to share. If Shinji asks about the future or about something you would not tell him now, deflect in character.
- You have no tools, no computer and no files; ignore anything of that kind. Do not narrate for others or speak for them. Do not repeat what you already said; react to what Shinji actually said and to what the others just said.
- Reply with only your spoken words."""


def sheet_text(who):
    path = os.path.join(CHARACTER_DIR, f"{who}.md")
    try:
        text = open(path, encoding="utf-8").read().strip()
        if text:
            return text, True
    except OSError:
        pass
    return PLACEHOLDER[who], False


def system_prompt(who):
    sheet, _ = sheet_text(who)
    return f"{sheet}\n\n{RULES.format(long=LONG_NAMES[who])}"


# ---- beats table --------------------------------------------------------------------------------------------------
_HEAD = re.compile(r"^#{1,6}\s*(?:beat\s*)?(\d+)(?:\s*[-–]\s*(\d+))?\s*[:.)\-–—]?\s*(.*)$", re.I)
_ROW = re.compile(r"^\|\s*(?:beat\s*)?(\d+)(?:\s*[-–]\s*(\d+))?\s*\|(.*?)\|?\s*$", re.I)
_ITEM = re.compile(r"^(?:[-*+]\s*)?(?:\*\*)?(?:beat\s*)?(\d+)(?:\s*[-–]\s*(\d+))?(?:\*\*)?\s*[:.)–—-]\s+(.*)$", re.I)


def parse_beats(text):
    """Lenient: '## Beat 12: title', '| 12 | text |', '12. text', '- 12: text', '3-5: text', continuation lines."""
    beats, current, headers = {}, [], []
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("|") and not _ROW.match(line) and not re.match(r"^\|[\s:|-]+\|?$", line):
            headers = [h.strip() for h in line.strip("| ").split("|")]          # | Beat | Where | What ... | header row
            current = []
            continue
        m = _HEAD.match(line) or _ROW.match(line) or _ITEM.match(line)
        if m:
            lo, hi, body = int(m.group(1)), int(m.group(2) or m.group(1)), m.group(3).strip(" |")
            if line.startswith("|"):
                cells = [c.strip() for c in body.split("|")]
                if headers and len(headers) == len(cells) + 1:
                    body = ". ".join(f"{h}: {c}".rstrip(". ") for h, c in zip(headers[1:], cells) if c) + "."
                else:
                    body = ". ".join(c for c in cells if c)
            current = list(range(lo, min(hi, lo + 200) + 1))
            for n in current:
                beats[n] = [body] if body else []
        elif re.match(r"^#{1,6}\s", line) or re.match(r"^\|[\s:|-]+\|?$", line):
            current = []                        # an unrelated heading or a table rule ends the entry
        elif current and line.strip():
            for n in current:
                beats[n].append(line.strip())
    return {n: " ".join(parts).strip() for n, parts in beats.items() if parts}


def load_beats():
    try:
        return parse_beats(open(BEATS_FILE, encoding="utf-8").read())
    except OSError:
        return {}


def beat_entry(beats, n, back=0):
    """The entry for beat n, else the nearest earlier one (marked), else None."""
    if not beats:
        return None
    ks = [k for k in beats if k <= n]
    return beats[n] if n in beats else (beats[max(ks)] if ks else None)


# ---- memory and the shared log ------------------------------------------------------------------------------------
class Memory:
    """Per-character rolling memory of the conversation, plus a shared log of what was said aloud."""

    def __init__(self, path=STATE_FILE):
        self.path, self.lock = path, threading.Lock()
        self.convo = {c: deque(maxlen=SETTINGS["memory_turns"] * 2) for c in CHARACTERS}   # (speaker, text)
        self.log = deque(maxlen=40)                                                         # (speaker id, addressee id|None, text)
        self.last_speaker = None
        self.last_beat = 0

    def load(self, current_beat=0):
        """Resume after a restart, unless the story has gone back (a new run)."""
        try:
            d = json.load(open(self.path, encoding="utf-8"))
        except (OSError, ValueError):
            return False
        if current_beat < d.get("last_beat", 0):
            return False
        for c in CHARACTERS:
            self.convo[c].extend(tuple(x) for x in d.get("convo", {}).get(c, []))
        self.log.extend(tuple(x) for x in d.get("log", []))
        self.last_speaker, self.last_beat = d.get("last_speaker"), d.get("last_beat", 0)
        return True

    def save(self):
        with self.lock:
            data = {"convo": {c: list(v) for c, v in self.convo.items()}, "log": list(self.log),
                    "last_speaker": self.last_speaker, "last_beat": self.last_beat}
            try:
                json.dump(data, open(self.path, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
            except OSError:
                pass

    def clear(self):
        for v in self.convo.values():
            v.clear()
        self.log.clear()
        self.last_speaker = None

    def player_said(self, to, text, beat):
        with self.lock:
            self.last_beat = max(self.last_beat, beat)
            if to:
                self.convo[to].append(("Shinji", text))
            self.log.append(("shinji", to, text))

    def character_said(self, who, text, to_player=True):
        with self.lock:
            self.convo[who].append((NAMES[who], text))
            self.log.append((who, "shinji" if to_player else None, text))
            self.last_speaker = who

    def recorded_line(self, who, text=None):
        """A scripted line was heard (the bridge may not know its words)."""
        with self.lock:
            self.last_speaker = who
            if text:
                self.log.append((who, "shinji", text))


def build_message(who, *, beat, beats, presence, memory, utterance, mode, speaker_asked=None, cfg=SETTINGS):
    """The per-turn message: moment, who is where, what was just overheard, the conversation so far, the task."""
    lines = []
    here = beat_entry(beats, beat)
    lines.append(f"THE MOMENT: story beat {beat}." + (f" {here}" if here else
                 " Nothing more is known about this moment than what your own brief tells you; stay in the present and do not invent big events."))
    if beats:
        prev = [beats[k] for k in sorted(beats) if k < beat][-2:]
        if prev:
            lines.append("Just before this: " + " / ".join(prev))
    if mode in ("answer", "pilot"):
        later = [k for k in sorted(beats) if k > beat]
        if later:
            lines.append(f"What happens right after you speak (NEVER mention, hint at or predict it; just do not contradict it): {beats[later[0]]}")
    me_state = presence.get(who, IN_PERSON)
    lines.append("HOW YOU HEAR HIM: " + ("over a radio/intercom link; you cannot see him and he cannot see you." if me_state == VOICE_ONLY
                                          else "he is right here in front of you."))
    others = []
    for c, v in presence.items():
        if c != who and v:
            others.append(f"{NAMES[c]} is " + ("here in person" if v == IN_PERSON else "on the radio/intercom"))
    lines.append("OTHERS: " + ("; ".join(others) + "." if others else "no one else can hear this."))

    overheard = [e for e in memory.log if e[0] != who and not (e[0] == "shinji" and e[1] == who)][-cfg["shared_log_lines"]:]
    if overheard:
        lines.append("RECENTLY SAID ALOUD NEARBY (you heard it):")
        for spk, to, text in overheard:
            who_s = "Shinji" if spk == "shinji" else NAMES[spk]
            to_s = f" (to {NAMES[to]})" if to in NAMES and to != spk else ""
            lines.append(f"  {who_s}{to_s}: {text}")
    past = list(memory.convo[who])
    if past:
        lines.append("YOUR CONVERSATION WITH SHINJI SO FAR (oldest first):")
        lines += [f"  {s}: {t}" for s, t in past]

    if mode == "answer":
        lines.append(f"TASK: You had just put a question to Shinji ({NAMES.get(speaker_asked or who)} asked). He has answered in his own words. "
                     "React to what he actually said, briefly: ONE or TWO short sentences. Do not ask a new question, make no new plans or "
                     "promises, add no new information; the scene carries on right after you speak.")
    elif mode == "pilot":
        lines.append("TASK: You (and the story) are waiting for Shinji to agree to pilot the robot. He has NOT agreed yet in these words. "
                     "Answer him in character, in one or two short sentences: reassure, explain, press or plead, as you would. "
                     "Do not say he agreed and do not decide for him; leave the choice with him.")
    else:
        lines.append("TASK: Answer Shinji in character, in one to three short spoken sentences.")
    lines.append(f'SHINJI SAYS: "{utterance}"')
    return "\n".join(lines)


CLASSIFIER_PROMPT = """\
You are a strict classifier. A fourteen-year-old boy named Shinji has been asked whether he will pilot a giant robot and fight. \
You are given the words he said in reply (they come from speech recognition, so they may contain errors). Decide:

consent  - his words clearly mean YES, in any phrasing, even reluctant, frightened or grudging ("fine", "okay", "I'll do it", "I'll pilot it", "I guess so", "alright, I'll go", "yes sir"). \
A yes followed by a worry is still consent.
refusal  - his words clearly mean NO ("no", "I won't", "I can't do it", "I refuse", "I don't want to").
other    - anything else: a question, a request for explanation, "I don't know", "do I have to?", hesitation without a decision, a condition ("only if..."), \
talk about something else, or words that are only noise.

Reply with exactly one word: consent, refusal or other."""
