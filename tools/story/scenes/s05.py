"""Scene 5, The cage.  The scene the whole piece exists for; every cue of cue-sheet.md is staged here.

Ritsuko leads the boy through the open cage door and out onto the bridge in the dark; the door shuts behind them with a boom, and the bridge
is silent but for a few dim red lamps.  When he reaches the end (hq.face) -- or stops within four blocks of it -- Ritsuko says 5.01, and
nothing happens for three seconds.  Then the cage lights come on in eight banks, farthest first, each with a heavy breaker clunk, the last
bank the one on the giant's face; the eyes stay dark.  Three seconds of that, 5.02, 5.03.  The booth lights come on; his father is standing in
the glass, already looking down (5.04-5.12, the order, Misato steps forward on 5.07, Ritsuko turns on 5.12; 5.13-5.20, Misato looks at the
floor on 5.17).  The first impact (lights flicker in a third of the banks, dust in the beams, the coolant rings; 5.21-5.24).  If he agrees at
the wait after 5.24 the story goes straight to "yes".  Otherwise Rei is wheeled in through the hospital door (5.25-5.31), the second, harder
impact comes: every light goes out for a second, a lighting rig tears loose from the roof and falls, Rei is thrown from the gurney to the
deck, the giant's hand comes up out of the coolant and the rig breaks on it, the eyes light for as long as the hand is up (5.32-5.35); he
goes to her (5.36-5.38) and the story waits for his yes, nudging him with 5.39, 5.40, 5.41, then 5.40 and 5.41 again, a distant impact after
each from 5.40 on.  At his yes everything stops, the alarm cuts (5.42, 5.43); Ritsuko leads him out, the lights going out behind them
(5.44 from behind) and the card EVANGELION UNIT 01.

Beats: 41 on arrival, 50 at the lights, 51 after 5.05, 52 after 5.20, 53 after 5.35, 54 at his yes.  Ambience: amb.lake until the door shuts
(then silence), amb.cage with music.cage from the first bank, music.father from 5.04, music.decision from the second impact until his yes
(with a repeating alarm layer from sfx.klaxon), music.resolve from the yes.

Two paths through the consent: a "yes" at the wait after 5.24 (a consent-capable wait: the bridge classifies the answer; a reply that is
not a yes ends the wait without consent and the story goes on with 5.25) skips straight to the yes; otherwise the wait after 5.38 holds
until he agrees, nudged.
"""
import math

import lead as L
from audio import sfx
from context import cast_look, cast_mount, cast_pose, cast_remove, cast_scale, cast_summon, tp_player
from core import CFG, OBJ, P, PA, T, blind, dir_to_yaw, fn, num, sset
from engine import C, Cond, Nudges
from hq_cage import N_BANKS, booth_anchor, cage, dirty_cmd
from objective import follow_objective, objective
import worldgen_sky

N = 5
TITLE = "The cage"

import pace

GURNEY_SETTLE = 0.7        # seconds the cast's gurney takes to turn to its goal and settle (the arrival score comes a few ticks after it stops)


def walk(who, x, y, z, speed=0.13):
    return f'function angel:cast/walk {{id:"{who}",x:{num(x)},y:{num(y)},z:{num(z)},speed:{num(speed)}}}'


