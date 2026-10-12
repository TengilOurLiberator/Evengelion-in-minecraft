"""Scene 6, The plug.

Sealed in the entry plug (a seat in a white capsule, then dark), flooded with amber fluid that rises past the eyes, first contact: the capsule
walls go clear and the boy looks down the bridge from the giant's eyes, synchronisation locks, the lock bolts go, the bridge slides away; through
black to the launch pad where he now stands as the giant; the word is given; up the shaft by physics (levitation, no per-tick teleports);
white at the top; night, the city, and the Angel at the end of the avenue.  Hands over to scene 7 (the fight).

How it looks (see launch_shell.py): everything the boy sees through is a box of thin display slabs round his head -- black opaque (dark),
black glass (dim instrument light), rising orange glass (the fluid), orange glass (the cockpit), white (the flashes).  No real water, no
nausea, no camera movement except the one acceleration up the shaft.

Beats: 60 sealed in; 61 from the pad; 70 on the surface.  Rei absent, Misato / Ritsuko / Gendo are radio voices (2) throughout.
"""
import launch_audio as au
import launch_cage as cg
import launch_geo as geo
import launch_hooks
import launch_shell as sh
import worldgen_sky
from context import tp_player
from core import CFG, P, PA, T, blind, fn, num, sset
from engine import C

N = 6
TITLE = "The plug"

# ---------------------------------------------------------------------------------------------------- numbers you may want to change
FLUID_TICKS = 160            # the amber surface climbs from the floor to the ceiling in 8 s (sfx.fluid_fill is 8 s long)
FLUID_BRIGHT = 15            # light level of the amber glass (0..15): it must glow, not look like mud (it was 12 with two layers: brown)
FLUID_LAYERS = 3             # stained glass is only 46 % opaque: three layers of the fluid give 84 % amber at full light, over the dark shell
PAD_FACING = (0.0, -60.0)    # yaw, pitch the boy is turned to on arrival at the launch pad (during the black): up the shaft
PARTICLE_EVERY = 3           # ticks between the sparks of light at the rising surface
DARK_LAYERS = 3
COCKPIT_BRIGHT = 13          # the amber glass round the head in the cockpit (one layer: the bridge must stay clear)
FLUID_BLOCK = "orange_stained_glass"
CONTACT_MOVE = 3.0           # seconds after 6.07 starts that the boy is moved to the cockpit (sfx.contact blooms from 2.4 s)
CLIMB_AMPLIFIERS = (6, 12, 18, 24, 29)      # levitation amplifier steps, 0.2 s apart: the ascent builds up over a second (final ~27 blocks/s)
CLIMB_STEP = 0.2
ASCENT_TIMEOUT = 9.0         # if the feet have not reached CUT_FEET_Y by then (lag, a stuck player), cut anyway
CITY_FLASH = (8.0, 14.0, 8.0)                       # half sizes of the white box round the head at the city (giant scale)
SHAFT_FLASH = (6.5, 14.0, 6.5)                      # ... and in the shaft (14 x 14 inside)
TURN_AT_ARRIVAL = True       # face the avenue (north) when arriving at the surface: done inside the white flash


