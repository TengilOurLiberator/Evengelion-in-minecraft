"""Which scripted lines the bridge may re-voice (ADAPT) and which it must speak exactly as written (VERBATIM).

Every line of MISATO, RITSUKO, GENDO and REI (111) is in exactly one of the two tables; tools/story/sim.py (`build_story.py --check`) fails if one is
missing, listed twice, unknown, or if a scene's own timing reads the length of an ADAPT line (a line a scene schedules something against must be
VERBATIM: the bridge plays its pre-rendered file, so its length is the one the scene was built on).

VERBATIM means the words are the script's AND the audio is the pre-rendered TTS take of this line (voices\\final), played by the bridge without a
fresh synthesis: the duration is exactly durations.json.  Reasons:
  cue      something happens on the line, or the line is the cue for something (a player action, a light, a door, a blast)
  count    the count that the push is timed to
  launch   "Evangelion Unit One: launch!" and the lines the launch is synchronised to
  reveal   "look out of your window": the descent's reveal
  nudge    the consent nudges (they repeat on a cadence, in the same words)
  short    one to five words: there is nothing to vary inside a 20 % budget
  timed    a scene schedules effects against the length of the line (found automatically by the checker, listed here to be explicit)
  callback a later line answers these words, or an earlier line is called back
  staging  the staging is built around this exact beat
  bark     said by the fight (tools/fight), pre-rendered and played by the game itself at once: never cued to the bridge

ADAPT lines map to the extra words ("keep") an adaptation must retain; names, numbers and capitalised words of the script line are always kept.
"""

VERBATIM = {
    "1.04": "cue: she calls him as the car stops (he gets in)",
    "1.06": "nudge: the repeat if he stands there",
    "2.05": "staging: the planes are pulled back; the ridge, the mine",
    "2.06": "cue: 'Down!' is the blast's cue (a silence window follows)",
    "2.07": "short: 'Still with me? Say something.' (the speak prompt appears after it)",
    "2.09": "count: the push is timed to 'One. Two. Three!'",
    "2.12": "timed: the telephone call (scene 2 schedules the drive against it)",
    "2.13": "timed: the telephone call",
    "2.14": "timed: the telephone call",
    "2.16": "timed: the telephone call ends the scene",
    "3.08": "reveal: 'look out of your window' (the Geofront comes into view)",
    "4.07": "short: 'Sorry! Really. Sorry.'",
    "4.08": "short: 'So this is the boy.'",
    "4.15": "callback: question and answer with 4.16-4.18",
    "4.16": "callback: 'one in a billion' is called back by 4.17, 4.18 and 7.17",
    "4.17": "callback: answers 4.16's number",
    "4.18": "callback: answers 4.17",
    "5.04": "short: the single word that turns every head to the booth",
    "5.06": "cue: 'Prepare to launch.'",
    "5.10": "callback: 'One' is a pilot, answering 5.09's 'no pilot' (re-voiced out of context it became 'Unit One': a changed fact)",
    "5.11": "short: 'You are not serious.'",
    "5.15": "short: 'But...'",
    "5.17": "short: 'Yes. I would.'",
    "5.22": "short: 'It has found us.'",
    "5.23": "short: 'Shinji. There is no time.'",
    "5.25": "cue: 'Medical. Wake Rei.' (a handset, Rei is woken)",
    "5.26": "cue: Rei is woken; the commander's decision",
    "5.27": "cue: Rei's 'Yes.' answers it; the gurney is timed to the exchange",
    "5.28": "timed: the gurney arrives as the exchange ends",
    "5.29": "timed: the gurney arrives as the exchange ends",
    "5.31": "staging: no words, a breath (made from noise, not spoken)",
    "5.33": "staging: the one line Ritsuko raises her voice, on the hand's first move",
    "5.35": "short: 'He can do this.'",
    "5.38": "short: 'It's what I'm for.'",
    "5.39": "nudge: the consent nudge (Rei)",
    "5.41": "nudge: the consent nudge, one word",
    "5.42": "short: 'Thank you, Shinji.' (the cue that he agreed)",
    "5.44": "short: 'Why?'",
    "6.10": "cue: 'Forty-one.' is the number on the plug's display",
    "6.12": "cue: 'Begin launch preparations!'",
    "6.16": "timed: the launch sequence (scene 6 schedules the bolts and the charge against it)",
    "6.17": "timed: the launch sequence",
    "6.18": "timed: the launch sequence; 'Hold on to something.'",
    "6.19": "launch: 'Evangelion Unit One: launch!'",
    "7.01": "bark", "7.02": "bark", "7.03": "bark", "7.04": "bark", "7.05": "bark", "7.06": "bark", "7.07": "bark",
    "7.08": "bark", "7.09": "bark", "7.11": "bark", "7.12": "bark", "7.13": "bark", "7.14": "bark", "7.16": "bark",
    "7.17": "bark", "7.18": "bark", "7.20": "bark",
}

ADAPT = {
    "1.05": [],
    "2.01": ["misato"],
    "2.02": ["hurt"],
    "2.03": ["angel"],
    "2.04": ["army"],
    "2.08": ["push"],
    "2.10": [],
    "2.11": ["car"],
    "3.02": ["pass"],
    "3.03": ["test"],
    "3.04": ["nerv", "father"],
    "3.05": [],
    "3.06": [],
    "3.07": [],
    "3.09": [],
    "3.10": [],
    "4.01": [],
    "4.02": [],
    "4.03": ["door"],
    "4.04": ["system"],
    "4.06": [],
    "4.09": [],
    "4.10": [],
    "4.11": [],
    "4.13": [],
    "4.14": [],
    "5.01": ["lights"],
    "5.02": [],
    "5.03": [],
    "5.05": [],
    "5.07": [],
    "5.08": [],
    "5.09": [],
    "5.12": ["inside"],
    "5.13": [],
    "5.14": [],
    "5.16": [],
    "5.18": [],
    "5.19": ["get", "in"],
    "5.20": ["choose", "quickly"],
    "5.24": ["decide"],
    "5.34": [],
    "5.36": [],
    "5.37": [],
    "5.43": [],
    "6.03": [],
    "6.05": ["breathe"],
    "6.06": [],
    "6.11": [],
    "6.21": ["come", "back"],
}


def is_verbatim(lid):
    return lid in VERBATIM or lid not in ADAPT


def reason(lid):
    return VERBATIM.get(lid, "not listed as adaptable: spoken as written")


def keep_words(lid):
    return list(ADAPT.get(lid, []))
