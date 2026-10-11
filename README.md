# Angel Attack

The first episode's story as a Minecraft VR experience: you are the boy; four characters you can talk to;
then you pilot the giant and fight.

## Play

1. `.\start.ps1` (add `-NewWorld` to begin again). This opens the local server.
2. Minecraft launcher, profile **Angel Attack**, Play. For the headset, start SteamVR first and switch Vivecraft to VR.
3. Multiplayer, **Angel Attack**.

The server listens on port 25566, RCON on 25576 (Genesis uses 25565 and 25575, so both can run at once).

## What is here

| Path | What it is |
|---|---|
| `start.ps1` | Starts the server, then the character bridge (the bridge start is a TODO for now) |
| `tools/server.ps1`, `tools/rcon.py` | Run the server and talk to it over RCON |
| `server/` | Fabric server runtime, mods and config, copied from Genesis. The world, logs and player data are made here and are not in git |
| `datapack/angel` | The datapack (empty for now) |
| `pack/angel-resources` | The resource pack for the narration and sounds (empty for now) |
| `tools/voices` | in progress |
| `characters_bridge/bridge.py` | in progress: the character bridge |
| `tools/world` | in progress |
| `script.md` | in progress |
| `characters/` | in progress |
