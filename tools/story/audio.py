"""Sound for the scenes: looped ambience beds, music cues and one-shot effects, with the rules that a bed or a cue never overlaps another
of its kind and that everything stops cleanly when its cue ends or the story halts.

    s.bed("hq")          start the ambience bed angel:amb.hq (the beds in play are stopped first); s.bed(None) stops the bed
    s.bed("cicadas+town_empty")    two beds layered as one (they start and stop together)
    s.bed("tunnel", fade=2.5)      the bed comes in over 2.5 s (a stepped ramp: see below); out="tunnel" ramps that bed down instead of cutting
    s.music("father")    start the music cue angel:music.father (the music in play is stopped first); s.music(None) stops it
    s.sfx("sfx.door_boom", at=(x, y, z), vol=2.0, pitch=0.8)   a one-shot effect (at=None: at the player, not positional)
    s.loop("klaxon")     an alarm layer: angel:sfx.klaxon every 11 s until s.loop(None) (it does not stop the beds or the music)
    s.loop("siren")      the city siren: its own 20 s, restarted every 20 s; s.loop("siren", at=(x, y, z), vol=2.0, name="siren_far") plays it from a
                         place in the world instead, so that it fades with distance as the car drives away
    s.silence()          stops every bed, cue and layer, then everything else that is still sounding (the mine's silence)

A bed is a sound that restarts itself: the function `angel:story/snd/bed_<key>/loop` plays it and schedules itself again after the length
of the recording (read from the .ogg named in sounds.json when it exists; `DEFAULT_SECONDS` when it does not yet).  A missing sound event is
simply silent in the game, so scenes can name events that are still being made; REBUILD once they exist so the loop lengths are right.
`angel:story/snd/stop_all` (called by halt) stops every bed and every cue: it clears their timers and sends `stopsound` for each event.

Fades.  Minecraft cannot change the volume of a sound that is already playing, so a bed that comes in (or goes) slowly is a staircase of
restarts: every step stops the quieter copy and starts the file again a notch louder, the last step being the ordinary loop.  That is fine
for noise beds, never for music (a music cue is never faded, only started or stopped).
"""
import json
import os
import struct

from core import NS, P, PA, ROOT, SOUNDS, T, fn, num

PACK_SOUNDS = os.path.join(ROOT, "pack", "angel-resources", "assets", "angel", "sounds")
DEFAULT_SECONDS = 60.0
# volume of each bed / cue unless a scene says otherwise
BED_VOL = {"hq": 0.55, "lake": 0.6, "cage": 0.55, "cicadas": 0.7, "town_empty": 0.7, "car_interior": 0.7, "tunnel": 0.7, "geofront": 0.7}
MUSIC_VOL = {"cage": 0.7, "father": 0.7, "decision": 0.75, "resolve": 0.8, "dread": 0.75, "road": 0.7, "descent": 0.85, "fight": 0.75,
             "fight_final": 0.8, "defeat": 0.9}