def build(s, ctx):
    launch_hooks.register(ctx, geo)
    cg.register(ctx)
    audio = ctx.audio
    A = ctx.anchor
    seat, pad, top = A("hq.plug_seat"), A("hq.pad"), A("city.launch_top")
    angel_start = A("city.angel_start")
    cm, sm = A("hq.captain_mark"), A("hq.scientist_mark")
    A("hq.face")
    if (pad["x"], pad["y"], pad["z"]) != geo.PAD_FEET:
        ctx.warn(f"scene 6: anchor hq.pad {(pad['x'], pad['y'], pad['z'])} differs from launch_geo.PAD_FEET {geo.PAD_FEET}")
    for line in geo.shaft_report(ctx)[0]:
        ctx.warn("scene 6: " + line)

    def span(lid, gap=True):
        """seconds the story spends on a line: the recording plus the engine's tail and gap"""
        return (ctx.lines[lid].ticks + (T(CFG.gap) if gap else 0)) / 20.0

    ap = launch_hooks.players()
    plug_feet = (seat["x"], geo.PLUG_FEET_Y, seat["z"])
    b = geo.PLUG_BOX
    cx, cy, cz = (b["x0"] + b["x1"]) / 2.0, (b["y0"] + b["y1"]) / 2.0, (b["z0"] + b["z1"]) / 2.0
    dark = lambda block: sh.box_shell("angel.lshell", block, (cx, cy, cz), (1.48, 2.48, 4.48), bright=0, layers=DARK_LAYERS)
    fluid = sh.Fluid("angel.lfluid", FLUID_BLOCK, b["x0"] + 0.07, b["x1"] - 0.07, b["y0"] + 0.07, b["y1"] - 0.1,
                     b["z0"] + 0.07, b["z1"] - 0.07, bright=FLUID_BRIGHT, layers=FLUID_LAYERS, men_tag="angel.lmen")
    cockpit = lambda block: sh.box_shell("angel.lcock", block, geo.COCKPIT_EYE, (geo.COCKPIT_HALF,) * 3, bright=COCKPIT_BRIGHT)
    # the surface passes the eyes (feet + 1.62) at this fraction of the climb
    eyes_frac = (geo.PLUG_FEET_Y + 1.62 - (b["y0"] + 0.07)) / fluid.full_height
    # sparks of light along the rising surface: one small function per step (each schedules the next, so the surface line reads as it climbs past the
    # eyes); halt clears them
    n_p = FLUID_TICKS // PARTICLE_EVERY
    for k in range(n_p):
        y = fluid.surface_y(min(1.0, k * PARTICLE_EVERY / float(FLUID_TICKS)))
        lines = [f"particle minecraft:dust{{color:[1.0,0.82,0.35],scale:0.7}} {num(cx)} {num(y, 2)} {num(cz)} 1.3 0.03 3.8 0 5 force"]
        if k + 1 < n_p:
            lines.append(f"schedule function angel:story/launch/fp{k + 1} {PARTICLE_EVERY}t")
        ctx.extra_functions[f"story/launch/fp{k}"] = lines
        ctx.fx_scheduled.append(f"story/launch/fp{k}")
    ctx.extra_functions["story/launch/flash_up"] = sh.box_shell("angel.lflash", "white_concrete", None, SHAFT_FLASH, bright=15)
    ctx.extra_functions["story/launch/flash_down"] = sh.box_shell("angel.lflash", "white_concrete", None, CITY_FLASH, bright=15)

    # ================================================================ setup (a jump runs it; the hand-over from scene 5 is a jump)
    s.do(blind(4.5), note="fade out")
    s.sleep(0.4)
    s.do(*ctx.preload(pad["x"], pad["z"]), fn("cast/remove_all"), "function angel:cast/gurney_remove", *audio.stop("bed"),
         note="preload the shaft; nobody is in the capsule")
    s.move_player(seat["x"], geo.PLUG_FEET_Y, seat["z"], settle=0.9, note="the player to the plug")
    s.do(*worldgen_sky.sky("hq"), *cg.sit_at(plug_feet), f"gamemode adventure {PA()}",
         sset("#present_misato", 0), sset("#present_ritsuko", 0), sset("#present_gendo", 0), sset("#present_rei", 0), sset("#beat", 54),
         note="the boy to the seat in the plug, in the dark; the capsule is white and lit (the lamps are part of the set)")
    s.sleep(1.2)
    s.setup_done()

    # ================================================================ sealed
    s.do(au.sfx("hatch_close"), note="the hatch closes (sfx.hatch_close, 4.5 s); the white capsule is still lit for a moment")
    s.sleep(1.2)
    s.do(*dark("black_concrete"), note="DARK: opaque black round the head")
    s.bed("plug", note="the sealed bed amb.plug")
    s.sleep(1.2, note="own breathing in the dark")
    s.present(misato=2, ritsuko=2, gendo=2, rei=0)
    s.say("6.01")                                                   # public address, through the hull
    s.sleep(0.8, note="machinery")
    s.say("6.02")
    s.do(sh.set_block("angel.lshell", "black_stained_glass"), note="dim instrument light: the black turns to dark glass")
    s.sleep(0.8)
    s.beat(60)
    s.say("6.03")

    # ================================================================ the fluid
    prep_at = 1.0
    s.do(au.sfx("fluid_fill"), *fluid.spawn(), note="6.04: the amber fluid begins (sfx.fluid_fill, 8 s): amber glass, and the surface itself as a bright sheet and line")
    s.after(0.3, *fluid.rise_to(fluid.full_height, FLUID_TICKS), fn("story/launch/fp0"),
            note="the amber surface climbs, one smooth rise, with sparks of light along it")
    s.after(0.3 + eyes_frac * FLUID_TICKS / 20.0, *audio.start("bed", "plug_flooded"),
            note="the surface passes the eyes: the bed goes dull and close (amb.plug_flooded)")
    # the cage is made ready for the view from the giant's eyes while the boy is under the fluid
    s.after(prep_at, *cg.forceload_cage(), note="cage chunks held")
    s.after(prep_at + 3.0, *cg.cast_for_cockpit(ctx), cg.lights_on(),
            note="the cage for the cockpit view: lights on, Misato and Ritsuko on their marks, Gendo in the booth, no Rei, no gurney")
    s.say("6.04")
    s.say("6.05")
    s.say("6.06")
    s.wait_answer(speaker="misato", prompt="answer Misato", timeout=6, note="optional: goes on by itself after 6 s")

    # ================================================================ contact: the walls go clear
    t = CONTACT_MOVE
    s.do(au.sfx("contact"), note="6.07: sfx.contact; the dark glass dissolves, the amber shimmers, then white")
    s.after(1.0, sh.kill("angel.lshell"), note="the capsule walls turn to glass: only the amber is left")
    flick = [(1.5, "white_stained_glass"), (1.7, FLUID_BLOCK), (1.9, "yellow_stained_glass"), (2.1, FLUID_BLOCK),
             (2.3, "white_stained_glass"), (2.5, FLUID_BLOCK), (2.7, "white_stained_glass"), (t - 0.15, "white_concrete")]
    for at, blk in flick:
        s.after(at, sh.set_block("angel.lfluid", blk), note=f"shimmer {blk}")
    s.after(t, *cg.sit_at(geo.COCKPIT_FEET, turn_south=True), *cockpit("white_concrete"), sh.kill("angel.lfluid"), sh.kill("angel.lmen"),
            note="MOVE to the cockpit in front of the giant's face, in the white (turned to face down the bridge if he looks away)")
    s.after(t + 0.15, sh.set_block("angel.lcock", "white_stained_glass"), note="the white thins")
    s.after(t + 0.40, sh.set_block("angel.lcock", FLUID_BLOCK), note="the amber tint stays")
    s.say("6.07")
    # the rising tone climbs for 4.2 s and locks: it starts so that the lock falls on the first syllable of 6.09
    s.after(max(0.05, span("6.08") - 4.2), au.sfx("sync_rise"), note="sfx.sync_rise: locks as 6.09 begins")
    s.say("6.08")
    s.do(fn("story/launch/eyes_on"), note="the eyes light as the tone locks")
    s.say("6.09")
    s.say("6.10")
    s.say("6.11")

    # ================================================================ release
    s.do(*[f'function angel:cast/walk {{id:"{cid}",x:{num(x)},y:{num(cm["y"])},z:{num(cm["z"] + 42.0)},speed:0.17}}'
           for cid, x in (("misato", cm["x"]), ("ritsuko", sm["x"]))], note="Misato and Ritsuko walk back along the bridge")
    s.say("6.12")
    for at, n in ((1.0, 1), (1.7, 2), (3.6, 3)):
        s.after(at, au.sfx(f"bolt_{n}", 1.2), *_bolt_fx(n), note=f"lock bolt {n}")
    s.after(1.3, au.sfx("bridge_slide"), note="the bridge slides away (sound only; the deck itself is part of the set)")
    s.say("6.13")
    s.say("6.14")
    s.do(blind(3.0), note="through black to the launch pad")
    s.sleep(0.4, note="dark")
    s.do(*cg.leave_seat(), sh.kill("angel.lcock"), fn("story/launch/eyes_off"), fn("cast/remove_all"), "function angel:cast/gurney_remove",
         *cg.forceload_cage_off(), *audio.start("bed", "hq"), *au.sfx_stop("bolt_1", "bolt_2", "bolt_3", "bridge_slide", "contact", "sync_rise"),
         ctx.preload(pad["x"], pad["z"]), note="in the dark: off the seat, the cage let go")
    # he arrives ALREADY LOOKING UP THE SHAFT (the teleport is through black: the only place to turn his head), and the move is guarded
    s.move_player(pad["x"], pad["y"], pad["z"], yaw=PAD_FACING[0], pitch=PAD_FACING[1], settle=0.5, note="to the launch pad, facing up the shaft")
    s.do(f"execute as {P()} run function angel:fight/become_giant", note="the boy is now the giant, free, no seat")
    s.sleep(1.3, note="the black lifts")
    s.music("launch", note="music.launch: its 20 s build ends at the kick; the drive begins there")
    s.beat(61)
    s.say("6.15")

    # ================================================================ the word
    s.do(*ctx.preload(top["x"], top["z"]), *ctx.preload(angel_start["x"], angel_start["z"]), note="hold the city chunks")
    s.say("6.16")
    s.sleep(2.5, note="a long pause")
    s.say("6.17")
    kick_in = span("6.15") + span("6.16") + 2.5 + span("6.17") + span("6.18") + span("6.19", False)
    ctx.warn(f"scene 6: the kick comes {kick_in:.1f} s after the pad appears; music.launch (20 s build) starts with the pad")
    # the whine climbs for 3 s and ends on 'launch!' (about 1.6 s into 6.19)
    s.after(max(0.05, span("6.18") + 1.6 - 3.0), au.sfx("launch_charge"), note="sfx.launch_charge: peaks on 'launch!'")
    s.say("6.18")
    s.say("6.19", gap=0)

    # ================================================================ the launch: up the shaft by physics
    climb = [f"effect give {ap} minecraft:levitation 12 {a} true" for a in CLIMB_AMPLIFIERS]
    s.do(*audio.stop("bed"), au.sfx("launch", 2.0), climb[0], sset("#l.y", 0),
         f"execute positioned {num(angel_start['x'])} {num(angel_start['y'])} {num(angel_start['z'])} rotated 0 0 run function angel:angel/summon {{height:30}}",
         note="THE KICK: levitation builds, sfx.launch; the Angel is summoned at the far end of the avenue")
    for k, a in enumerate(climb[1:], 1):
        s.after(CLIMB_STEP * k, a, note=f"levitation step {k}")
    read_y = f"execute store result score #l.y angel.story run data get entity {P()} Pos[1] 1"
    at_eyes = f"execute at {P()} anchored eyes positioned ^ ^ ^ run "
    s.until(C.score("#l.y", f"{int(geo.CUT_FEET_Y)}..", est=4.8), timeout=ASCENT_TIMEOUT, tick=[read_y],
            on_done=[at_eyes + fn("story/launch/flash_up")], note="up the shaft until the feet pass y 108, then the white-out")
    s.sleep(0.2, note="white")
    # ---- the cut: to the city, standing on the lift platform, at giant scale, no upward motion (a teleport zeroes the velocity)
    face = " 180 0" if TURN_AT_ARRIVAL else ""
    tp_top = f"tp {P()} {num(top['x'])} {num(top['y'])} {num(top['z'])}{face}"
    s.do(f"effect clear {ap} minecraft:levitation", tp_top,
         sh.kill("angel.lflash"), at_eyes + fn("story/launch/flash_down"),
         *audio.stop("music"), *au.sfx_stop("launch", "launch_roar", "launch_charge"),
         au.sfx("launch_arrive", 2.0), *worldgen_sky.sky("city"),
         note="THE CUT: white; to city.launch_top (giant, on the lift, facing the avenue); music and roar end, the lift locks")
    s.steps[-1].guarded = True                       # (the checker: this teleport is followed by the wait below)
    # the move is 2000 blocks (the chunks were forceloaded at the pad, long before): make sure he is there, re-teleporting every 0.4 s if not
    s.until(C.near(top["x"], top["y"], top["z"], 8.0, est=0.1), timeout=4.0, nag=(0.4, 0.4, [tp_top]), on_timeout=[tp_top], est=0.1,
            note="he is really on the lift (re-teleported every 0.4 s if not)")
    s.bed("city_night", note="night: the city bed")
    s.after(0.6, sh.set_block("angel.lflash", "white_stained_glass"), note="the white thins")
    s.after(1.2, sh.kill("angel.lflash"), note="night")

    # ================================================================ the surface
    s.sleep(1.4, note="the lift locks, wind")
    s.say("6.20")
    s.sleep(2.0, note="quiet")
    s.say("6.21")
    s.beat(70)
    s.next_scene(7)


def _bolt_fx(n):
    """A hammer blow of dust and sparks at the restraint arms on the giant's shoulders (the sound is the thing; this is a little more)."""
    x, y, z = {1: (3071.0, 44.0, 42.0), 2: (3121.0, 44.0, 42.0), 3: (3071.0, 44.0, 57.0)}[n]
    return [f'particle minecraft:falling_dust{{block_state:"minecraft:gray_concrete"}} {num(x)} {num(y + 5)} {num(z)} 3 2 3 0 60 force',
            f"particle minecraft:explosion {num(x)} {num(y)} {num(z)} 1 1 1 0 2 force"]
