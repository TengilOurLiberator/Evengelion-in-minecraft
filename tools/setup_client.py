"""Prepare D:\\angel-attack\\game as the game directory of the Angel Attack VR profile.

    python tools\\setup_client.py                        prepare game\\ (safe to run again; the Genesis game is only read)
    python tools\\setup_client.py --install-profile      also add the "Angel Attack VR" profile to the Minecraft launcher
    python tools\\setup_client.py --plain                the bare Fabric + Vivecraft set again (alias --no-shaders)
    python tools\\setup_client.py --fetch-only           only download / verify the files of tools\\client_mods.json
    python tools\\setup_client.py --reset-mod-config     write the default mod configs again (Iris, ...), also where they exist
    python tools\\setup_client.py --shaders quality|vr|off   the shader preset (tools\\client_presets.json); default quality
    python tools\\setup_client.py --distant-horizons    switch the Distant Horizons mod on (only useful with it on the server too; see README)

What it takes from the Genesis game folder (D:\\genesis-vr\\game, read only): the mods (the Fabric jars the VR profile
runs), config, openvr (the SteamVR manifest and input bindings), and options.txt as the starting point.
Not taken: saves, logs, crash reports, menu worlds, the Genesis resource pack, the Fabric cache (.fabric, rebuilt by the
game on first start), and the Genesis server list.

The visual and audio mods (tools\\client_mods.json)
  Every file of the manifest is a Modrinth project version (project slug, version id, file name, sha512, kind, purpose,
  enabled). The files live in downloads\\mods\\ (not in git). A file that is missing there is downloaded again from
  Modrinth by its version id (api.modrinth.com; the file's cdn.modrinth.com address comes from the API), and a file whose
  sha512 differs from the manifest (and from the API's) is refused and not installed. Then they are copied:
    kind mod           game\\mods\\            (enabled false: installed as <file>.disabled, which the loader ignores)
    kind shader        game\\shaderpacks\\
    kind resourcepack  game\\resourcepacks\\   (enabled false: present, but not switched on in options.txt)
  What was installed is remembered in game\\.client_mods_installed.json, so that --plain and a changed manifest remove
  exactly those files and nothing else.

What it writes into game\\:
  resourcepacks\\angel-resources   a copy of pack\\angel-resources, made again on every run
  options.txt                    resource packs bottom to top: vanilla, the enabled packs of the manifest (Faithful), the
                                 Angel resource pack on top; Genesis's video settings
  servers.dat                    one entry, "Angel Attack", at localhost:<server-port from server\\server.properties>
  mods                           Genesis's jars (a jar that Genesis no longer has is removed) plus the manifest's
  config, openvr                 copied from Genesis only where the file does not exist yet (local tweaks are kept)
  config\\iris.properties         the preset's shader pack, only if the file does not exist (--shaders or --reset-mod-config: always)
  shaderpacks\\<pack>.txt         the preset's options of that pack (tools\\client_presets.json), same rule
  config\\DistantHorizons.toml    only with --distant-horizons: the LOD radius (64 chunks) and the vanilla fog kept, same rule
  options.txt                    also the preset's game_options (render distance; 12 with --distant-horizons)
  Everything else (Sodium, Continuity, ETF, EMF, Sound Physics, Flashback, Mod Menu, Vivecraft) is left at the mods' defaults.

The launcher's profile list (launcher_profiles.json under %APPDATA%\\.minecraft) is changed only with --install-profile.
Without it the script prints the profile entry that it would add, so that it can be added after asking.
"""
import argparse, hashlib, json, os, shutil, struct, datetime, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "game")
GENESIS_GAME = r"D:\genesis-vr\game"
MC = os.path.join(os.environ.get("APPDATA", ""), ".minecraft")
PACK = "angel-resources"
PROFILE_NAME = "Angel Attack VR"
PROFILE_KEY = "angel-attack-vr"
SERVER_NAME = "Angel Attack"
GENESIS_PROFILE = "Genesis VR"
DEFAULT_VERSION = "fabric-loader-0.19.5-26.3"          # the Genesis VR profile's loader version, if it cannot be read
DEFAULT_JAVA_ARGS = "-Xmx6G -XX:+UseG1GC"

