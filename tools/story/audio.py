"""Sound for the scenes: looped ambience beds, music cues and one-shot effects, with the rules that a bed or a cue never overlaps another
of its kind and that everything stops cleanly when its cue ends or the story halts.

    s.bed("hq")          start the ambience bed angel:amb.hq (the beds in play are stopped first); s.bed(None) stops the bed
    s.music("father")    start the music cue angel:music.father (the music in play is stopped first); s.music(None) stops it
    s.sfx("sfx.door_boom", at=(x, y, z), vol=2.0, pitch=0.8)   a one-shot effect (at=None: at the player, not positional)
    s.loop("klaxon")     an alarm layer: angel:sfx.klaxon every 11 s until s.loop(None) (it does not stop the beds or the music)

A bed is a sound that restarts itself: the function `angel:story/snd/bed_<key>/loop` plays it and schedules itself again after the length
of the recording (read from the .ogg named in sounds.json when it exists; `DEFAULT_SECONDS` when it does not yet).  A missing sound event is
simply silent in the game, so scenes can name events that are still being made; REBUILD once they exist so the loop lengths are right.
`angel:story/snd/stop_all` (called by halt) stops every bed and every cue: it clears their timers and sends `stopsound` for each event.
"""
import json
import os
import struct

from core import NS, P, PA, ROOT, SOUNDS, T, fn, num

PACK_SOUNDS = os.path.join(ROOT, "pack", "angel-resources", "assets", "angel", "sounds")
DEFAULT_SECONDS = 60.0
# volume of each bed / cue unless a scene says otherwise
BED_VOL = {"hq": 0.55, "lake": 0.6, "cage": 0.55}
MUSIC_VOL = {"cage": 0.7, "father": 0.7, "decision": 0.75, "resolve": 0.8}
MUSIC_LOOP = {"decision": True}                  # music that restarts itself until it is stopped (the others play once)
LOOP_PERIOD = {"klaxon": 11.0}                   # a "loop" is an effect layer (an alarm) that repeats every so many seconds until stopped
LOOP_VOL = {"klaxon": 0.4}


def ogg_seconds(path):
    """Length of an Ogg Vorbis / Opus file in seconds (granule position of the last page over the sample rate), or None."""
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    if len(data) < 64 or data[:4] != b"OggS":
        return None
    rate = None
    i = data.find(b"\x01vorbis")
    if i >= 0:
        rate = struct.unpack_from("<I", data, i + 12)[0]
    elif data.find(b"OpusHead") >= 0:
        rate = 48000
    j = data.rfind(b"OggS")
    if rate is None or j < 0:
        return None
    gran = struct.unpack_from("<q", data, j + 6)[0]
    return gran / float(rate) if gran > 0 else None


def event_file_seconds(event):
    """Length of the recording behind sound event `event` ("angel:amb.hq") from sounds.json, or None."""
    key = event.split(":", 1)[-1]
    try:
        with open(SOUNDS, encoding="utf-8") as f:
            sj = json.load(f)
    except (OSError, ValueError):
        return None
    ent = sj.get(key)
    if not ent:
        return None
    for snd in ent.get("sounds", []):
        name = snd["name"] if isinstance(snd, dict) else snd
        rel = name.split(":", 1)[-1]
        sec = ogg_seconds(os.path.join(PACK_SOUNDS, *rel.split("/")) + ".ogg")
        if sec:
            return sec
    return None


class Audio:
    def __init__(self, ctx):
        self.ctx = ctx
        self.cues = {}                 # (kind, key) -> dict

    # ------------------------------------------------------------------ registry
    def _cue(self, kind, key):
        k = (kind, key)
        if k not in self.cues:
            if kind == "bed":
                event, source, vol, loop = f"{NS}:amb.{key}", "ambient", BED_VOL.get(key, 0.6), True
            elif kind == "loop":
                event, source, vol, loop = f"{NS}:sfx.{key}", "master", LOOP_VOL.get(key, 0.5), True
            else:
                event, source, vol, loop = f"{NS}:music.{key}", "music", MUSIC_VOL.get(key, 0.7), MUSIC_LOOP.get(key, False)
            secs = LOOP_PERIOD.get(key) if kind == "loop" else event_file_seconds(event)
            self.cues[k] = dict(kind=kind, key=key, event=event, source=source, vol=vol, loop=loop, secs=secs or DEFAULT_SECONDS, known=bool(secs))
        return self.cues[k]

    def start(self, kind, key):
        """Commands that start bed/music `key` (stopping whatever of that kind is in play)."""
        self._cue(kind, key)
        return [fn(f"story/snd/{kind}_{key}/start")]

    def stop(self, kind):
        return [fn(f"story/snd/stop_{kind}")]

    # ------------------------------------------------------------------ the functions
    def write(self):
        ex = self.ctx.extra_functions
        stops = {"bed": [], "music": [], "loop": []}
        for (kind, key), c in sorted(self.cues.items()):
            base = f"story/snd/{kind}_{key}"
            play = f"execute at {P()} run playsound {c['event']} {c['source']} {PA()} ~ ~ ~ {num(c['vol'])} 1.0 1.0"
            if c["loop"]:
                ex[f"{base}/loop"] = [f"# {c['event']}: {c['secs']:.1f}s{'' if c['known'] else ' (recording not found: default length)'}",
                                      play, f"schedule function {NS}:{base}/loop {max(1, T(c['secs']))}t"]
                ex[f"{base}/start"] = [fn(f"story/snd/stop_{kind}"), fn(f"{base}/loop")]
            else:
                ex[f"{base}/start"] = [fn(f"story/snd/stop_{kind}"), play]
            stops[kind] += ([f"schedule clear {NS}:{base}/loop"] if c["loop"] else []) + [f"stopsound {PA()} {c['source']} {c['event']}"]
        for kind in ("bed", "music", "loop"):
            ex[f"story/snd/stop_{kind}"] = stops[kind] or ["# nothing registered"]
        ex["story/snd/stop_all"] = [fn("story/snd/stop_bed"), fn("story/snd/stop_music"), fn("story/snd/stop_loop")]

    def names(self):
        return sorted(f"{k}:{key}" for (k, key) in self.cues)


def sfx(event, at=None, vol=1.0, pitch=1.0, minvol=0.0, source="master"):
    """One-shot effect.  `event`: "sfx.door_boom" or "angel:sfx.door_boom" (or a vanilla "minecraft:..." id).  at=(x, y, z): from that place,
    heard from its direction by the player (volume 16 blocks per 1.0, minvol is the volume the player hears beyond that); None: at the player."""
    if ":" not in event:
        event = f"{NS}:{event}"
    if at is None:
        return f"execute at {P()} run playsound {event} {source} {PA()} ~ ~ ~ {num(vol)} {num(pitch)} 1.0"
    x, y, z = at
    return f"playsound {event} {source} {PA()} {num(x)} {num(y)} {num(z)} {num(vol)} {num(pitch)} {num(minvol)}"
