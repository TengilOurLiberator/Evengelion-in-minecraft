"""install.py - put the chosen candidates (choices.json) into the pack.

    python install.py            # install / re-install every choice
    python install.py --dry-run

For each event: refuse if the candidate failed the contract or was rejected for speech; copy the procedural file to
work/sound_candidates/procedural_backup/<repo-relative path> (only if no backup exists yet, so the backup is always the procedural
original); copy the candidate over the pack file (atomic replace); write installed.json (candidate, seed, prompt, hashes, sizes).
sounds.json is NOT touched: the event names and file names are unchanged.
"""
import hashlib
import json
import os
import shutil
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import audio_utils as au
from gen import variant_cfg


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def main():
    dry = "--dry-run" in sys.argv
    ch = json.load(open(os.path.join(HERE, "choices.json"), encoding="utf-8"))
    P = json.load(open(os.path.join(HERE, "prompts.json"), encoding="utf-8"))["events"]
    sj = os.path.join(au.PACK, "sounds.json")
    sj_before = sha(sj)
    out_of = {}                                           # output event -> prompts.json entry
    for ev, e in P.items():
        for o in e.get("outputs", [ev]):
            out_of[o] = (ev, e)
    events = {}
    for ev, (k, why) in sorted(ch["install"].items()):
        src_ev, e = out_of[ev]
        rec = json.load(open(os.path.join(au.CAND, ev, f"cand{k}.json")))
        v = rec.get("verdict", {})
        if rec["fail"] or v.get("reject"):
            sys.exit(f"{ev} cand{k} is not installable: {rec['fail'] or v.get('notes')}")
        cand = os.path.join(au.CAND, ev, f"cand{k}.ogg")
        pack = au.event_file(ev)
        bak = au.backup_file(ev)
        if not os.path.exists(bak):
            if not dry:
                os.makedirs(os.path.dirname(bak), exist_ok=True)
                shutil.copyfile(pack, bak)
        if not os.path.exists(bak) and not dry:
            sys.exit("backup failed for " + ev)
        ek = variant_cfg(e, k)
        gen = json.load(open(os.path.join(au.CAND, "raw", src_ev, "gen.json")))
        parts = {n: g for n, g in gen.items() if n.startswith(("main_k%d_" % k, "build_k%d_" % k, "drive_k%d_" % k))}
        first = next(iter(parts.values()))
        prompt = {n: (g.get("tags") or g.get("prompt")) for n, g in parts.items()}
        events[ev] = dict(candidate=k, engine="ACE-Step 1.5 turbo" if first["engine"] == "ace" else "Stable Audio Open 1.0",
                          seed=first["seed"], seeds={n: g["seed"] for n, g in parts.items()},
                          prompt=prompt, negative_prompt=first.get("neg"), bpm=first.get("bpm"), key=first.get("key"),
                          reason=why, source_file=os.path.relpath(cand, au.ROOT).replace("\\", "/"),
                          raw_files=[f"work/sound_candidates/raw/{src_ev}/{n}" for n in parts],
                          processing=rec["log"], contract=rec["contract"],
                          sha256_generated=sha(cand), sha256_procedural=sha(bak) if os.path.exists(bak) else None,
                          bytes_generated=os.path.getsize(cand), bytes_procedural=os.path.getsize(bak) if os.path.exists(bak) else None)
        if not dry:
            tmp = pack + ".install.tmp"
            shutil.copyfile(cand, tmp)
            os.replace(tmp, pack)
        print(f"{ev:24s} <- cand{k}  {events[ev]['bytes_procedural']} -> {events[ev]['bytes_generated']} bytes")
    if not dry:
        data = dict(written=time.strftime("%Y-%m-%d %H:%M:%S"),
                    note="Events whose pack .ogg is a generated candidate (ACE-Step / Stable Audio Open via ComfyUI). make_sound.py rebuilds the "
                         "procedural files in place and would overwrite these: afterwards run  python switch.py all generated.",
                    events=events, kept_procedural=ch["keep_procedural"])
        json.dump(data, open(os.path.join(HERE, "installed.json"), "w", encoding="utf-8"), indent=1, default=float)
    assert sha(sj) == sj_before, "sounds.json changed"
    print(f"{len(events)} events; sounds.json untouched")


if __name__ == "__main__":
    main()