MANIFEST = os.path.join(ROOT, "tools", "client_mods.json")
DOWNLOADS = os.path.join(ROOT, "downloads", "mods")
INSTALLED_LIST = ".client_mods_installed.json"          # in game\: the manifest files that were installed
API = "https://api.modrinth.com/v2/"
UA = {"User-Agent": "angel-attack-setup/1.0 (github.com/TengilOurLiberator; setup_client.py)"}
KIND_DIR = {"mod": "mods", "shader": "shaderpacks", "resourcepack": "resourcepacks"}

# the shader pack Iris starts with (manifest slug), and its options. Everything else in the pack stays at its defaults.
PRESETS = os.path.join(ROOT, "tools", "client_presets.json")

# the video and gameplay settings the piece wants (Genesis's values; the same for the headset)
WANTED = {"onboardAccessibility": "false", "skipMultiplayerWarning": "true", "joinedFirstServer": "true",
          "tutorialStep": "none", "pauseOnLostFocus": "false", "soundCategory_voice": "1.0",
          # as far and as fine as the game allows: the piece is about seeing a whole world appear
          "renderDistance": "32", "simulationDistance": "16", "entityDistanceScaling": "5.0", "biomeBlendRadius": "7",
          "cloudRange": "128", "particles": "0", "graphicsPreset": "\"custom\"", "mipmapLevels": "4", "entityShadows": "true"}
GENESIS_PACK = "file/genesis-resources"


def need(path, what):
    if not os.path.exists(path):
        raise SystemExit(f"missing {what}: {path}")


# ---- the manifest: download, verify, install ---------------------------------------------------------------------------

def load_manifest():
    need(MANIFEST, "client mod manifest")
    return json.load(open(MANIFEST, encoding="utf-8"))


def sha512_of(path):
    h = hashlib.sha512()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def api_version(version_id):
    req = urllib.request.Request(API + "version/" + version_id, headers=UA)
    return json.load(urllib.request.urlopen(req, timeout=60))


def download(entry):
    """Download one manifest file by its version id into downloads\\mods\\. The hash the API gives and the manifest's hash
    must agree and the downloaded bytes must match; otherwise nothing is kept."""
    v = api_version(entry["version_id"])
    if v["project_id"] != entry["project_id"]:
        raise SystemExit(f"{entry['slug']}: version {entry['version_id']} belongs to another project ({v['project_id']})")
    files = [f for f in v["files"] if f["filename"] == entry["file"]]
    if not files:
        raise SystemExit(f"{entry['slug']}: version {entry['version_id']} has no file {entry['file']!r}")
    f = files[0]
    if f["hashes"]["sha512"].lower() != entry["sha512"].lower():
        raise SystemExit(f"{entry['slug']}: the API's sha512 differs from the manifest's; refusing")
    if not f["url"].startswith("https://cdn.modrinth.com/data/"):
        raise SystemExit(f"{entry['slug']}: unexpected download address {f['url']}; refusing")
    os.makedirs(DOWNLOADS, exist_ok=True)
    dst = os.path.join(DOWNLOADS, entry["file"])
    part = dst + ".part"
    print(f"  downloading {entry['file']} ({f['size'] / 1e6:.1f} MB) ...", flush=True)
    with urllib.request.urlopen(urllib.request.Request(f["url"], headers=UA), timeout=120) as r, open(part, "wb") as out:
        shutil.copyfileobj(r, out, 1 << 20)
    if sha512_of(part).lower() != entry["sha512"].lower():
        os.remove(part)
        raise SystemExit(f"{entry['slug']}: downloaded file does not match the sha512; removed, not installed")
    os.replace(part, dst)
    return dst


