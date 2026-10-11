"""Sound for scenes 6 and 7 that the engine's audio does not cover.

Beds (`s.bed("plug")`) and music (`s.music("launch")`) are the engine's (audio.py): one bed and one cue at a time, each restarting itself
and stopped by halt.  What is left here are the one-shot effects, with their volume, and the list of long effects the restore function
silences (a roar or a rising tone must not outlive a `story/stop`).  `sfx.card` is left alone: scene 5's card may still be sounding when
scene 6 begins.
"""
from audio import sfx as _sfx
from core import NS, PA

# long one-shots of these scenes (silenced by restore)
SFX_LONG = ["launch", "launch_roar", "launch_charge", "fluid_fill", "contact", "sync_rise", "hatch_close", "bridge_slide",
            "bolt_1", "bolt_2", "bolt_3", "launch_arrive"]


def sfx(name, vol=1.0, pitch=1.0):
    """playsound angel:sfx.<name> at the player (not positional)"""
    return _sfx(f"sfx.{name}", None, vol, pitch)


def sfx_stop(*names):
    return [f"stopsound {PA()} * {NS}:sfx.{n}" for n in names]


def stop_sfx_cmds():
    return sfx_stop(*SFX_LONG)
