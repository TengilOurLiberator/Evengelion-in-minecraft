"""Fabric mode of the visual test: a SEPARATE test game directory (default work\\testgame_mods) that is a copy of the mods, config,
shaderpacks and resourcepacks of D:\\angel-attack\\game, plus a variant: which shader pack (if any) Iris starts with and its options.
The real game folder is only read.  Vivecraft stays installed and stays in non-VR mode (its config says vrEnabled false).

A variant is a dict:
    fabric        False: the plain 26.3 client (the baseline); True: the Fabric Loader profile with the mods
    shader        shader pack file name in shaderpacks\\ (None: shaders off)
    options       {OPTION: value} written to shaderpacks\\<file>.txt (the pack's own option names)
    packs         resource packs, bottom to top, between "vanilla" and the project's pack
    remove_mods   file name prefixes of mods left out of this variant
    iris          extra iris.properties entries
    dh_radius     DistantHorizons lodChunkRenderDistanceRadius (None: leave the config as copied)
"""
import json
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
REAL_GAME = os.path.join(ROOT, "game")
FAITHFUL = "file/Faithful 32x - 26.3.zip"

REIMAGINED = "ComplementaryReimagined_r5.9.3.zip"
UNBOUND = "ComplementaryUnbound_r5.9.3.zip"
BSL = "BSL_v10.1.8.zip"
MAKEUP = "MakeUp-UltraFast-9.5g.zip"

VARIANTS = {
    "a_vanilla": dict(fabric=False),
    "b_mods": dict(fabric=True, shader=None, packs=[FAITHFUL]),
    "c_reimagined": dict(fabric=True, shader=REIMAGINED, options={"COLORED_LIGHTING": 192}, packs=[FAITHFUL]),
    "d_reimagined_nocolor": dict(fabric=True, shader=REIMAGINED, options={"COLORED_LIGHTING": 0}, packs=[FAITHFUL]),
    "e_bsl": dict(fabric=True, shader=BSL, options={}, packs=[FAITHFUL]),
    "f_makeup": dict(fabric=True, shader=MAKEUP, options={}, packs=[FAITHFUL]),
    # cost / cause experiments (mods on, shaders off unless said)
    "x_no_dh": dict(fabric=True, shader=None, packs=[FAITHFUL], remove_mods=["DistantHorizons"]),
    "x_sodium_only": dict(fabric=True, shader=None, packs=[FAITHFUL], remove_mods=[
        "DistantHorizons", "Flashback", "entity_", "sound-physics", "modmenu", "placeholder", "continuity", "iris"]),
    "x_vanilla_faithful": dict(fabric=True, shader=None, packs=[FAITHFUL], remove_mods=[
        "DistantHorizons", "Flashback", "entity_", "sound-physics", "modmenu", "placeholder", "continuity", "iris", "sodium"]),
}


def _sync_dir(src, dst, delete_extra=True):
    """Copy files whose size differs (big jars are not copied again); optionally remove what src does not have."""
    os.makedirs(dst, exist_ok=True)
    names = set()
    for name in os.listdir(src):
        s, d = os.path.join(src, name), os.path.join(dst, name)
        names.add(name)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        elif not (os.path.exists(d) and os.path.getsize(d) == os.path.getsize(s)):
            shutil.copy2(s, d)
    if delete_extra:
        for name in os.listdir(dst):
            if name not in names:
                p = os.path.join(dst, name)
                shutil.rmtree(p) if os.path.isdir(p) else os.remove(p)


def prepare(game, variant, src_game=REAL_GAME):
    """Fill the test game directory for one variant. Returns the extra options.txt entries (resourcePacks, maxFps, ...)."""
    if os.path.abspath(game).lower() == os.path.abspath(src_game).lower():
        raise SystemExit("refusing to use the real game folder as the test game directory")
    os.makedirs(game, exist_ok=True)
    if not variant.get("fabric"):
        return {"resourcePacks": '["vanilla","file/angel-resources"]'}
    # mods
    mods = os.path.join(game, "mods")
    _sync_dir(os.path.join(src_game, "mods"), mods)
    for f in os.listdir(mods):
        if any(f.startswith(p) for p in variant.get("remove_mods", [])):
            os.remove(os.path.join(mods, f))
    # config: a fresh copy every run, then the variant's files
    shutil.rmtree(os.path.join(game, "config"), ignore_errors=True)
    shutil.copytree(os.path.join(src_game, "config"), os.path.join(game, "config"))
    cfg = os.path.join(game, "config")
    vc = os.path.join(cfg, "vivecraft-client-config.json")
    if os.path.exists(vc):                      # non-VR, certainly
        t = open(vc, encoding="utf-8").read().replace('"vrEnabled": "true"', '"vrEnabled": "false"')
        open(vc, "w", encoding="utf-8", newline="\n").write(t)
    # shader packs
    sp = os.path.join(game, "shaderpacks")
    _sync_dir(os.path.join(src_game, "shaderpacks"), sp)
    for f in os.listdir(sp):
        if f.endswith(".txt"):
            os.remove(os.path.join(sp, f))
    shader = variant.get("shader")
    iris = {"colorSpace": "SRGB", "disableUpdateMessage": "true", "enableDebugOptions": "false",
            "enableShaders": "true" if shader else "false", "maxShadowRenderDistance": "16",
            "shaderPack": shader or ""}
    iris.update(variant.get("iris", {}))
    open(os.path.join(cfg, "iris.properties"), "w", encoding="utf-8", newline="\n").write(
        "".join(f"{k}={v}\n" for k, v in iris.items()))
    if shader and variant.get("options"):
        open(os.path.join(sp, shader + ".txt"), "w", encoding="utf-8", newline="\n").write(
            "".join(f"{k}={v}\n" for k, v in variant["options"].items()))
    if variant.get("dh_radius") is not None:
        open(os.path.join(cfg, "DistantHorizons.toml"), "w", encoding="utf-8", newline="\n").write(
            "[client.advanced.graphics.quality]\n\tlodChunkRenderDistanceRadius = %d\n" % variant["dh_radius"])
    # resource packs: the zips (copied once), the options entry
    rp = os.path.join(game, "resourcepacks")
    os.makedirs(rp, exist_ok=True)
    for f in os.listdir(os.path.join(src_game, "resourcepacks")):
        s = os.path.join(src_game, "resourcepacks", f)
        if os.path.isfile(s):
            d = os.path.join(rp, f)
            if not (os.path.exists(d) and os.path.getsize(d) == os.path.getsize(s)):
                shutil.copy2(s, d)
    packs = ["vanilla"] + list(variant.get("packs", [])) + ["file/angel-resources"]
    return {"resourcePacks": json.dumps(packs, separators=(",", ":"))}
