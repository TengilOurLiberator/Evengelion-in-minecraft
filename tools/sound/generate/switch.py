"""switch.py - flip events between the procedural sound and the generated one, by ear.

    python switch.py status                      # every replaced event and which version the pack plays now
    python switch.py sfx.crash generated         # one event
    python switch.py sfx.crash procedural
    python switch.py sfx. procedural             # every replaced event whose name starts with this (sfx., music., amb.)
    python switch.py all procedural              # everything back to the synthesised versions
    python switch.py all generated

Only the .ogg of the event is copied (same file name either way), so sounds.json never changes; a running game picks the file up
on the next resource reload (F3+T) or restart.  Procedural originals live in work/sound_candidates/procedural_backup/<repo path>,
the installed generated files in work/sound_candidates/<event>/cand<k>.ogg (installed.json says which k).
Events that were kept procedural are not in installed.json and are left alone.  `music.decision_loop`/`music.launch_loop` are
separate events from `music.decision`/`music.launch` and switch independently, so switch both together to keep the hand-off seamless
(`music.decision` / `music.launch` as a prefix also catches their loop file).
NOTE: make_sound.py rebuilds the procedural files in place and would overwrite generated ones; after a rebuild run
`python switch.py all generated` to put the generated sounds back.
"""
import hashlib
import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(HERE)))
CAND = os.path.join(ROOT, "work", "sound_candidates")
BACKUP = os.path.join(CAND, "procedural_backup")
INSTALLED = os.path.join(HERE, "installed.json")


def rel(event):
    kind, short = event.split(".", 1)
    return os.path.join("pack", "angel-resources", "assets", "angel", "sounds", kind, short + ".ogg")


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()


def state_of(event, rec):
    pack = os.path.join(ROOT, rel(event))
    if not os.path.exists(pack):
        return "MISSING"
    s = sha(pack)
    if s == rec.get("sha256_generated"):
        return "generated"
    if s == rec.get("sha256_procedural"):
        return "procedural"
    return "UNKNOWN (rebuilt or edited since install)"


def put(src, dst):
    tmp = dst + ".switch.tmp"
    shutil.copyfile(src, tmp)
    os.replace(tmp, dst)


def main(argv):
    if not os.path.exists(INSTALLED):
        sys.exit("installed.json not found: nothing has been installed yet")
    data = json.load(open(INSTALLED, encoding="utf-8"))
    events = data["events"]
    if len(argv) == 1 and argv[0] == "status":
        n = {}
        for ev, rec in sorted(events.items()):
            st = state_of(ev, rec)
            n[st] = n.get(st, 0) + 1
            print(f"{ev:24s} {st:10s} cand{rec['candidate']}  seed {rec.get('seed')}")
        print(n)
        for ev, why in sorted(data.get("kept_procedural", {}).items()):
            print(f"{ev:24s} kept procedural: {why}")
        return
    if len(argv) != 2 or argv[1] not in ("procedural", "generated"):
        sys.exit(__doc__)
    what, to = argv
    todo = [ev for ev in sorted(events) if what == "all" or ev == what or ev.startswith(what)]
    if not todo:
        sys.exit(f"no replaced event matches '{what}'. Replaced events: {', '.join(sorted(events))}")
    for ev in todo:
        rec = events[ev]
        dst = os.path.join(ROOT, rel(ev))
        if to == "procedural":
            src = os.path.join(BACKUP, rel(ev))
        else:
            src = os.path.join(ROOT, rec["source_file"])
        if not os.path.exists(src):
            print(f"{ev:24s} SKIPPED: {src} not found")
            continue
        put(src, dst)
        print(f"{ev:24s} -> {to}  ({os.path.getsize(dst)} bytes)")


if __name__ == "__main__":
    main(sys.argv[1:])
