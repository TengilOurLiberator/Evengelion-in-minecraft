"""Build the Angel (the monster) and the boss fight into the Angel Attack datapack.

    python build_fight.py             write the functions, damage type and block tag; remove what an earlier build wrote
    python build_fight.py --check     build into a temporary folder and only run the checks
    python build_fight.py --out DIR   write the pack files under DIR (default D:\\angel-attack\\datapack\\angel)
    python build_fight.py --previews  also render the previews (tools\\fight\\preview\\)
    python build_fight.py --pace full|video   the preset (default video; or set ANGEL_PACE): see gen_fight.py FULL / VIDEO and README.md

Use the Python of the D:\\voice-assistant environment (numpy, pillow).

Writes under <pack>\\data\\angel\\: function\\angel\\ (the monster), function\\fight\\ (the fight, with say\\ stand-ins for the
story's lines), tags\\block\\fight\\beam_pass.json.  The list of files written is kept in
build_manifest.json next to this file, so the next build removes exactly those and nothing else.

The story engine's lines: function\\fight\\say\\7_NN calls angel:say/7_NN if data\\angel\\function\\say\\7_NN.mcfunction
exists when this runs, otherwise it prints the line with tellraw and pretends to talk for a while.  Rebuild after the story
engine has written its say functions.  Likewise angel:story/fight_done {result:"won"} is called only if
function\\story\\fight_done.mcfunction exists at build time.
"""
import argparse
import json
import os
import re
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TOOLS = os.path.dirname(HERE)
ROOT = os.path.dirname(TOOLS)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TOOLS, "world"))
import gen_angel  # noqa: E402
import gen_fight  # noqa: E402
import model  # noqa: E402

PACK = os.path.join(ROOT, "datapack", "angel")
MANIFEST = os.path.join(HERE, "build_manifest.json")


def say(m=""):
    print(m, flush=True)


def collect(pack):
    fdir = os.path.join(pack, "data", "angel", "function")
    ang, fgt = {}, {}
    gen_angel.gen(ang)
    story_hand = os.path.isfile(os.path.join(fdir, "story", "fight_done.mcfunction"))
    gen_fight.gen(fgt, fdir, story_hand)
    files = {}
    for p, lines in ang.items():
        files[f"data/angel/function/angel/{p}.mcfunction"] = "\n".join(lines) + "\n"
    for p, lines in fgt.items():
        files[f"data/angel/function/fight/{p}.mcfunction"] = "\n".join(lines) + "\n"
    files["data/angel/tags/block/fight/beam_pass.json"] = json.dumps(
        {"values": ["#minecraft:air", "minecraft:light", "#minecraft:replaceable"]}, indent=1)
    return files, ang, fgt, story_hand


def known_sounds():
    """(set of our sound events, set of vanilla ones or None).  Ours: pack\\angel-resources\\assets\\angel\\sounds.json.  Vanilla: the installed
    client's sounds.json, found through the asset index under %APPDATA%\\.minecraft\\assets (read only)."""
    ours = set(json.load(open(os.path.join(ROOT, "pack", "angel-resources", "assets", "angel", "sounds.json"), encoding="utf-8")))
    vanilla = None
    try:
        adir = os.path.join(os.environ["APPDATA"], ".minecraft", "assets")
        best = max((f for f in os.listdir(os.path.join(adir, "indexes")) if f.endswith(".json")), key=lambda f: int(f[:-5]) if f[:-5].isdigit() else -1)
        h = json.load(open(os.path.join(adir, "indexes", best), encoding="utf-8"))["objects"]["minecraft/sounds.json"]["hash"]
        vanilla = set(json.load(open(os.path.join(adir, "objects", h[:2], h), encoding="utf-8")))
    except Exception:
        pass
    return ours, vanilla


def check_sounds(allf):
    """Every playsound / stopsound id the generated functions use must exist.  Returns [(id, where)]."""
    ours, vanilla = known_sounds()
    bad = []
    for k, lines in allf.items():
        for ln in lines:
            for m in re.finditer(r"(?:playsound|stopsound @a \S+) ([a-z0-9_.:/]+)", ln):
                sid = m.group(1)
                ns, _, name = sid.rpartition(":")
                if (ns or "minecraft") == "angel":
                    ok = name in ours
                else:
                    ok = vanilla is None or name in vanilla
                if not ok:
                    bad.append((sid, k))
    return bad