def fetch_all(manifest):
    """Make sure every manifest file is in downloads\\mods\\ with the right hash. Returns {file: path}."""
    paths = {}
    for e in manifest["files"]:
        path = os.path.join(DOWNLOADS, e["file"])
        if os.path.exists(path):
            if sha512_of(path).lower() != e["sha512"].lower():
                raise SystemExit(f"{e['file']}: sha512 differs from the manifest; delete it from downloads\\mods to fetch it again")
        else:
            path = download(e)
        paths[e["file"]] = path
    return paths


def read_installed(game):
    p = os.path.join(game, INSTALLED_LIST)
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def load_presets():
    need(PRESETS, "shader presets")
    return json.load(open(PRESETS, encoding="utf-8"))


def effective_enabled(manifest, preset, distant_horizons):
    """{slug: bool}: the manifest's 'enabled', minus the preset's mods_off, plus --distant-horizons."""
    off = set(preset.get("mods_off", [])) if preset else set()
    eff = {}
    for e in manifest["files"]:
        eff[e["slug"]] = bool(e["enabled"]) and e["slug"] not in off
        if distant_horizons and e["slug"] == "distanthorizons":
            eff[e["slug"]] = True
    return eff


def entry_target(game, e, eff):
    """Relative path in game\\ where a manifest file goes."""
    name = e["file"] + (".disabled" if e["kind"] == "mod" and not eff[e["slug"]] else "")
    return os.path.join(KIND_DIR[e["kind"]], name)


def install_manifest(game, manifest, plain, eff):
    """Copy the manifest's files into game\\ (or, with plain, remove what an earlier run installed)."""
    previous = read_installed(game)
    wanted = {} if plain else {entry_target(game, e, eff): e for e in manifest["files"]}
    paths = {} if plain else fetch_all(manifest)
    for rel in previous:                                    # what an earlier run installed and is no longer wanted
        if rel not in wanted:
            p = os.path.join(game, rel)
            if os.path.isfile(p):
                os.remove(p)
    for rel, e in wanted.items():
        if e["kind"] == "mod":                               # the enabled <-> disabled twin must not stay
            plain_rel = os.path.join("mods", e["file"])
            for twin in (plain_rel, plain_rel + ".disabled"):
                if twin != rel and os.path.isfile(os.path.join(game, twin)):
                    os.remove(os.path.join(game, twin))
        dst = os.path.join(game, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        src = paths[e["file"]]
        if not (os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src)):
            shutil.copy2(src, dst)
    with open(os.path.join(game, INSTALLED_LIST), "w", encoding="utf-8", newline="\n") as f:
        json.dump(sorted(wanted), f, indent=2)
    return wanted


# ---- the Genesis base ---------------------------------------------------------------------------------------------------

def server_port():
    """The port in server\\server.properties (25565 if it is not there)."""
    path = os.path.join(ROOT, "server", "server.properties")
    if os.path.exists(path):
        for line in open(path, encoding="utf-8"):
            if line.startswith("server-port="):
                return int(line.split("=", 1)[1].strip())
    return 25565


def copy_pack(game):
    src = os.path.join(ROOT, "pack", PACK)
    need(os.path.join(src, "pack.mcmeta"), "resource pack (pack.mcmeta)")
    dst = os.path.join(game, "resourcepacks", PACK)
    shutil.rmtree(dst, ignore_errors=True)
    shutil.copytree(src, dst)
    return dst


def copy_mods(genesis, game, keep):
    """Genesis's jars into game\\mods; a jar that Genesis no longer has goes, except the manifest's (keep: file names)."""
    src = os.path.join(genesis, "mods")
    need(src, "Genesis mods folder")
    dst = os.path.join(game, "mods")
    os.makedirs(dst, exist_ok=True)
    jars = sorted(f for f in os.listdir(src) if f.lower().endswith(".jar"))
    for f in os.listdir(dst):
        if f.lower().endswith(".jar") and f not in jars and f not in keep:
            os.remove(os.path.join(dst, f))
    for f in jars:
        shutil.copy2(os.path.join(src, f), os.path.join(dst, f))
    return jars


