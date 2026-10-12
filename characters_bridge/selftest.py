"""Offline checks of the logic that needs no Claude, no GPU and no server:  python selftest.py"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import addressing as ad
import characters as ch
import rcon_commands as rc
from fake_rcon import FakeRcon
from speech_text import CONSENT_FAST, clean, consent_heuristic, sentences
from world import World

fails = 0


def check(name, got, want):
    global fails
    ok = got == want
    fails += not ok
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f"   got {got!r} want {want!r}"))


# ---- names ----
ALL = ["misato", "ritsuko", "gendo", "rei"]
for text, want in [
    ("Misato, what is that thing?", "misato"), ("Captain Katsuragi, where are we going", "misato"),
    ("Mizato I'm scared", "misato"), ("Doctor Akagi, is it safe?", "ritsuko"), ("Ritzuko what does it do", "ritsuko"),
    ("Father, why did you call me here", "gendo"), ("Commander, I don't understand", "gendo"),
    ("Rei, are you okay?", "rei"), ("Ayanami, say something", "rei"), ("Ray, are you okay", "rei"),
    ("what are you looking at, ray?", "rei"), ("Rei, tell Misato I said hi", "rei"),
    ("Tell Misato I'm here", "misato"), ("I want to see my father", None), ("The doctor said no", None),
    ("What is that thing", None), ("a ray of light came in through the window", None),
]:
    check(f"name  {text!r}", ad.named(text, ALL), want)
check("name  absent character ignored", ad.named("Misato, help", ["rei", "gendo"]), None)

# ---- gaze / nearest / last speaker ----
fake = FakeRcon(verbose=False)
world = World(fake)
fake.look_at("rei")
st = world.snapshot()
player, rot, chars = world.positions(st)
check("gaze   looking at Rei", ad.resolve("what is this place", st.present, player, rot, chars)[0], "rei")
fake.look_away()
player, rot, chars = world.positions(st)
check("nearest looking away -> Misato (3 blocks)", ad.resolve("what is this place", st.present, player, rot, chars)[0], "misato")
fake.set_score(rc.score_present("misato"), 0)
st = world.snapshot()
player, rot, chars = world.positions(st)
check("absent Misato skipped -> Ritsuko (4 blocks)", ad.resolve("hello?", st.present, player, rot, chars)[0], "ritsuko")
fake.place("ritsuko", 30)
fake.place("rei", 20)
fake.place("gendo", 25)
fake.look_at("gendo")
player, rot, chars = world.positions(st)
check("everyone too far, not in gaze -> last speaker", ad.resolve("hello?", st.present, player, rot, chars, last_speaker="rei")[0], "rei")
fake.set_score(rc.score_present("gendo"), 2)
st = world.snapshot()
player, rot, chars = world.positions(st)
check("voice-only Gendo on the line beats a distant person", ad.resolve("hello?", st.present, player, rot, chars, last_speaker="gendo")[0], "gendo")
check("name wins over gaze", ad.resolve("Rei, hello", st.present, player, rot, chars, last_speaker="gendo")[0], "rei")
check("asker preferred over nearest/last when nothing named or looked at",
      ad.resolve("will you leave her alone?", st.present, player, rot, chars, last_speaker="rei", asker="gendo")[0], "gendo")
for c in ALL:
    fake.set_score(rc.score_present(c), 0)
st = world.snapshot()
check("nobody present -> silence", ad.resolve("hello?", st.present)[0], None)

# ---- rcon strings and parsing ----
check("parse score", rc.parse_score("#beat has 5 [angel.story]"), 5)
check("parse unset score", rc.parse_score("Can't get value of angel.story for #x; none is set"), None)
check("parse pos", rc.parse_pos("Misato has the following entity data: [1.5d, 64.0d, -2.25d]"), (1.5, 64.0, -2.25))
check("parse rotation", rc.parse_rotation("Shinji has the following entity data: [-90.0f, 12.5f]"), (-90.0, 12.5))
check("look vector yaw 90 faces -X", [round(v, 3) for v in ad.look_vector(90, 0)], [-1.0, 0.0, 0.0])
check("tellraw is valid json", rc.subtitle("Rei", 'a "quote"', "aqua").startswith('tellraw @a {"text": "<Rei> a \\"quote\\""'), True)

# ---- beats ----
beats = ch.parse_beats("""# Beats
## Beat 1: arrival
Shinji arrives at the gate.
## 2. The cage
The robot is revealed.
| 3 | Misato asks him to pilot |
| --- | --- |
- 4: Gendo gives the order
5-6: The first fight
7) Aftermath
""")
check("beats parsed", sorted(beats), [1, 2, 3, 4, 5, 6, 7])
check("beat continuation line", beats[1], "arrival Shinji arrives at the gate.")
check("beat range", beats[6], "The first fight")
check("beat fallback to earlier", ch.beat_entry(beats, 99), "Aftermath")

# ---- sentences ----
def chunks(s, n=5):
    return [s[i:i + n] for i in range(0, len(s), n)]

check("sentences streamed", list(sentences(chunks("Come on, Shinji. We don't have much time! Are you ready? One more thing."))),
      ["Come on, Shinji.", "We don't have much time!", "Are you ready?"])
check("short sentence joined", list(sentences(chunks("No. Absolutely not, Shinji. Get some rest."))), ["No. Absolutely not, Shinji.", "Get some rest."])
check("forbidden dropped", list(sentences(chunks("I am an AI language model. Stay close to me."))), ["Stay close to me."])
check("directions removed", clean('*smiles* Misato: "Hello (quietly) there [pause]"'), "Hello there")

# ---- consent shortcuts ----
for t, want in [("okay", "consent"), ("Yes.", "consent"), ("I'll do it", "consent"), ("no", "refusal"), ("I won't", "refusal"),
                ("what is it?", "other"), ("I don't want to", "refusal")]:
    check(f"consent heuristic {t!r}", consent_heuristic(t), want)
check("fast path 'Fine.'", bool(CONSENT_FAST.match("Fine.")), True)
check("fast path rejects 'okay but what is it'", bool(CONSENT_FAST.match("okay but what is it")), False)

# ---- prompts ----
mem = ch.Memory(path=os.path.join(os.environ.get("TEMP", "."), "angel_selftest_state.json"))
mem.player_said("misato", "Where are we?", 3)
mem.character_said("misato", "Almost there.")
mem.recorded_line("gendo", "Report.")
msg = ch.build_message("rei", beat=3, beats=beats, presence={"misato": 1, "ritsuko": 0, "gendo": 2, "rei": 1}, memory=mem,
                       utterance="Hi", mode="answer", speaker_asked="gendo")
check("prompt has beat entry", "Misato asks him to pilot" in msg, True)
check("prompt never leaks later than next beat", "Aftermath" not in msg and "first fight" not in msg, True)
check("prompt shows the overheard line", "Misato: Almost there." in msg, True)
check("system prompt placeholder works", "Rei Ayanami" in ch.system_prompt("rei"), True)

real_dir, ch.CHARACTER_DIR = ch.CHARACTER_DIR, os.path.join(os.environ.get("TEMP", "."), "no_such_dir_for_sheets")
check("missing sheet -> placeholder", [ch.sheet_text(c)[1] for c in ALL], [False] * 4)
check("missing sheet still gives a system prompt", "Gendo" in ch.system_prompt("gendo"), True)
ch.CHARACTER_DIR = real_dir

# ---- re-voiced lines: what the adapter accepts -----------------------------------------------------------------------
import adapter as ad_mod  # noqa: E402

SCRIPT_203 = "Good. That thing behind us, we call an Angel. Don't ask me who chose the name."
check("adapter accepts a light re-voicing", ad_mod.validate(SCRIPT_203, "Good, glad of it. That thing behind us, we call an Angel. Don't ask who chose the name.", ["angel"])[0], True)
for why, text in [("too long", SCRIPT_203 + " Really, truly, I mean it, so there."), ("too short", "Good. That is an Angel."),
                  ("lost the name", "Good. That thing behind us, we call it a monster. Don't ask me who chose the name."),
                  ("brackets", "Good. (smiling) That thing behind us, we call an Angel. Don't ask me who chose the name."),
                  ("meta", "Good. That thing behind us, in this game we call an Angel. Don't ask me who chose it."),
                  ("new number", "Good. That thing behind us, we call an Angel, number 3. Don't ask me who chose it.")]:
    check(f"adapter rejects: {why}", ad_mod.validate(SCRIPT_203, text, ["angel"])[0], False)
S524 = "What did you come all this way for? Look at him. Look at it. Then decide, but decide facing them."
check("adapter rejects: a question swapped for a new thought", ad_mod.validate(S524, "You don't have to say anything yet. Look at him. Look at it. Then decide, facing them.", ["decide"])[0], False)
check("adapter accepts: the same sentences reworded", ad_mod.validate(S524, "What did you come all this way for, Shinji? Look at him. Look at it. Then decide, but decide facing them.", ["decide"])[0], True)
check("adapter: an unchanged line is no adaptation", ad_mod.same_line(SCRIPT_203, SCRIPT_203.upper()), True)
check("adapter reads a JSON reply wrapped in prose", ad_mod.parse_reply('Here you go:\n{"2.03": "Good."}\nThanks'), {"2.03": "Good."})
check("required words: names, numbers, keep", sorted(ad_mod.required_words("Forty-one. With no suit and Unit One ready, Shinji.", ["suit"])), ["forty", "one", "shinji", "suit", "unit"])

# ---- the scripted lines: the step listing, the look-ahead, the handshake with a fake game ---------------------------------
import time  # noqa: E402

import line_policy  # noqa: E402
import storybook  # noqa: E402
from conductor import Conductor  # noqa: E402
from playback import NullMixer  # noqa: E402
from prepare import Preparer  # noqa: E402
from storysim import FakeGame  # noqa: E402

book = storybook.Book()
check("the script has 111 character lines", len(book.human()), 111)
check("every character line is in the policy exactly once",
      sorted(l.id for l in book.human()) == sorted(set(line_policy.VERBATIM) | set(line_policy.ADAPT)) and not (set(line_policy.VERBATIM) & set(line_policy.ADAPT)), True)
check("code <-> id", (storybook.code_to_id(207), storybook.id_to_code("5.44")), ("2.07", 544))
story = storybook.Story(storybook.load_steps(log=lambda m: None))
ahead = story.ahead(2, 0, max_lines=6)
check("look-ahead from the start of scene 2 finds the lines in order", [a["line"] for a in ahead[:4]], ["2.01", "2.02", "2.03", "2.04"])
check("look-ahead: lines after a wait are blocked, before it are not", [a["blocked"] for a in ahead[:4]], [False, False, True, True])
check("segment: the lines up to the next wait", story.segment(2, 0), ["2.01", "2.02"])
check("hand-over: look-ahead crosses into the next scene", any(a["scene"] == 3 for a in story.ahead(2, 100, max_lines=6)), True)


def handshake(speed, claim=True, die_after_claim=False, line="2.03"):
    game = FakeGame(book, speed=speed)
    prep = Preparer(book, verbatim_only=True)
    mixer = NullMixer(speed=speed)
    cond = Conductor(game, book, story, prep, mixer, subtitles=False, log=lambda m: None)
    if claim:
        cond.start(game)
        time.sleep(0.4 / speed)
    t0 = time.time()
    game.say(line)
    time.sleep(0.2 / speed)
    if die_after_claim:
        cond.stop()
    while game.scores["#talking"] == 1 and time.time() - t0 < 30:
        time.sleep(0.01)
    took = (time.time() - t0) * speed
    kinds = [e[1] for e in game.events]
    cond.stop()
    game.close()
    return took, kinds, game, mixer


want = book.verbatim_seconds("2.03")
took, kinds, game, mixer = handshake(6.0)
check("handshake: cue -> claim -> the line lasts the real length and the story waits for it", ("cue" in kinds, "claim" in kinds, "fallback" in kinds, abs(took - (want + 0.25)) < 0.5), (True, True, False, True))
check("handshake: the bridge played it", len(mixer.log) == 1 and abs(mixer.log[0][2] - want) < 0.01, True)
took, kinds, game, mixer = handshake(6.0, claim=False)
check("no bridge: the game plays the file (no cue)", ("cue" in kinds, "file" in kinds), (False, True))
fg = FakeGame(book, speed=6.0)
fg.scores["#bridge_hb"] = 20                                    # a heartbeat but nobody to answer the cue
fg.say("2.03")
t0 = time.time()
while fg.scores["#talking"] == 1 and time.time() - t0 < 20 and "fallback" not in [e[1] for e in fg.events]:
    time.sleep(0.01)
check("a cue nobody claims is taken over by the game within 14 ticks", [e[1] for e in fg.events if e[1] == "fallback"], ["fallback"])
fg.close()
took, kinds, game, mixer = handshake(6.0, die_after_claim=True)
check("bridge killed mid-line: the clock still releases the story", took < want + 1.0, True)

print("\n%d failure(s)" % fails if fails else "\nall checks passed")
sys.exit(1 if fails else 0)
