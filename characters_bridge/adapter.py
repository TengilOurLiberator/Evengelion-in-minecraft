"""Claude re-voices a scripted line, lightly, in character, given what has actually happened.

The script's text is the INTENT of a line.  By default the line is delivered as written; for the lines that line_policy.py allows (not a cue, not
timing-critical) the bridge asks Claude for a version that fits what Shinji said at the last wait, how long he took, whether the story went
on without him.  Everything Claude returns is checked here before it is allowed anywhere near a voice:

  * about the same length: within 20 % of the script line's words;
  * every fact survives: each number, each capitalised name and the policy's `keep` words are still in the line;
  * nothing new: no digits that were not there, no brackets, stage directions, quotes or talk about being an AI, a game or a script;
  * it is a different line (an unchanged line is simply not adapted: the pre-rendered take plays).
Whatever fails is dropped and the verbatim take is used.
"""
import json
import math
from config import adapt_bounds
import re
import threading
import time

import characters as ch
from config import CHARACTERS, NAMES

SYSTEM = """\
You are the line editor of an interactive drama. A fourteen-year-old boy, Shinji Ikari, has been brought to a secret base; the people around him \
(Misato, Ritsuko, Gendo, Rei) speak scripted lines, and he talks back aloud. You are given SCRIPT LINES that are about to be spoken and what \
actually happened a moment ago. For each one you write how that same person would say that same line NOW, or you leave it as it is.

THE RULES (nothing outranks them)
1. The script line is the intent. Keep its meaning, every fact in it, its job in the conversation (a question stays a question, an order an order), \
and who it is addressed to: if the line speaks to Shinji as "you" it still does, and if it speaks ABOUT him as "he" or "him" to someone else it still \
does (keep the person and the pronouns). Every sentence of the script line must still be there, in the same order, reworded at most: never drop a \
sentence or swap one for a new thought (a question is not replaced by a statement). Never add plot, information, promises, names or numbers. Never \
explain or look ahead.
2. Keep names, numbers and capitalised words exactly. Keep the words listed under keep.
3. About the same length: the new line has within 20 percent of the script line's number of words (never more than 20 percent longer).
4. A light touch, but a real one. Each line should sound as if it were said to THIS boy at THIS moment, not recited. Where he has given you something \
to take up, take it up: pick up a word he used, notice that he answered at once or took a long time or said nothing, soften or sharpen the line to \
match how he answered. Where he has not, give the line the small natural variation a live speaker gives a sentence she has said before: a different \
connecting word, a turn of phrase, a short reaction. Make a small change to most lines; change the least in lines that are pure fact or order. Return \
a line unchanged only if it already could not be said better. Never change more than the 20 percent budget allows.
5. Never contradict the LATER LINES (they are fixed and will be spoken after yours), and never say what they say. Do not repeat the line that was \
just spoken. Whoever was asked a question may already have answered Shinji in her own words: do not answer for her.
6. Each person speaks as in their character notes below: Misato quick and warm; Ritsuko level, dry, exact; Gendo low, few words, states, never \
persuades; Rei very soft, brief, flat. Keep their register.
7. Spoken words only: no stage directions, no brackets, no asterisks, no quotation marks, no emoji, no speaker label. Never mention an AI, a model, \
a script, a game, a show, actors, or anything outside this world.

OUTPUT: only a JSON object that maps each line number you were given to its spoken text, e.g. {"2.03": "..."} -- every line asked for, nothing else.

THE CHARACTER NOTES
"""

BANNED = re.compile(r"\b(AI|artificial|language model|prompt|script|Minecraft|game|episode|series|anime|actor|character sheet)\b", re.I)
NUMBER_WORDS = set("zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen "
                   "twenty thirty forty fifty sixty seventy eighty ninety hundred thousand million billion".split())


def words(text):
    return re.findall(r"[A-Za-z0-9']+", text)


def system_prompt():
    sheets = "\n\n".join(f"### {NAMES[c]}\n{ch.sheet_text(c)[0]}" for c in CHARACTERS)
    return SYSTEM + sheets


def required_words(text, keep=()):
    """Words a re-voiced line must still contain: digits and number words, capitalised words that are not the first word of a sentence, ALL-CAPS
    words, plus the policy's keep words (lower case)."""
    req = set(w.lower() for w in keep)
    for m in re.finditer(r"[A-Za-z0-9']+", text):
        w = m.group(0)
        before = text[:m.start()].rstrip()
        sentence_start = not before or before[-1] in ".!?…" or before.endswith('"')
        if any(c.isdigit() for c in w):
            req.add(w.lower())
        elif w.lower() in NUMBER_WORDS:
            req.add(w.lower())
        elif len(w) > 1 and w.isupper():
            req.add(w.lower())
        elif w[0].isupper() and not sentence_start and w not in ("I", "I'm", "I'll", "I've", "I'd"):
            req.add(w.lower())
    return req


STOP = set("a an the to of in on at it its is are was were be been am i you your we our he him his she her they them their and or but that this these those "
           "do does did not no so as for with from by if then than there here me my us what who whom how when where which will would can could just very "
           "have has had".split())


def sentences_of(text):
    return [s.strip() for s in re.split(r"(?<=[.!?…])\s+", text.strip()) if s.strip()]


def content(s):
    return set(w.lower() for w in words(s) if w.lower() not in STOP)