def copy_missing(genesis, game, name):
    """Copy Genesis's folder file by file, but only the files that game\\ does not have yet: local tweaks stay."""
    src = os.path.join(genesis, name)
    need(src, f"Genesis {name} folder")
    dst_root = os.path.join(game, name)
    added = 0
    for dirpath, _dirs, files in os.walk(src):
        rel = os.path.relpath(dirpath, src)
        os.makedirs(os.path.join(dst_root, rel), exist_ok=True)
        for f in files:
            d = os.path.join(dst_root, rel, f)
            if not os.path.exists(d):
                shutil.copy2(os.path.join(dirpath, f), d)
                added += 1
    return added


def pack_id(entry):
    return "file/" + entry["file"]


def write_options(genesis, game, manifest, plain, game_options=None):
    """Start from the game's own options (after the first run), else Genesis's, else the player's Minecraft options.
    Resource packs, bottom to top: vanilla, [other packs already there], the manifest's enabled packs, angel-resources."""
    base = None
    for cand in (os.path.join(game, "options.txt"), os.path.join(genesis, "options.txt"), os.path.join(MC, "options.txt")):
        if os.path.exists(cand):
            base = cand
            break
    lines = list(open(base, encoding="utf-8")) if base else []
    managed = {pack_id(e) for e in manifest["files"] if e["kind"] == "resourcepack"}
    switched_on = [] if plain else [pack_id(e) for e in manifest["files"] if e["kind"] == "resourcepack" and e["enabled"]]
    wanted = dict(WANTED)
    wanted.update(game_options or {})
    out, seen = [], set()
    for line in lines:
        key = line.split(":", 1)[0]
        if key == "resourcePacks":
            try:
                packs = json.loads(line.split(":", 1)[1])
            except (ValueError, IndexError):
                packs = ["vanilla"]
            packs = [p for p in packs if p not in managed and p not in (GENESIS_PACK, f"file/{PACK}")]
            if "vanilla" not in packs:
                packs.insert(0, "vanilla")
            packs += switched_on
            packs.append(f"file/{PACK}")
            line = "resourcePacks:" + json.dumps(packs, separators=(",", ":")) + "\n"
            seen.add(key)
        elif key == "incompatibleResourcePacks":
            line = "incompatibleResourcePacks:[]\n"
            seen.add(key)
        elif key in wanted:
            line = f"{key}:{wanted[key]}\n"
            seen.add(key)
        out.append(line)
    if "resourcePacks" not in seen:
        out.append("resourcePacks:" + json.dumps(["vanilla"] + switched_on + [f"file/{PACK}"], separators=(",", ":")) + "\n")
    out += [f"{k}:{v}\n" for k, v in wanted.items() if k not in seen]
    path = os.path.join(game, "options.txt")
    open(path, "w", encoding="utf-8").writelines(out)
    return path, base


# ---- mod configs (only what is certain; the rest stays at the mods' defaults) ------------------------------------------

def write_if(path, text, force):
    """Write a default config file, but not over an existing one (the player's or an earlier tweak) unless forced."""
    if os.path.exists(path) and not force:
        return False
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    return True


