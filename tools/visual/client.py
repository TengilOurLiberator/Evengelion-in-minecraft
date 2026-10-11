"""The silent desktop test client: own game folder, offline name, resource pack on, video settings for pictures."""
import json
import os
import shutil
import subprocess

from . import winutil

MC = os.path.join(os.environ["APPDATA"], ".minecraft")                 # read-only use of the installed game
JAVA = os.path.join(os.environ["LOCALAPPDATA"], r"Packages\Microsoft.4297127D64EC6_8wekyb3d8bbwe\LocalCache\Local\runtime"
                    r"\java-runtime-epsilon\windows-x64\java-runtime-epsilon\bin\java.exe")
VERSION = "26.3"
NAME = "Tester"
PACK = "angel-resources"


def options(fov=90, render=24, gamma=0.5, extra=None):
    """options.txt text. Everything not listed gets the game's default. master volume 0: the test is silent."""
    o = {
        "version": "5023",
        "fov": f"{(fov - 70) / 40.0:.4f}",           # stored as (fov - 70) / 40 ; this is the VERTICAL field of view
        "fovEffectScale": "0.0", "screenEffectScale": "0.0", "darknessEffectScale": "0.0",
        "gamma": f"{gamma}",
        "renderDistance": str(render), "simulationDistance": "12", "entityDistanceScaling": "5.0",
        "renderClouds": '"off"', "cloudRange": "32", "vignette": "false", "bobView": "false", "damageTiltStrength": "0.0",
        "enableVsync": "false", "maxFps": "120", "inactivityFpsLimit": '"minimized"', "pauseOnLostFocus": "false",
        "biomeBlendRadius": "5", "ao": "true", "mipmapLevels": "4", "entityShadows": "true", "particles": "0",
        "guiScale": "2", "showSubtitles": "false", "narrator": "0", "chatVisibility": "2",
        "soundCategory_master": "0.0", "soundCategory_music": "0.0", "soundCategory_record": "0.0",
        "soundCategory_weather": "0.0", "soundCategory_block": "0.0", "soundCategory_hostile": "0.0",
        "soundCategory_neutral": "0.0", "soundCategory_player": "0.0", "soundCategory_ambient": "0.0",
        "soundCategory_voice": "0.0",
        "onboardAccessibility": "false", "skipMultiplayerWarning": "true", "joinedFirstServer": "true",
        "tutorialStep": "none", "lang": "en_us", "autoJump": "false",
        "resourcePacks": f'["vanilla","file/{PACK}"]', "incompatibleResourcePacks": "[]",
        "fullscreen": "false", "overrideWidth": "0", "overrideHeight": "0",
    }
    o.update(extra or {})
    return "".join(f"{k}:{v}\n" for k, v in o.items())


def prepare(game, pack_src, fov, render, gamma, extra=None):
    """Make the game folder: options, the resource pack (a copy, so the pack on disk is never locked), empty natives."""
    os.makedirs(game, exist_ok=True)
    os.makedirs(os.path.join(game, "natives"), exist_ok=True)
    rp = os.path.join(game, "resourcepacks")
    os.makedirs(rp, exist_ok=True)
    dst = os.path.join(rp, PACK)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(pack_src, dst)
    with open(os.path.join(game, "options.txt"), "w", encoding="utf-8", newline="\n") as f:
        f.write(options(fov, render, gamma, extra))
    for d in ("saves", "logs", "screenshots"):                     # fresh logs; leftovers never confuse us
        shutil.rmtree(os.path.join(game, d), ignore_errors=True)


def command(game, port, width, height, xmx="6G"):
    v = json.load(open(os.path.join(MC, "versions", VERSION, VERSION + ".json")))
    ok = lambda lib: all(r.get("os", {}).get("name") in (None, "windows") and "arch" not in r.get("os", {})
                         for r in lib.get("rules", [{}]) if r.get("action") == "allow")
    cp = [os.path.join(MC, "libraries", *lib["downloads"]["artifact"]["path"].split("/"))
          for lib in v["libraries"] if ok(lib) and "artifact" in lib.get("downloads", {})]
    cp.append(os.path.join(MC, "versions", VERSION, VERSION + ".jar"))
    natives = os.path.join(game, "natives")
    jvm = []
    for a in v["arguments"]["jvm"]:
        if isinstance(a, str):
            jvm.append(a)
        elif any(r.get("os", {}).get("name") == "windows" for r in a["rules"]):
            jvm += a["value"] if isinstance(a["value"], list) else [a["value"]]
    sub = {"${natives_directory}": natives, "${launcher_name}": "angel-visual-test", "${launcher_version}": "1",
           "${classpath}": os.pathsep.join(cp)}
    for k, val in sub.items():
        jvm = [a.replace(k, val) for a in jvm]
    return [JAVA, f"-Xmx{xmx}"] + jvm + [
        v["mainClass"], "--username", NAME, "--version", VERSION, "--gameDir", game,
        "--assetsDir", os.path.join(MC, "assets"), "--assetIndex", v["assetIndex"]["id"],
        "--accessToken", "0", "--userType", "legacy", "--width", str(width), "--height", str(height),
        "--quickPlayMultiplayer", f"localhost:{port}"]


def launch(game, port, width, height):
    log = open(os.path.join(game, "client.log"), "w")
    proc = subprocess.Popen(command(game, port, width, height), cwd=game, stdout=log, stderr=subprocess.STDOUT,
                            creationflags=0x08000000)               # CREATE_NO_WINDOW: no console window
    winutil.adopt(proc)
    return proc
