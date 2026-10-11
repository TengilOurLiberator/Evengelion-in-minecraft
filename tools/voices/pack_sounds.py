"""Encode the finished lines into the resource pack and tell the datapack how long each one is.

    python pack_sounds.py                       # encode what changed, rewrite sounds.json and durations.json
    python pack_sounds.py --force               # re-encode everything
    python pack_sounds.py --speaker GENDO       # encode only this character (json files still cover everyone)
    python pack_sounds.py --prune               # delete oggs whose final wav no longer exists

Reads    D:\\angel-attack\\voices\\final\\<SPEAKER>\\<id>.wav
Writes   D:\\angel-attack\\pack\\angel-resources\\assets\\angel\\sounds\\line\\<speaker>\\<id with . -> _>.ogg   (mono Vorbis, as in Genesis: libvorbis -q:a 6)
         D:\\angel-attack\\pack\\angel-resources\\assets\\angel\\sounds.json      events  angel:line.<speaker>.<id_>
         D:\\angel-attack\\voices\\durations.json                                {"2.01": 3.214, ...}  seconds, from the final wavs

In game:  /playsound angel:line.misato.2_01 voice @a
Other entries already in sounds.json (anything not starting with "line.") are left alone.
pack.mcmeta is not touched.
"""
import argparse
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import common


def duration(path):
    import soundfile as sf
    i = sf.info(path)
    return i.frames / i.samplerate


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--finals", default=common.FINAL_DIR)
    ap.add_argument("--pack", default=common.PACK_DIR)
    ap.add_argument("--durations", default=common.DURATIONS_JSON)
    ap.add_argument("--speaker")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--prune", action="store_true")
    ap.add_argument("--quality", type=int, default=6, help="libvorbis -q:a (Genesis used 6)")
    ap.add_argument("--stream-over", type=float, default=8.0,
                    help="lines longer than this many seconds are marked stream:true in sounds.json")
    a = ap.parse_args()

    only = {s.strip().upper() for s in a.speaker.split(",")} if a.speaker else None
    assets = os.path.join(a.pack, "assets", "angel")
    sounds_dir = os.path.join(assets, "sounds", "line")
    finals = {}                                               # id -> (speaker, path)
    for sp in common.SPEAKERS:
        d = os.path.join(a.finals, sp)
        if not os.path.isdir(d):
            continue
        for f in sorted(os.listdir(d)):
            if f.endswith(".wav") and not f.startswith("_"):
                lid = f[:-4]
                if lid in finals:
                    sys.exit(f"line id {lid} exists for both {finals[lid][0]} and {sp}")
                finals[lid] = (sp, os.path.join(d, f))
    if not finals:
        sys.exit(f"no final wavs under {a.finals}; run transform.py first")

    durations, events, encoded = {}, {}, 0
    for lid in sorted(finals, key=lambda s: tuple(int(p) for p in s.split("."))):
        sp, wav = finals[lid]
        spk, uid = sp.lower(), common.norm_id(lid)
        dur = duration(wav)
        durations[lid] = round(dur, 3)
        ogg = os.path.join(sounds_dir, spk, uid + ".ogg")
        if (only is None or sp in only) and (a.force or not os.path.exists(ogg) or os.path.getmtime(ogg) < os.path.getmtime(wav)):
            os.makedirs(os.path.dirname(ogg), exist_ok=True)
            subprocess.run([common.FFMPEG, "-v", "error", "-y", "-i", wav, "-ac", "1", "-ar", "48000",
                            "-c:a", "libvorbis", "-q:a", str(a.quality), ogg], check=True)
            encoded += 1
        if os.path.exists(ogg):
            entry = {"name": f"angel:line/{spk}/{uid}"}
            if dur > a.stream_over:
                entry["stream"] = True
            events[f"line.{spk}.{uid}"] = {"sounds": [entry]}

    if a.prune and os.path.isdir(sounds_dir):
        keep = {os.path.join(sounds_dir, sp.lower(), common.norm_id(i) + ".ogg") for i, (sp, _) in finals.items()}
        for root, _, files in os.walk(sounds_dir):
            for f in files:
                p = os.path.join(root, f)
                if f.endswith(".ogg") and p not in keep:
                    os.remove(p)
                    print("pruned", p)

    sj = os.path.join(assets, "sounds.json")
    old = {}
    if os.path.exists(sj):
        try:
            old = json.load(open(sj, encoding="utf-8"))
        except Exception:
            print("warning: existing sounds.json is not valid JSON; replacing it")
    merged = {k: v for k, v in old.items() if not k.startswith("line.")}
    merged.update(events)
    os.makedirs(assets, exist_ok=True)
    json.dump(merged, open(sj, "w", encoding="utf-8", newline="\n"), indent=1)
    os.makedirs(os.path.dirname(a.durations), exist_ok=True)
    json.dump(durations, open(a.durations, "w", encoding="utf-8", newline="\n"), indent=1)
    total = sum(durations.values())
    print(f"{encoded} encoded, {len(events)} line events in {sj}")
    print(f"{len(durations)} durations ({total:.0f}s of speech) in {a.durations}")


if __name__ == "__main__":
    main()