def build(s, ctx):
    PC = pace.PACE
    SPEED = PC.walk_speed
    tight = PC.tight
    A = ctx.anchor
    cdoor, bstart, face = A("hq.cage_door"), A("hq.bridge_start"), A("hq.face")
    cap, sci, gin, gmark = A("hq.captain_mark"), A("hq.scientist_mark"), A("hq.gurney_in"), A("hq.gurney_mark")
    shield, d2, booth = A("hq.shield"), A("hq.debris_2"), booth_anchor(ctx)
    cg = cage(ctx)
    XC = cdoor["x"]                       # 3096.5, the centre of the catwalk, the door and the bridge
    Y = cap["y"]                          # 54, the deck
    sound_at_bridge = (XC, Y + 4.0, 100.0)

    # where things stand
    RIT_MARK = (sci["x"], Y, sci["z"])                 # (98.5, 54, 76.5)
    MIS_MARK = (cap["x"], Y, cap["z"])                 # (94.5, 54, 76.5)
    MIS_STEP = (XC - 1.5, Y, face["z"] + 1.9)          # Misato steps forward on 5.07: beside and a little behind the boy
    REI_MID = (XC - 0.5, Y, 77.4)                      # where Rei lies after she is thrown (her middle); the shield column is z 78.5
    EYE = 1.6
    GENDO_SCALE = 2.0                                  # he is 25 blocks away at the front edge of the booth: 1.0 is a doll in a window, 2.0 a figure
    BOOTH_EYE = (booth["x"], booth["y"] + 1.62 * GENDO_SCALE, booth["z"])      # (the scaled mannequin's eyes)
    HE_STOPS = (face["x"], face["y"] + EYE, face["z"])  # the boy's eyes at the stop, which Gendo looks at
    GURNEY_START = (gin["x"] - 5.0, Y, gin["z"])       # inside the hospital vestibule, behind the door at x = gin.x
    SEAT = (gmark["x"] + 0.9, Y + 0.945, gmark["z"])   # where Rei's foot end is on the gurney at the mark

    def eyes_of(p):
        return (p[0], p[1] + EYE, p[2])

    # ================================================================ setup (a jump runs it; a hand-over from scene 4 skips it)
    s.do(blind(PC.s5_setup_fade), note="fade out")
    s.sleep(0.4)
    s.move_player(cdoor["x"], cdoor["y"], cdoor["z"], settle=PC.s5_setup_settle, before=ctx.preload_rect(3040, 16, 3135, 176),
                  note="the player to hq.cage_door (the head is not turned), the whole cage and the lake hall forceloaded")
    s.do(fn("story/hq/reset_cage"), fn("story/hq/reset_lobby"), dirty_cmd(), fn("story/hq/door_opened"), fn("story/hq/side_closed"), *worldgen_sky.sky("hq"),
         note="the set as scene 4 leaves it: cage dark, the cage door open, the hospital door closed, hand lowered, eyes dark")
    s.do(sset("#beat", 41), sset("#present_misato", 1), sset("#present_ritsuko", 1), sset("#present_gendo", 0), sset("#present_rei", 0),
         cast_summon("ritsuko", XC, Y, cdoor["z"] - 1.8, 180.0), cast_summon("misato", XC - 1.1, Y, cdoor["z"] + 1.8, 180.0),
         note="Ritsuko in front of the door, Misato beside the boy")
    s.do(*ctx.audio.start("bed", "lake"), note="the lake hall's air")
    s.sleep(PC.s5_setup_sleep)
    s.setup_done()

    # ================================================================ dark: onto the bridge behind Ritsuko
    s.do(dirty_cmd(), fn("story/hq/side_closed"), sset("#consent", 0), sset("#f.hold", 0), sset("#f.rei_here", 0))
    door_cells = [(x, y, z) for (x, y, z) in cg.door]                      # the cage door is open when she walks: its cells count as air for the companion's path
    L.lead(s, ctx, "ritsuko", [
        L.Stop(XC, Y, 139.0, wait=False, note="through the cage door"),
        L.Stop(bstart["x"], Y, bstart["z"], wait=False, note="hq.bridge_start"),
        L.Stop(XC, Y, 128.0, note="out on the bridge"),
    ], speed=SPEED, companion=("misato", 3.2, 1.2), start=(XC, cdoor["z"] - 1.8), follow_text="Go through the door",
        companion_at=(XC - 1.1, cdoor["z"] + 1.8), nav_open=door_cells)
    # the door shuts behind them with a boom; then silence
    s.do(fn("story/hq/door_close"), sfx("sfx.door_heavy", at=(XC, Y + 3.0, 140.5), vol=3.0, minvol=0.8), *ctx.audio.stop("bed"),
         note="the cage door shuts behind them")
    s.after(0.4, sfx("sfx.door_boom", at=(XC, Y + 3.0, 140.5), vol=4.0, pitch=0.8, minvol=0.9), note="the boom")
    s.sleep(PC.s5_door_pause)
    # they go to their marks in the dark; the boy walks to the end of the bridge
    s.do(walk("misato", *MIS_MARK, speed=PC.walk_misc + 0.01), note="Misato to captain_mark")
    L.lead(s, ctx, "ritsuko", [
        L.Stop(XC, Y, 100.0, wait=not tight, note="the middle of the bridge"),
        L.Stop(*RIT_MARK, note="Ritsuko to scientist_mark"),
    ], speed=SPEED, start=(XC, 128.0))
    s.do(sset("#f.hold", 0), note="count how long he stands near the end")
    fx, fy, fz = face["x"], face["y"], face["z"]
    s.until([C.near(fx, fy, fz, 1.5, est=PC.s5_est_face), C.score("#f.hold", "60..", est=PC.s5_est_face)], timeout=150, est=PC.s5_est_face,
            tick=[f"execute positioned {num(fx)} {num(fy)} {num(fz)} if entity {P('distance=..4')} run scoreboard players add #f.hold angel.story 1",
                  f"execute positioned {num(fx)} {num(fy)} {num(fz)} unless entity {P('distance=..4')} run scoreboard players set #f.hold angel.story 0"],
            hint=("Walk to the end of the bridge.", []), hint_after=40,
            objective=objective("Walk out onto the bridge", at=(fx, fy, fz), line="Walk out to the end of the bridge, toward the giant", how="walk", grace=PC.s5_face_grace),
            on_timeout=[tp_player(fx, fy, fz)], note="the player reaches hq.face (or stops within 4 blocks of it for 3 s)")
    s.sleep(PC.s5_face_pause)
    s.say("5.01")
    s.sleep(PC.s5_nothing, note="the beat of nothing before the lights")

    # ================================================================ lights: eight banks, farthest first, the face last
    s.beat(50)
    for k in range(N_BANKS):
        cmds = [fn(f"story/hq/bank_on_{k}"),
                sfx(f"sfx.breaker_{k % 3 + 1}", at=cg.bank_pos[k], vol=3.0, pitch=0.9 if k == N_BANKS - 1 else 1.0, minvol=0.7)]
        if k == 0:
            cmds += ctx.audio.start("bed", "cage") + ctx.audio.start("music", "cage")
        s.do(*cmds, note=f"bank {k} on ({cg.banks[k]['on'].__len__()} lights)" + (" -- the face" if k == N_BANKS - 1 else ""))
        s.sleep(PC.s5_bank_step)
    s.sleep(PC.s5_lights_stand, note="let it stand before anyone speaks")
    s.say("5.02")
    s.say("5.03")
    s.wait_answer(speaker="ritsuko", prompt="answer Ritsuko")

    # ================================================================ the father
    # The eye must go to the booth without the head being turned: the cage's own lights dip a little (three of the eight banks go out for 1.3 s,
    # a change the whole field of view feels), and in the dip ONE hard light snaps on him with its sound coming from his direction (a flare of
    # light at his face too); Misato and Ritsuko turn and look up at him a beat later (the way they look is the second signal), and he says
    # nothing for two full seconds more.
    dip = cg.flicker("dip", [1, 3, 5], [(0, "off"), (26, "on")])
    gyaw = dir_to_yaw(HE_STOPS[0] - booth["x"], HE_STOPS[2] - booth["z"])
    # Gendo stands exactly on hq.booth (the front edge of the balcony, so that no pane or rail crosses him), at twice life size: a mannequin with
    # the `scale` attribute 2.0 (angel:cast/scale), looking down at the boy's stop
    s.do(dip, note="the cage's other lights dip (banks 1, 3, 5 off for 1.3 s)")
    s.sleep(0.4)
    s.do(cast_summon("gendo", booth["x"], booth["y"], booth["z"], gyaw), cast_scale("gendo", GENDO_SCALE), *L.face(ctx, "gendo", *HE_STOPS, ticks=8),
         sset("#present_gendo", 1), fn("story/hq/booth_on"), fn("story/hq/booth_flare"),
         sfx("sfx.booth_light", at=(booth["x"], booth["y"] + 2.5, booth["z"]), vol=4.0, minvol=1.0),
         note="ONE hard light snaps on him, sfx.booth_light from the booth, a flare at his face: Gendo stands at the front edge, looking down")
    s.after(0.35, *L.face(ctx, "misato", *BOOTH_EYE), *L.face(ctx, "ritsuko", *BOOTH_EYE), note="Misato and Ritsuko both turn and look up at him")
    s.sleep(PC.s5_father_hold, note="a beat of him lit and still, the women staring up at him, before he speaks (two full seconds in the full pacing)")
    s.do(*ctx.audio.start("music", "father"), note="music: the father")
    s.say("5.04")
    s.say("5.05")
    s.wait_answer(speaker="gendo", prompt="answer your father")

    # ================================================================ the order
    s.beat(51)
    s.do(*L.face(ctx, "ritsuko", *BOOTH_EYE), *L.face(ctx, "misato", *BOOTH_EYE), note="both look up at the booth")
    s.say("5.06")
    s.do(walk("misato", *MIS_STEP, speed=0.12), note="Misato steps forward")
    s.after(2.0, *L.face(ctx, "misato", *BOOTH_EYE), note="she looks up at the booth")
    s.say("5.07")
    s.do(*L.face(ctx, "ritsuko", *eyes_of(MIS_STEP)), note="Ritsuko answers Misato (she does not move)")
    s.say("5.08")
    s.do(*L.face(ctx, "misato", *eyes_of(RIT_MARK)))
    s.say("5.09")
    s.say("5.10")
    s.say("5.11")
    s.do(L.face_player("ritsuko"), note="on 5.12 Ritsuko turns to the boy")
    s.say("5.12")
    s.wait_answer(speaker="ritsuko", prompt="answer Ritsuko")
    s.say("5.13")
    s.say("5.14")
    s.say("5.15")
    s.say("5.16")
    s.do(*L.face(ctx, "misato", MIS_STEP[0], Y + 0.0, MIS_STEP[2] - 0.8), note="on 5.17 Misato looks at the floor")
    s.say("5.17")
    s.say("5.18")
    s.say("5.19")
    s.wait_answer(speaker="gendo", prompt="answer your father")
    s.say("5.20")
    s.beat(52)

    # ================================================================ the first impact
    s.sleep(PC.s5_impact_pause, note="a held breath")
    fl1 = cg.flicker("hit1", [1, 3, 5], [(0, "off"), (3, "on"), (6, "off"), (8, "on"), (13, "off"), (15, "on")])
    s.do(fn("story/hq/impact1"), fl1, note="a deep blow from above: a third of the banks flicker, dust in the beams, the coolant rings")
    s.sleep(PC.s5_impact_after)
    s.say("5.21")
    s.say("5.22")
    s.say("5.23")
    s.do(L.face_player("misato"), note="Misato turns to the boy")
    s.say("5.24")
    # a consent-capable wait: the bridge classifies the answer; a yes goes straight to the yes, any other answer is voiced by the character
    # and the wait ends without consent (answer_ends); 45 s of silence also go on
    s.do(sset("#consent", 0))
    s.wait_consent(speaker="misato", prompt="answer Misato", answer_ends=True, timeout=PC.s5_consent_timeout, est=6.0, note="WAIT (a yes here goes straight to the yes)")
    s.branch(C.score("#consent", "1"), "yes_early")
    s.sleep(PC.s5_early_pause)

    # ================================================================ Rei
    s.say("5.25")
    s.say("5.26")
    s.say("5.27")
    s.do(sset("#present_rei", 2), note="Rei on the intercom")
    # The gurney starts to roll as Rei says yes (5.28) and is timed to ARRIVE as 5.30 ends: nobody stands waiting for it.  While it comes, the door
    # opens, the lamps over the hospital door blink, Misato and Ritsuko turn their heads toward it (the way they look is the cue to look west), the squeak
    # of its wheels passes along the spur (two sounds, the second from half way), and the medics come into view through the door.
    gx, gy, gz = GURNEY_START
    span = lambda lid: (ctx.lines[lid].ticks + T(CFG.gap)) / 20.0
    travel = abs(gmark["x"] - gx)
    if tight:
        arrive_in = span("5.28") + span("5.29") + PC.s5_gurney_into_530 - GURNEY_SETTLE            # it arrives a couple of seconds into 5.30 (BASE: its exact length is known)
    else:
        arrive_in = span("5.28") + span("5.29") + span("5.30") - 0.4 - GURNEY_SETTLE      # seconds from this step to the end of 5.30's own recording
    g_speed = round(travel / (arrive_in * 20.0), 4)
    vblink = cg.flicker("vest_blink", [], [(0, "off"), (4, "on"), (8, "off"), (12, "on"), (20, "off"), (24, "on")], extra_off=["vest"])
    s.do(f"execute positioned {num(gx)} {num(gy)} {num(gz)} rotated -90 0 run function angel:cast/gurney",
         f"execute positioned {num(gx)} {num(gy)} {num(gz)} rotated -90 0 run function angel:cast/summon {{id:\"rei\"}}",
         cast_mount("rei", "gurney"), cast_pose("rei", "lying"), "function angel:cast/gurney_crew",
         f"function angel:cast/gurney_move {{x:{num(gmark['x'])},y:{num(Y)},z:{num(gmark['z'])},speed:{num(g_speed, 4)}}}",
         sfx("sfx.gurney", at=(gx + 4.0, Y + 1.0, gz), vol=1.8, minvol=0.5),
         note=f"the gurney starts to roll with 5.28 (speed {g_speed}: it arrives as 5.30 ends)")
    s.after(0.4, fn("story/hq/side_open"), fn("story/hq/vest_on"), sfx("sfx.door_heavy", at=(gin["x"], Y + 2.0, gin["z"]), vol=2.5, minvol=0.6),
            note="the hospital door opens")
    s.after(0.9, *L.face(ctx, "misato", gin["x"], Y + 1.6, gin["z"]), *L.face(ctx, "ritsuko", gin["x"], Y + 1.6, gin["z"]),
            note="Misato and Ritsuko turn toward the door and the squeak of wheels")
    for k, at_ in enumerate((1.4, 3.6, 5.8)):
        s.after(at_, vblink, note="the lamps over the hospital door blink" if k == 0 else "")
    s.after(5.5, sfx("sfx.gurney", at=(gx + 0.55 * travel, Y + 1.0, gz), vol=2.2, minvol=0.6), note="the wheels again, from half way along the spur")
    s.say("5.28")
    s.say("5.29")
    s.say("5.30")
    s.until(Cond(["if score #arrived_gurney angel.cast matches 1"], 3.0, "the gurney is at the mark"), timeout=30, est=3.0,
            note="the gurney reaches hq.gurney_mark")
    s.sleep(PC.s5_rei_pause)
    s.do(sset("#present_rei", 1), sset("#f.rei_here", 1), note="Rei is here (tries to sit up)")
    s.say("5.31")
    s.sleep(PC.s5_rei_after)

    # ================================================================ the second impact (t = 0 here): the order of the shot, in ticks
    #   0  impact; every light out; dust, rings.                                          (the player is told it is dark by every sense)
    #  20  the lights stutter back on                      (lights_flicker hum)
    #  36  THE RIG TEARS LOOSE above the player (rig-tear sound from overhead, sparks and dust fall past his face, fragments, a swinging shadow on the deck);
    #      Misato, Ritsuko and the medics stare UP at it                                   (sway 36..80)
    #  40  the wash of the hand, hand_rise (a stereo wash: it swells for 2.6 s)
    #  64  THE HAND SURGES UP out of the coolant beside the bridge in 8 steps (to 92): spray on the west side, the palm sweeping in from the west overhead
    #  80  the rig lets go and falls onto the palm (the falling whistle), landing at 111: it breaks on the hand over his head, the far side rained on
    # 118  THE EYES LIGHT (sfx.eyes_on from 104): the glow falls across the bridge
    # 121  everyone turns and looks UP at the face
    # 128  the medics back away; 130 5.32 begins (BASE: "right arm in motion"); 134 the alarm
    # 150  only now: the aftershock; Rei is thrown from the gurney to the deck (landing 162)
    # after 5.35: the hand settles back down and the eyes go dark
    FACE_EYE = (XC, Y + 8.6, 58.2)                     # the giant's eyes (the slits are at y 61..64, z 57 behind the plate at z 59)
    RIG_UP = (XC, Y + 22.0, 77.5)                      # where the rig hangs, for everyone's eyes (they only look up as far as 30 degrees)
    TL = dict(place=10, back=20, tear=36, stare=40, wash=40, hand=64, eyes_snd=104, eyes=118, looks=121, medics=128, say=PC.s5_say_tick, alarm=134, throw=150)
    sec = lambda tk: tk / 20.0
    s.do(sfx("sfx.impact_above_hard", at=(XC, 100.0, 72.5), vol=5.0, pitch=0.8, minvol=1.0), sfx("sfx.dust_fall", vol=0.9), fn("story/hq/all_off"), fn("story/hq/dust_heavy"),
         fn("story/hq/rings"), *ctx.audio.start("music", "decision"), sfx("sfx.jolt", vol=2.0, pitch=0.8),
         note="HARDER: every light goes out for one second; dust; the coolant rings; the music of the decision (Rei is still on the gurney)")
    s.after(sec(TL["place"]), fn("story/hq/rig2_place"), note="in the dark: where the rig will hang (above the player, a little ahead, clamped over the hand)")
    s.after(sec(TL["back"]), cg.flicker("hit2_back", range(N_BANKS), [(0, "on"), (2, "off"), (4, "on"), (5, "off"), (7, "on")], extra_off=["booth", "vest"]),
            sfx("sfx.lights_flicker", vol=0.9), note="the lights stutter back")
    s.after(sec(TL["tear"]), fn("story/hq/rig2_start"),
            note="THE RIG TEARS LOOSE overhead: rig-tear sound from above, sparks and dust past his face, a swinging shadow; it hangs for two seconds")
    s.after(sec(TL["stare"]), *[c for who in ("misato", "ritsuko", "medic1", "medic2") for c in L.face(ctx, who, *RIG_UP)],
            note="everyone stares up at the rig")
    s.after(sec(TL["wash"]), sfx("sfx.hand_rise", at=(XC - 6.0, 46.0, 70.0), vol=4.0, minvol=1.0), f"particle minecraft:splash {num(XC - 12.5)} 37.6 82 5 0.3 8 0.3 120 force",
            note="the wash of the hand begins (a stereo wash: it swells for 2.6 s)")
    s.after(sec(TL["hand"]), fn("story/hq/hand_surge"), note="THE HAND SURGES UP out of the coolant beside the bridge (eight steps, 1.4 s), spray on its side, the palm sweeping in overhead")
    s.after(sec(TL["eyes_snd"]), sfx("sfx.eyes_on", at=(XC, 62.0, 58.0), vol=3.0, minvol=1.0), note="the power-up drone begins")
    s.after(sec(TL["eyes"]), fn("story/hq/eyes_on"), fn("story/hq/eyes_fx"), note="THE EYES LIGHT: their glow falls across the bridge (for as long as the hand is up)")
    s.after(sec(TL["looks"]), *[c for who in ("misato", "ritsuko", "medic1", "medic2") for c in L.face(ctx, who, *FACE_EYE)],
            note="everyone turns and looks UP at the face (past the player)")
    s.after(sec(TL["medics"]), walk("medic1", gmark["x"] + 1.8, Y, gmark["z"] + 5.5, speed=0.1), walk("medic2", gmark["x"] - 1.8, Y, gmark["z"] + 5.5, speed=0.1),
            note="the medics back away")
    s.after(sec(TL["alarm"]), *ctx.audio.start("loop", "klaxon"), sset("#f.alarm", 1), note="the alarm")
    # only now is Rei seen to have been thrown from the gurney: the aftershock, then an arc of 0.6 s, turning to lie along the bridge
    rei = "@e[type=minecraft:mannequin,tag=angel.rei,limit=1]"
    end = (REI_MID[0], Y + 0.125, REI_MID[2] - 0.9)                 # her foot end (yaw 180: feet to the north)
    steps = 7
    mid = (REI_MID[0], Y, REI_MID[2])
    t_th = sec(TL["throw"])
    s.after(t_th - 0.05, sfx("sfx.jolt", vol=2.4, pitch=0.9), fn("story/hq/shock_floor"), "function angel:cast/dismount {id:\"rei\"}",
            note="the aftershock: the bridge jolts, dust from the rails, the gurney's rider is let go")
    for i in range(1, steps + 1):
        u = i / float(steps)
        t_ = t_th + 0.04 + 0.085 * i
        if i < steps:
            x = SEAT[0] + (end[0] - SEAT[0]) * u
            z = SEAT[2] + (end[2] - SEAT[2]) * u
            y = SEAT[1] + (end[1] - SEAT[1]) * u + 1.5 * math.sin(math.pi * u)
            s.after(t_, f"tp {rei} {num(x)} {num(y)} {num(z)}", note="Rei is thrown from the gurney" if i == 1 else "")
        else:
            # she lands: up from the lying pose, put on the deck facing north, down again (the cast's own pose calls keep the body right)
            s.after(t_, cast_pose("rei", "standing"), f"tp {rei} {num(mid[0])} {num(mid[1])} {num(mid[2])} 180 0", cast_pose("rei", "lying"),
                    sfx("sfx.dust_fall", vol=0.8), note="Rei lands on the deck, lying along the bridge")
    s.sleep(sec(TL["say"]), note="the rig meets the hand at 111 and the eyes light at 118; 5.32 begins at 130")
    s.say("5.32")
    s.say("5.33")
    s.say("5.34")
    s.say("5.35")
    s.beat(53)
    # the hand goes back down, the eyes go dark
    s.do(fn("story/hq/hand_down"), fn("story/hq/eyes_off"), sfx("sfx.hand_rise", at=(XC - 4.0, 50.0, 76.0), vol=3.0, pitch=0.6, minvol=0.8),
         f"particle minecraft:splash {num(XC - 8)} 38 76 6 0.5 6 0.4 60 force", note="the hand sinks back; the eyes go dark")

    # ================================================================ the girl
    s.until(C.near(REI_MID[0], Y, REI_MID[2], 2.0, est=PC.s5_est_girl), timeout=120, est=PC.s5_est_girl, hint=("Go to the girl on the floor.", []), hint_after=25,
            objective=objective("Go to her", at=(REI_MID[0], Y + 0.5, REI_MID[2]), line="Walk to Rei, on the floor ahead  -  go right up to her", how="walk", grace=PC.s5_girl_grace),
            note="the player comes within 2 blocks of Rei")
    s.do(cast_pose("rei", "standing"), cast_pose("rei", "sitting"),
         f"execute at {P()} run particle minecraft:dust{{color:[0.62,0.04,0.04],scale:1.3}} ~ ~1.0 ~ 0.22 0.15 0.22 0 14 force",
         "execute at " + P() + " run playsound minecraft:item.armor.equip_leather master @a ~ ~ ~ 0.6 0.9 0.5",
         note="he lifts her: she sits up in his arms; his hand comes away red")
    s.sleep(PC.s5_girl_pause)
    s.say("5.36")
    s.say("5.37")
    s.say("5.38")
    s.do(sset("#consent", 0))
    wait_ticks = lambda lid, extra: T(ctx.lines[lid].seconds + 0.4 + extra)
    nud = Nudges(first=PC.s5_nudge_first, repeat=PC.s5_nudge_repeat, loop_from=1, lines=["5.39", "5.40", "5.41"], cmds=[
        [fn("say/5_39")],
        [fn("say/5_40"), cg.sched("impact_far", wait_ticks("5.40", 1.2))],
        [fn("say/5_41"), cg.sched("impact_far", wait_ticks("5.41", 1.4))]])
    s.wait_consent(speaker="rei", prompt="will you pilot it?  Say yes or no", loud=True, nudges=nud, no_skip=True, note="WAIT FOR YES (nudged: 5.39, 5.40, 5.41, then 5.40, 5.41 ...)")
    s.goto("yes")

    # ================================================================ the early yes: Rei is only a voice
    s.label("yes_early")
    s.do(sset("#present_rei", 2), note="(the early yes: Rei has not been brought in; her 'Why?' will be a voice behind them)")

    # ================================================================ Yes
    s.label("yes")
    s.beat(54)
    s.do(*ctx.audio.stop("music"), *ctx.audio.stop("loop"), *ctx.audio.stop("bed"), f"execute if score #f.alarm {OBJ} matches 1 run " + sfx("sfx.alarm_cut"),
         note="EVERYTHING STOPS: the music, the alarm cuts (if it was sounding)")
    s.sleep(PC.s5_yes_silence, note="silence")
    s.do(*ctx.audio.start("music", "resolve"), L.face_player("misato"), L.face_player("ritsuko"), note="music: the resolve, under 5.42 and 5.43 only")
    s.say("5.42")
    s.say("5.43", gap=0)
    s.music(None, note="the music is OUT here: nothing but the room from now until 5.44 has been said")
    s.hush("the hold on the father and 5.44")
    # Gendo has not moved: two seconds on him in silence, then the booth lights go out.  Only then does Ritsuko walk toward the door (her
    # footsteps would be the one sound in the hold); Misato stays by Rei (late path, no footsteps)
    s.do(f"execute if score #f.rei_here {OBJ} matches 1 run " + walk("misato", REI_MID[0] - 1.0, Y, REI_MID[2] - 0.2, speed=0.12),
         note="Misato stays by Rei")
    s.sleep(PC.s5_yes_hold, note="hold on Gendo: he has not moved, he says nothing; SILENCE")
    s.do(fn("story/hq/booth_off"), *L.walk_cmds("ritsuko", XC, Y, 125.0, SPEED), note="the booth lights go out (no sound); Ritsuko walks toward the door")
    # as the boy follows her, 5.44 from behind: still silence under it
    rx, rz = REI_MID[0], REI_MID[2]
    s.until(Cond([f"positioned {num(rx)} {num(Y)} {num(rz)} unless entity {P('distance=..6.5')}"], 6.0, "the boy is 6.5 blocks from Rei"),
            timeout=60, est=PC.s5_follow_est, hint=("Follow Ritsuko.", []), hint_after=20, note="he follows Ritsuko", objective=follow_objective("ritsuko"))
    s.say("5.44")
    s.unhush()
    # now the cage goes dark behind them, bank by bank, each with its breaker
    s.do(sfx("sfx.breaker_1", at=cg.bank_pos[N_BANKS - 1], vol=2.0, pitch=0.8, minvol=0.5), fn(f"story/hq/bank_off_{N_BANKS - 1}"), note="the cage goes dark behind them")
    for j, k in enumerate(range(N_BANKS - 2, 0, -1)):
        s.after(PC.s5_bank_off0 + PC.s5_bank_off_step * j, fn(f"story/hq/bank_off_{k}"), sfx(f"sfx.breaker_{k % 3 + 1}", at=cg.bank_pos[k], vol=1.5, pitch=0.85, minvol=0.4),
                note=f"bank {k} off")
    s.until(L.arrived("ritsuko", est=PC.s5_est_mid), timeout=60, est=PC.s5_est_mid, note="Ritsuko reaches the middle of the bridge", objective=follow_objective("ritsuko"), watch=False)
    s.until(L.near_char("ritsuko", 6.0), timeout=60, est=0.5, on_timeout=[tp_player(XC, Y, 119.5)], note="the boy is with her", objective=follow_objective("ritsuko"))
    s.do(*L.lead_off("ritsuko"), fn("story/hq/bank_off_0"), fn("story/hq/vest_off"), sfx("sfx.breaker_2", at=cg.bank_pos[0], vol=1.5, pitch=0.8, minvol=0.4), note="the last light")
    s.sleep(PC.s5_dark_pause, note="dark")
    s.do(*ctx.audio.stop("music"), *ctx.audio.stop("bed"))
    s.sleep(PC.s5_dark_pause2)

    # ================================================================ the card
    s.card("EVANGELION  UNIT 01", hold=PC.card_hold)
    s.sim_path("early_yes", take=["yes_early"], skip=("5.25", "5.41"))
    s.next_scene(6, jump=True)