def check(ang, fgt):
    import cmdcheck
    allf = {f"angel/{k}": v for k, v in ang.items()}
    allf.update({f"fight/{k}": v for k, v in fgt.items()})
    bad = cmdcheck.check_functions({k: v for k, v in allf.items()})
    for path, n, line, msg in bad[:40]:
        say(f"  COMMAND CHECK {path}:{n}: {msg}\n      {line[:200]}")
    # every function we call must exist (the story's say/ and story/ ones are guarded elsewhere)
    refs = set()
    pat = re.compile(r"function angel:(angel|fight)/([a-z0-9_/]+)")
    for k, lines in allf.items():
        for ln in lines:
            for m in pat.finditer(ln):
                refs.add((m.group(1), m.group(2), k))
    missing = []
    for ns, name, where in sorted(refs):
        if name.startswith("pp/") or name.startswith("p/") or name.startswith("s/"):
            pass
        have = (ns == "angel" and name in ang) or (ns == "fight" and name in fgt)
        if name.endswith("_") or name.endswith("/"):
            continue
        if not have:
            missing.append((f"angel:{ns}/{name}", where))
    for m in missing[:40]:
        say(f"  MISSING FUNCTION {m[0]} (called from {m[1]})")
    snd = check_sounds(allf)
    for sid, where in snd[:40]:
        say(f"  UNKNOWN SOUND {sid} (in {where})")
    return len(bad), len(missing) + len(snd)


def write(pack, files, out_manifest=True):
    old = []
    if os.path.isfile(MANIFEST):
        old = json.load(open(MANIFEST, encoding="utf-8")).get("files", [])
    for rel in old:
        p = os.path.join(pack, rel.replace("/", os.sep))
        if os.path.isfile(p):
            os.remove(p)
    # prune empty folders that were ours
    for rel in sorted(old, key=len, reverse=True):
        d = os.path.dirname(os.path.join(pack, rel.replace("/", os.sep)))
        while d.startswith(pack) and d != pack and os.path.isdir(d) and not os.listdir(d):
            os.rmdir(d)
            d = os.path.dirname(d)
    total = 0
    for rel, text in files.items():
        p = os.path.join(pack, rel.replace("/", os.sep))
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        total += len(text)
    if out_manifest:
        with open(MANIFEST, "w", encoding="utf-8", newline="\n") as f:
            json.dump({"files": sorted(files)}, f, indent=1)
    return total


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out")
    ap.add_argument("--previews", action="store_true")
    ap.add_argument("--pace", choices=sorted(gen_fight.PRESETS),
                    help="the fight's preset: video (default; env ANGEL_PACE=full|video when this is not given) = the paced fight with the visible rules; full = the earlier numbers and behaviour")
    a = ap.parse_args()
    if a.pace:
        gen_fight.set_pace(a.pace)
    model.build()
    say(f"pace: {gen_fight.PACE}")
    say(f"model: {len(model.PARTS)} parts, heights {gen_angel.HEIGHTS}, poses {len(gen_angel.POSE_FILES)}")
    pack = os.path.abspath(a.out) if a.out else PACK
    files, ang, fgt, story_hand = collect(pack)
    nb, nm = check(ang, fgt)
    say(f"checked {sum(len(v) for v in ang.values()) + sum(len(v) for v in fgt.values())} lines: {nb} command problems, {nm} missing functions or unknown sounds")
    if a.check:
        say(f"would write {len(files)} files")
        return 1 if (nb or nm) else 0
    total = write(pack, files, out_manifest=not a.out)
    say(f"wrote {len(files)} files, {total / 1e6:.2f} MB, into {pack}")
    say(f"story say functions found: {sum(os.path.isfile(os.path.join(pack, 'data', 'angel', 'function', 'say', f'7_{i:02d}.mcfunction')) for i in range(1, 21))} of 20; story/fight_done: {story_hand}")
    if a.previews:
        import preview
        os.makedirs(preview.OUT, exist_ok=True)
        for n in ("idle_a", "charge", "charge_2", "charge_3", "thrust", "wrap_close", "regen_0", "regen_2", "die_1", "die_2", "die_3", "walk_l"):
            preview.sheet(n, model.poses()[n])
        say("previews written")
    return 1 if (nb or nm) else 0


if __name__ == "__main__":
    sys.exit(main())

