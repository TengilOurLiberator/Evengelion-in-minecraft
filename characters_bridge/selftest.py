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

print("\n%d failure(s)" % fails if fails else "\nall checks passed")
sys.exit(1 if fails else 0)