def mod_configs(game, manifest, eff, preset, shaders, force):
    """Iris starts with the preset's shader pack and options (shaders 'off': Iris is left with shaders switched off).
    Distant Horizons gets its config only when it is on. Returns what was written."""
    wrote = []
    by_slug = {e["slug"]: e for e in manifest["files"]}
    if eff.get("iris"):
        pack = by_slug[preset["shader"]]
        iris = {"colorSpace": "SRGB", "disableUpdateMessage": "true", "enableDebugOptions": "false",
                "enableShaders": "false" if shaders == "off" else "true", "maxShadowRenderDistance": "16",
                "shaderPack": pack["file"]}
        iris.update(preset.get("iris", {}))
        text = ("#This file stores configuration options for Iris, such as the currently active shaderpack\n"
                f"#written by tools/setup_client.py (preset {shaders})\n" + "".join(f"{k}={v}\n" for k, v in iris.items()))
        p = os.path.join(game, "config", "iris.properties")
        if write_if(p, text, force):
            wrote.append(p)
        opts = preset.get("options")
        if opts and shaders != "off":
            p = os.path.join(game, "shaderpacks", pack["file"] + ".txt")
            if write_if(p, "".join(f"{k}={v}\n" for k, v in opts.items()), force):
                wrote.append(p)
    if eff.get("distanthorizons"):
        # the key paths are certain (the mod's own language file and class nesting); the file is written only if absent, and
        # Distant Horizons fills in every other entry with its defaults. Its fog is switched off in favour of the game's own
        # fog: the Angel sets use the biome fog (the geofront's golden haze), which DH otherwise replaces.
        p = os.path.join(game, "config", "DistantHorizons.toml")
        text = ("# written by tools/setup_client.py; Distant Horizons adds every other setting at its default\n"
                "[client.advanced.graphics.quality]\n"
                f"\tlodChunkRenderDistanceRadius = {DH_LOD_RADIUS}\n"
                "[client.advanced.graphics.fog]\n"
                "\tenableDhFog = false\n"
                "\tenableVanillaFog = true\n")
        if write_if(p, text, force):
            wrote.append(p)
    return wrote


# Distant Horizons' LOD radius in chunks (only with --distant-horizons)
DH_LOD_RADIUS = 64


# ---- servers.dat, launcher profile --------------------------------------------------------------------------------------

def nbt_string(text):
    b = text.encode("utf-8")
    return struct.pack(">H", len(b)) + b


def write_servers(game, port):
    """servers.dat (uncompressed NBT): one entry, the local Angel Attack server."""
    entry = (b"\x08" + nbt_string("name") + nbt_string(SERVER_NAME)
             + b"\x08" + nbt_string("ip") + nbt_string(f"localhost:{port}") + b"\x00")
    nbt = b"\x0a" + nbt_string("") + b"\x09" + nbt_string("servers") + b"\x0a" + struct.pack(">i", 1) + entry + b"\x00"
    path = os.path.join(game, "servers.dat")
    with open(path, "wb") as f:
        f.write(nbt)
    return path


def profile_entry():
    """The launcher profile for the game folder. The version and JVM arguments are the Genesis VR profile's."""
    version, java_args = DEFAULT_VERSION, DEFAULT_JAVA_ARGS
    lp = os.path.join(MC, "launcher_profiles.json")
    if os.path.exists(lp):
        for p in json.load(open(lp, encoding="utf-8")).get("profiles", {}).values():
            if p.get("name") == GENESIS_PROFILE:
                version, java_args = p.get("lastVersionId", version), p.get("javaArgs", java_args)
    now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
    return {"created": now, "gameDir": GAME, "icon": "Grass", "javaArgs": java_args, "lastUsed": now,
            "lastVersionId": version, "name": PROFILE_NAME, "type": "custom"}