# Music that restarts itself until it is stopped: exactly the files that tools/sound/manifest.json flags `loop` (checked by sim.check_music).
# A file that is NOT a loop (descent, defeat, resolve, victory, and the long decision and launch files) plays once.
MUSIC_LOOP = {"cage": True, "father": True, "dread": True, "road": True, "fight": True, "fight_final": True}
# A long file followed by its loop file: the loop starts when the long file ends and repeats by its own length (the library table says so:
# the last 13.85 s of music.decision are music.decision_loop; music.launch is 20 s of build and then the drive cycle twice).
MUSIC_CHAIN = {"decision": "decision_loop", "launch": "launch_loop"}
LOOP_PERIOD = {"klaxon": 11.0}                   # a "loop" is an effect layer (an alarm) that repeats every so many seconds until stopped (else: its own length)
LOOP_VOL = {"klaxon": 0.4, "siren": 0.6}
RAMP_STEP = 0.8                                  # seconds per step of a fade


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
        self.mixes = {}                # composite bed name -> [part keys]
        self.ramps = []                # (path, lines) of the fade functions
        self.ramp_paths = {"bed": [], "music": [], "loop": []}

    # ------------------------------------------------------------------ registry
    def _cue(self, kind, key, event_key=None, at=None, vol=None):
        k = (kind, key)
        if k not in self.cues:
            ek = event_key or key
            if kind == "bed":
                event, source, v, loop = f"{NS}:amb.{ek}", "ambient", BED_VOL.get(key, 0.6), True
            elif kind == "loop":
                event, source, v, loop = f"{NS}:sfx.{ek}", "master", LOOP_VOL.get(ek, 0.5), True
            else:
                event, source, v, loop = f"{NS}:music.{ek}", "music", MUSIC_VOL.get(key, 0.7), MUSIC_LOOP.get(key, False)
            if vol is not None:
                v = vol
            secs = (LOOP_PERIOD.get(ek) or event_file_seconds(event)) if kind == "loop" else event_file_seconds(event)
            chain = MUSIC_CHAIN.get(ek) if kind == "music" else None
            self.cues[k] = dict(kind=kind, key=key, event=event, source=source, vol=v, loop=loop, secs=secs or DEFAULT_SECONDS, known=bool(secs), at=at,
                                chain=(f"{NS}:music.{chain}", event_file_seconds(f"{NS}:music.{chain}") or DEFAULT_SECONDS) if chain else None)
        return self.cues[k]

    def _mix(self, key):
        """A bed named "a+b" is the layers a and b started and stopped together; returns (function-name stem, [cue dicts])."""
        parts = key.split("+")
        for p in parts:
            self._cue("bed", p)
        stem = parts[0] if len(parts) == 1 else "mix_" + "_".join(parts)
        if len(parts) > 1:
            self.mixes[stem] = parts
        return stem, [self.cues[("bed", p)] for p in parts]

    def start(self, kind, key, fade=0.0, out=None, out_fade=1.0, at=None, vol=None, name=None):
        """Commands that start bed/music/loop `key` (stopping whatever of that kind is in play).
        fade: seconds the bed takes to come in (beds only); out: key of the bed that is in play and should be ramped down over out_fade s
        instead of being cut (beds only)."""
        if kind == "bed":
            stem, parts = self._mix(key)
            if fade <= 0 and out is None:
                return [fn(f"story/snd/bed_{stem}/start")]
            return [fn(self._bed_ramp(stem, parts, fade, out, out_fade))]
        cue = self._cue(kind, name or key, event_key=key if name else None, at=at, vol=vol)
        return [fn(f"story/snd/{kind}_{cue['key']}/start")]

    def stop(self, kind):
        return [fn(f"story/snd/stop_{kind}")]

    def fade_out(self, key, seconds):
        """Commands that ramp the bed `key` (the one in play) down to nothing over `seconds` and stop it; every other bed is stopped at once."""
        return [fn(self._bed_ramp(None, [], 0.0, key, seconds))]

    # ------------------------------------------------------------------ ramps
    def _play(self, p, f=1.0):
        return f"execute at {P()} run playsound {p['event']} {p['source']} {PA()} ~ ~ ~ {num(p['vol'] * f)} 1.0 1.0"

    def _bed_ramp(self, stem, parts, fade, out, out_fade):
        """The function that brings bed `stem` in over `fade` s (and ramps bed `out` down over `out_fade` s at the same time)."""
        tag = f"in{int(round(fade * 10))}" + (f"_out_{out.replace('+', '_')}{int(round(out_fade * 10))}" if out else "")
        base = f"story/snd/bed_{stem or 'none'}/ramp_{tag}"
        if (base + "/start") in {p for p, _ in self.ramps}:
            return base + "/start"
        n_in = max(2, int(round(fade / RAMP_STEP))) if fade > 0 else 0
        n_out = max(2, int(round(out_fade / RAMP_STEP))) if out else 0
        n = max(n_in, n_out, 1)
        total = max(fade if fade > 0 else 0.0, out_fade if out else 0.0)
        dt = max(1, T(total / n))
        out_parts = []
        if out:
            _, out_parts = self._mix(out)
        steps = []
        for k in range(n):
            lines = []
            f_in = min(1.0, (k + 1) / float(n_in)) if n_in else 1.0
            f_out = max(0.0, 1.0 - (k + 1) / float(n_out)) if n_out else 0.0
            last = k == n - 1
            for p in out_parts:
                lines.append(f"stopsound {PA()} {p['source']} {p['event']}")
                if f_out > 0.001:
                    lines.append(self._play(p, f_out))
            for p in parts:
                if not n_in:                       # no fade in: the incoming bed starts at full volume with the first step
                    if k == 0:
                        lines.append(fn(f"story/snd/bed_{p['key']}/loop"))
                    continue
                lines.append(f"stopsound {PA()} {p['source']} {p['event']}")
                if last:
                    lines.append(fn(f"story/snd/bed_{p['key']}/loop"))
                else:
                    lines.append(self._play(p, f_in))
            if not last:
                lines.append(f"schedule function {NS}:{base}/s{k + 1} {dt}t")
            steps.append(lines)
        # first step runs at once (from `start`), the others are scheduled
        start = []
        if not out:
            start.append(fn("story/snd/stop_bed"))
        else:
            # every bed that is not the one being ramped down is stopped; the outgoing bed's own repeat is cancelled
            for (kind, key), c in sorted(self.cues.items()):
                if kind == "bed" and key not in [p["key"] for p in out_parts] + [p["key"] for p in parts]:
                    start += [f"schedule clear {NS}:story/snd/bed_{key}/loop", f"stopsound {PA()} {c['source']} {c['event']}"]
            for p in out_parts:
                start.append(f"schedule clear {NS}:story/snd/bed_{p['key']}/loop")
            start.append("# (the incoming bed's earlier copies, if any, are stopped by the ramp's steps)")
        for p in parts:
            start.append(f"schedule clear {NS}:story/snd/bed_{p['key']}/loop")
        start += steps[0]
        self.ramps.append((base + "/start", start))
        for k in range(1, n):
            self.ramps.append((f"{base}/s{k}", steps[k]))
            self.ramp_paths["bed"].append(f"{base}/s{k}")
        # the start function itself is the entry; its scheduled successors are cleared by stop_bed
        return base + "/start"

    # ------------------------------------------------------------------ the functions
    def write(self):
        ex = self.ctx.extra_functions
        stops = {"bed": [], "music": [], "loop": []}
        for (kind, key), c in sorted(self.cues.items()):
            base = f"story/snd/{kind}_{key}"
            if c["at"] is None:
                play = f"execute at {P()} run playsound {c['event']} {c['source']} {PA()} ~ ~ ~ {num(c['vol'])} 1.0 1.0"
            else:
                x, y, z = c["at"]
                play = f"playsound {c['event']} {c['source']} {PA()} {num(x)} {num(y)} {num(z)} {num(c['vol'])} 1.0 0.0"
            if c["loop"]:
                ex[f"{base}/loop"] = [f"# {c['event']}: {c['secs']:.1f}s{'' if c['known'] else ' (recording not found: default length)'}",
                                      play, f"schedule function {NS}:{base}/loop {max(1, T(c['secs']))}t"]
                ex[f"{base}/start"] = [fn(f"story/snd/stop_{kind}"), fn(f"{base}/loop")]
            elif c.get("chain"):
                cev, csecs = c["chain"]
                cplay = play.replace(c["event"], cev)
                ex[f"{base}/chain"] = [f"# {cev}: {csecs:.2f}s, repeats until stopped (it follows {c['event']}, {c['secs']:.2f}s)",
                                       cplay, f"schedule function {NS}:{base}/chain {max(1, T(csecs))}t"]
                ex[f"{base}/start"] = [fn(f"story/snd/stop_{kind}"), play, f"schedule function {NS}:{base}/chain {max(1, T(c['secs']))}t"]
            else:
                ex[f"{base}/start"] = [fn(f"story/snd/stop_{kind}"), play]
            stops[kind] += ([f"schedule clear {NS}:{base}/loop"] if c["loop"] else []) + [f"stopsound {PA()} {c['source']} {c['event']}"]
            if c.get("chain"):
                stops[kind] += [f"schedule clear {NS}:{base}/chain", f"stopsound {PA()} {c['source']} {c['chain'][0]}"]
        for stem, parts in self.mixes.items():
            ex[f"story/snd/bed_{stem}/start"] = [fn("story/snd/stop_bed")] + [fn(f"story/snd/bed_{p}/loop") for p in parts]
        for path, lines in self.ramps:
            ex[path] = lines
        for path in self.ramp_paths["bed"]:
            stops["bed"].insert(0, f"schedule clear {NS}:{path}")
        for kind in ("bed", "music", "loop"):
            ex[f"story/snd/stop_{kind}"] = stops[kind] or ["# nothing registered"]
        ex["story/snd/stop_all"] = [fn("story/snd/stop_bed"), fn("story/snd/stop_music"), fn("story/snd/stop_loop")]
        # everything: the three kinds, then whatever else is still sounding (a line's tail, a long effect, a one-shot)
        ex["story/snd/silence"] = [fn("story/snd/stop_all"), f"stopsound {PA()}"]

    def names(self):
        return sorted(f"{k}:{key}" for (k, key) in self.cues)


def silence_cmds():
    """Every bed, cue and layer stopped and their timers cleared, then `stopsound` for every other sound."""
    return [fn("story/snd/silence")]


def sfx(event, at=None, vol=1.0, pitch=1.0, minvol=0.0, source="master"):
    """One-shot effect.  `event`: "sfx.door_boom" or "angel:sfx.door_boom" (or a vanilla "minecraft:..." id).  at=(x, y, z): from that place,
    heard from its direction by the player (volume 16 blocks per 1.0, minvol is the volume the player hears beyond that); None: at the player."""
    if ":" not in event:
        event = f"{NS}:{event}"
    if at is None:
        return f"execute at {P()} run playsound {event} {source} {PA()} ~ ~ ~ {num(vol)} {num(pitch)} 1.0"
    x, y, z = at
    return f"playsound {event} {source} {PA()} {num(x)} {num(y)} {num(z)} {num(vol)} {num(pitch)} {num(minvol)}"
