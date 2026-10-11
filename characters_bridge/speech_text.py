"""Turn a stream of text chunks into clean, speakable sentences (and refuse anything that breaks the fiction)."""
import re

from config import SETTINGS

# Things a character must never say aloud. A sentence containing one is dropped, not spoken.
FORBIDDEN = re.compile(
    r"\bas an ai\b|\blanguage model\b|\bartificial intelligence\b|\bchatbot\b|\bclaude\b|\banthropic\b|\bopenai\b|"
    r"\bminecraft\b|\bvideo ?game\b|\bthe game\b|\bgame ?play\b|\bnpc\b|\bplayer character\b|\bheadset\b|\bvr\b|"
    r"\banime\b|\bmanga\b|\btv show\b|\btelevision (?:show|series)\b|\bthe series\b|\bepisode\b|\bseason\b|\bevangelion\b.*\b(?:anime|show|series)\b|"
    r"\bcharacter sheet\b|\bsystem prompt\b|\bthe prompt\b|\brole-?play\b|\bfictional\b|\bscript\b|\bbeat \d+\b|\bstory beat\b",
    re.I)

_END = re.compile(r"(?<=[.!?…])[\"')\]”]*\s+")


def clean(text):
    """Only what a person would say aloud: no stage directions, speaker labels, markdown, emoji."""
    t = text or ""
    t = re.sub(r"\*[^*]*\*|_[^_]{1,60}_|\[[^\]]*\]|\([^)]*\)|<[^>]*>", " ", t)
    t = re.sub(r"^\s*(?:shinji|misato|ritsuko|gendo|rei|captain katsuragi|dr\.? akagi)\s*:\s*", "", t, flags=re.I)
    t = t.replace("“", "").replace("”", "").replace('"', "").replace("`", "").replace("#", "")
    t = re.sub(r"[\U0001F000-\U0001FFFF☀-➿]", "", t)
    t = re.sub(r"\s+", " ", t).strip(" -")
    return t


def sentences(chunks, max_sentences=None, max_chars=None, min_len=14):
    """Yield cleaned sentences as soon as they are complete. Very short ones are joined to the next.

    Stops after max_sentences / max_chars; the rest of the stream is still consumed by the caller's generator
    cleanup, never spoken."""
    max_sentences = max_sentences or SETTINGS["max_sentences"]
    max_chars = max_chars or SETTINGS["max_reply_chars"]
    buf, count, chars, held, did_early = "", 0, 0, "", False

    def emit(raw):
        nonlocal count, chars
        s = clean(raw)
        if not s or not re.search(r"[A-Za-z0-9]", s):
            return None
        if FORBIDDEN.search(s):
            return None
        count += 1
        chars += len(s)
        return s

    early = re.compile(r"^(.{18,}?[,;:—])\s+(?=\S)")      # first clause of a long opening sentence

    for chunk in chunks:
        buf += chunk
        while True:
            m = _END.search(buf)
            is_early = False
            if not m and count == 0 and not did_early and not held and len(buf) >= 70:
                # a long first sentence: voice its first clause now so the first sound comes sooner
                m = early.match(buf)
                is_early = did_early = m is not None
            if not m:
                break
            sent, buf = held + buf[:m.end()], buf[m.end():]
            if len(clean(sent)) < min_len:
                held = sent + " "
                continue
            held = ""
            s = emit(sent)
            if s:
                if is_early:
                    count -= 1                  # a clause, not a whole sentence, for the sentence limit
                yield s
            if count >= max_sentences or chars >= max_chars:
                return
    tail = held + buf
    if tail.strip():
        s = emit(tail)
        if s:
            yield s


CONSENT_FAST = re.compile(
    r"^\W*(?:(?:yes|yeah|yep|yup|ok|okay|alright|all right|fine|sure)(?:\W+(?:i will|i'?ll do it|i'?ll do it then|i'?ll pilot it|ma'?am|sir|please))?"
    r"|i(?:'?ll| will) (?:do it|pilot(?: it| the robot)?|get in|go|fight)|i'?ll do it|i will|i'?ll pilot it)\W*$", re.I)

REFUSAL_WORDS = re.compile(r"\b(no|not|never|won'?t|can'?t|cannot|don'?t|refuse|nope)\b", re.I)
YES_WORDS = re.compile(r"\b(yes|yeah|okay|ok|fine|alright|sure|i'?ll do it|i will)\b", re.I)


def consent_heuristic(text):
    """Offline fallback if Claude cannot be reached: consent / refusal / other."""
    if CONSENT_FAST.match(text or ""):
        return "consent"
    if YES_WORDS.search(text or "") and not REFUSAL_WORDS.search(text or ""):
        return "consent"
    return "refusal" if REFUSAL_WORDS.search(text or "") else "other"