def install_profile(entry):
    lp = os.path.join(MC, "launcher_profiles.json")
    need(lp, "launcher profile list (open the Minecraft launcher once first)")
    data = json.load(open(lp, encoding="utf-8"))
    profiles = data.setdefault("profiles", {})
    key = PROFILE_KEY
    for k, p in profiles.items():
        if p.get("name") == PROFILE_NAME:
            key = k
            entry["created"] = p.get("created", entry["created"])
    backup = lp + ".before-angel-attack"
    if not os.path.exists(backup):
        shutil.copy2(lp, backup)
    profiles[key] = entry
    with open(lp, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    return lp, backup, key


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("game_dir", nargs="?", default=GAME, help="the game folder to prepare (default: game\\ in this project)")
    ap.add_argument("--genesis-game", default=GENESIS_GAME, help="the Genesis game folder to take mods and settings from")
    ap.add_argument("--install-profile", action="store_true",
                    help="add the 'Angel Attack VR' profile to the Minecraft launcher (close the launcher first)")
    ap.add_argument("--plain", "--no-shaders", dest="plain", action="store_true",
                    help="the bare Fabric + Vivecraft set: remove what tools\\client_mods.json installed, no extra packs")
    ap.add_argument("--fetch-only", action="store_true", help="only download and verify the manifest's files, change nothing else")
    ap.add_argument("--reset-mod-config", action="store_true", help="write the default mod configs again, also where they exist")
    ap.add_argument("--shaders", choices=["quality", "vr", "off"],
                    help="shader preset from tools\\client_presets.json (default: quality; 'off' keeps the mods but switches shaders off); "
                         "giving it rewrites iris.properties and the pack's options")
    ap.add_argument("--distant-horizons", action="store_true",
                    help="switch the Distant Horizons mod on (it needs the same mod on the server to add anything; see README)")
    args = ap.parse_args()
    game, genesis = args.game_dir, args.genesis_game
    manifest = load_manifest()
    if args.fetch_only:
        fetch_all(manifest)
        print("all manifest files are in", DOWNLOADS, "with the right sha512")
        return
    need(genesis, "Genesis game folder")
    os.makedirs(game, exist_ok=True)

    presets = load_presets()
    shaders = args.shaders or presets["default"]
    preset = presets["presets"]["quality" if shaders == "off" else shaders]
    if shaders == "off":
        preset = dict(preset, options={})
    eff = effective_enabled(manifest, None if args.plain else preset, args.distant_horizons)
    made = []
    made.append(copy_pack(game))
    wanted = install_manifest(game, manifest, args.plain, eff)     # first: nothing is changed if a download fails its hash
    keep = {os.path.basename(r) for r in wanted if r.startswith("mods")}
    jars = copy_mods(genesis, game, keep)
    for name in ("config", "openvr"):
        n = copy_missing(genesis, game, name)
        made.append(os.path.join(game, name) + f" ({n} files added from Genesis; existing files kept)")
    game_options = dict(preset.get("game_options", {}))
    if args.distant_horizons:                 # the LODs carry the distance: 12 chunks of real terrain (tested: same frame time as 24 without)
        game_options["renderDistance"] = "12"
    opts, opts_base = write_options(genesis, game, manifest, args.plain, None if args.plain else game_options)
    made.append(opts)
    made.append(write_servers(game, server_port()))
    cfg = [] if args.plain else mod_configs(game, manifest, eff, preset, shaders, args.reset_mod_config or bool(args.shaders))

    print("game folder:", game, "(plain: Fabric + Vivecraft only)" if args.plain else f"(shader preset: {shaders})")
    for p in made:
        print("  wrote", p)
    print("  Genesis mods:", ", ".join(jars))
    if wanted:
        print("  manifest files installed (%d):" % len(wanted))
        for rel in sorted(wanted):
            print("    ", rel)
    for p in cfg:
        print("  wrote default config", p)
    print("  options.txt started from:", opts_base or "nothing (defaults)")
    print("  servers.dat: one entry, %r at localhost:%d" % (SERVER_NAME, server_port()))

    entry = profile_entry()
    if args.install_profile:
        lp, backup, key = install_profile(entry)
        print(f"launcher profile written: {lp} (key {key}; the first version of the file is in {backup})")
    else:
        print("\nLauncher profile NOT changed. With --install-profile this entry would be added to")
        print(os.path.join(MC, "launcher_profiles.json"), "under the key", repr(PROFILE_KEY) + ":")
        print(json.dumps({PROFILE_KEY: entry}, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