def lost_sentence(original, new):
    """The first sentence of the script line whose content words are mostly absent from every sentence of the new line (a sentence swapped for a new
    thought), else None.  Sentences of four words or fewer ("Good.", "Keep hold of it.") are exempt: a rewording there is all there is."""
    new_sets = [content(s) for s in sentences_of(new)]
    for s in sentences_of(original):
        a = content(s)
        if len(words(s)) <= 4 or len(a) < 2:
            continue
        best = max((len(a & b) / len(a) for b in new_sets), default=0.0)
        if best < 0.5:
            return s
    return None


def validate(original, new, keep=()):
    """-> (ok, reason, cleaned_text)"""
    if not isinstance(new, str):
        return False, "not text", ""
    t = re.sub(r"\s+", " ", new).strip().strip('"').strip()
    if not t:
        return False, "empty", ""
    if re.search(r"[\[\]\(\)\*{}<>_`]|\n", new.strip()):
        return False, "brackets or markup", ""
    if '"' in t or "“" in t or "”" in t:
        return False, "quotation marks", ""
    if set(m.group(0).lower() for m in BANNED.finditer(t)) - set(m.group(0).lower() for m in BANNED.finditer(original)):
        return False, "talks about something outside the world", ""            # (a word the script line itself has -- "series" in 5.03 -- is its own business)
    n0, n1 = len(words(original)), len(words(t))
    _lo, _hi, _ = adapt_bounds()
    lo, hi = math.ceil(n0 * _lo - 1e-9), math.floor(n0 * _hi + 1e-9)
    if not (lo <= n1 <= hi):
        return False, f"{n1} words, the script line has {n0} (allowed {lo}..{hi})", ""
    have = set(w.lower() for w in words(t))
    missing = sorted(required_words(original, keep) - have)
    if missing:
        return False, f"lost {missing}", ""
    gone = lost_sentence(original, t)
    if gone:
        return False, f"dropped or replaced the sentence {gone!r}", ""
    new_digits = [w for w in words(t) if any(c.isdigit() for c in w)]
    if new_digits and not any(any(c.isdigit() for c in w) for w in words(original)):
        return False, f"new numbers {new_digits}", ""
    if t[-1] not in ".!?…":
        t += "."
    return True, "ok", t


def same_line(a, b):
    norm = lambda s: [w.lower() for w in words(s)]
    return norm(a) == norm(b)


def build_message(items, context, later):
    """items: [(Line, presence_text)], context: dict(log=[...], moment=str), later: [Line]"""
    out = []
    if context.get("log"):
        out.append("WHAT HAS BEEN SAID RECENTLY (oldest first):")
        out += [f"  {l}" for l in context["log"][-10:]]
    out.append("")
    out.append("WHAT JUST HAPPENED: " + context.get("moment", "Nothing in particular; the story simply goes on."))
    out.append("")
    out.append("SCRIPT LINES TO RE-VOICE (in the order they are spoken):")
    for ln, how in items:
        n = len(ln.words)
        out.append(f'  {ln.id}  {NAMES[ln.speaker]} ({how}), {n} words (allowed {math.ceil(n * adapt_bounds()[0] - 1e-9)}..{math.floor(n * adapt_bounds()[1] + 1e-9)}): "{ln.text}"'
                   + (f"   keep: {', '.join(ln.keep)}" if ln.keep else ""))
    fixed = context.get("fixed_between") or []
    if fixed:
        out.append("")
        out.append("LINES IN THE SAME STRETCH THAT CANNOT CHANGE (spoken between yours, in the order of the script):")
        out += [f'  {ln.id}  {NAMES.get(ln.speaker, "NERV")}: "{ln.text}"' for ln in fixed]
    if later:
        out.append("")
        out.append("LATER LINES, FIXED (spoken after yours; never contradict or pre-empt them):")
        out += [f'  {ln.id}  {NAMES.get(ln.speaker, "NERV")}: "{ln.text}"' for ln in later]
    out.append("")
    out.append("Reply with the JSON object only.")
    return "\n".join(out)


def parse_reply(text):
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        return {}
    try:
        d = json.loads(m.group(0))
    except ValueError:
        return {}
    return {str(k): v for k, v in d.items()} if isinstance(d, dict) else {}


class Adapter:
    """One Claude (a Brain) dedicated to re-voicing; never the minds that answer the player, so a live reply is never queued behind it."""

    def __init__(self, brain, log=print):
        self.brain, self.log = brain, log

    def adapt(self, items, context, later):
        """items: [(Line, how)]. -> ({line id: cleaned text}, {line id: reason it was left as written}, seconds)"""
        t0 = time.time()
        msg = build_message(items, context, later)
        try:
            raw = self.brain.ask(msg)
        except Exception as e:                             # a Claude failure is never fatal: the lines play as written
            return {}, {ln.id: f"Claude: {e}" for ln, _ in items}, time.time() - t0
        got = parse_reply(raw)
        ok, left = {}, {}
        for ln, _ in items:
            if ln.id not in got:
                left[ln.id] = "not returned"
                continue
            good, why, text = validate(ln.text, got[ln.id], ln.keep)
            if not good:
                left[ln.id] = why
            elif same_line(ln.text, text):
                left[ln.id] = "unchanged"
            else:
                ok[ln.id] = text
        return ok, left, time.time() - t0
