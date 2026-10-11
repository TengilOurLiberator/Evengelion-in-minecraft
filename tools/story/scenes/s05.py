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
from context import cast_look, cast_mount, cast_pose, cast_remove, cast_summon, tp_player
from core import OBJ, P, PA, T, blind, dir_to_yaw, fn, num, sset
from engine import C, Cond, Nudges
from hq_cage import N_BANKS, cage, dirty_cmd
import worldgen_sky

N = 5
TITLE = "The cage"

SPEED = 0.15


def walk(who, x, y, z, speed=0.13):
    return f'function angel:cast/walk {{id:"{who}",x:{num(x)},y:{num(y)},z:{num(z)},speed:{num(speed)}}}'


def build(s, ctx):
    A = ctx.anchor
    cdoor, bstart, face = A("hq.cage_door"), A("hq.bridge_start"), A("hq.face")
    cap, sci, gin, gmark = A("hq.captain_mark"), A("hq.scientist_mark"), A("hq.gurney_in"), A("hq.gurney_mark")
    shield, d2, booth = A("hq.shield"), A("hq.debris_2"), A("hq.booth")
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
    BOOTH_EYE = (booth["x"], booth["y"] + EYE, booth["z"])
    HE_STOPS = (face["x"], face["y"] + EYE, face["z"])  # the boy's eyes at the stop, which Gendo looks at
    GURNEY_START = (gin["x"] - 5.0, Y, gin["z"])       # inside the hospital vestibule, behind the door at x = gin.x
    SEAT = (gmark["x"] + 0.9, Y + 0.945, gmark["z"])   # where Rei's foot end is on the gurney at the mark

    def eyes_of(p):
        return (p[0], p[1] + EYE, p[2])

    # ================================================================ setup (a jump runs it; a hand-over from scene 4 skips it)
    s.do(blind(3.5), note="fade out")
    s.sleep(0.4)
    s.do(*ctx.preload_rect(3040, 16, 3135, 176), note="preload the whole cage and the lake hall")
    s.sleep(1.4, note="the chunks load")
    s.do(fn("story/hq/reset_cage"), fn("story/hq/reset_lobby"), dirty_cmd(), fn("story/hq/door_opened"), fn("story/hq/side_closed"),
         note="the set as scene 4 leaves it: cage dark, the cage door open, the hospital door closed, hand lowered, eyes dark")
    s.do(tp_player(cdoor["x"], cdoor["y"], cdoor["z"]), *worldgen_sky.sky("hq"), note="the player to hq.cage_door (the head is not turned)")
    s.do(sset("#beat", 41), sset("#present_misato", 1), sset("#present_ritsuko", 1), sset("#present_gendo", 0), sset("#present_rei", 0),
         cast_summon("ritsuko", XC, Y, cdoor["z"] - 1.8, 180.0), cast_summon("misato", XC - 1.1, Y, cdoor["z"] + 1.8, 180.0),
         note="Ritsuko in front of the door, Misato beside the boy")
    s.do(*ctx.audio.start("bed", "lake"), note="the lake hall's air")
    s.sleep(1.5)
    s.setup_done()

    # ================================================================ dark: onto the bridge behind Ritsuko
    s.do(dirty_cmd(), fn("story/hq/side_closed"), sset("#consent", 0), sset("#f.hold", 0), sset("#f.rei_here", 0))
    L.lead(s, ctx, "ritsuko", [
        L.Stop(XC, Y, 139.0, wait=False, note="through the cage door"),
        L.Stop(bstart["x"], Y, bstart["z"], wait=False, note="hq.bridge_start"),
        L.Stop(XC, Y, 128.0, note="out on the bridge"),
    ], speed=SPEED, companion=("misato", 3.2, 1.2), start=(XC, cdoor["z"] - 1.8))
    # the door shuts behind them with a boom; then silence
    s.do(fn("story/hq/door_close"), sfx("sfx.door_heavy", at=(XC, Y + 3.0, 140.5), vol=3.0, minvol=0.8), *ctx.audio.stop("bed"),
         note="the cage door shuts behind them")
    s.after(0.4, sfx("sfx.door_boom", at=(XC, Y + 3.0, 140.5), vol=4.0, pitch=0.8, minvol=0.9), note="the boom")
    s.sleep(1.5)
    # they go to their marks in the dark; the boy walks to the end of the bridge
    s.do(walk("misato", *MIS_MARK, speed=0.13), note="Misato to captain_mark")
    L.lead(s, ctx, "ritsuko", [
        L.Stop(XC, Y, 100.0, note="the middle of the bridge"),
        L.Stop(*RIT_MARK, note="Ritsuko to scientist_mark"),
    ], speed=SPEED, start=(XC, 128.0))
    s.do(sset("#f.hold", 0), note="count how long he stands near the end")
    fx, fy, fz = face["x"], face["y"], face["z"]
    s.until([C.near(fx, fy, fz, 1.5, est=10), C.score("#f.hold", "60..", est=10)], timeout=150, est=10.0,
            tick=[f"execute positioned {num(fx)} {num(fy)} {num(fz)} if entity {P('distance=..4')} run scoreboard players add #f.hold angel.story 1",
                  f"execute positioned {num(fx)} {num(fy)} {num(fz)} unless entity {P('distance=..4')} run scoreboard players set #f.hold angel.story 0"],
            hint=("Walk to the end of the bridge.", []), hint_after=40,
            on_timeout=[tp_player(fx, fy, fz)], note="the player reaches hq.face (or stops within 4 blocks of it for 3 s)")
    s.sleep(0.5)
    s.say("5.01")
    s.sleep(3.0, note="three seconds of nothing")

    # ================================================================ lights: eight banks, farthest first, the face last
    s.beat(50)
    for k in range(N_BANKS):
        cmds = [fn(f"story/hq/bank_on_{k}"),
                sfx(f"sfx.breaker_{k % 3 + 1}", at=cg.bank_pos[k], vol=3.0, pitch=0.9 if k == N_BANKS - 1 else 1.0, minvol=0.7)]
        if k == 0:
            cmds += ctx.audio.start("bed", "cage") + ctx.audio.start("music", "cage")
        s.do(*cmds, note=f"bank {k} on ({cg.banks[k]['on'].__len__()} lights)" + (" -- the face" if k == N_BANKS - 1 else ""))
        s.sleep(0.5)
    s.sleep(2.5, note="let it stand: three seconds in all before anyone speaks")
    s.say("5.02")
    s.say("5.03")
    s.wait_answer(speaker="ritsuko", prompt="answer Ritsuko")

    # ================================================================ the father
    flick_booth = cg.flicker("booth", [], [(0, "on"), (3, "off"), (5, "on"), (9, "off"), (11, "on")], extra_off=["booth"])
    gyaw = dir_to_yaw(HE_STOPS[0] - booth["x"], HE_STOPS[2] - booth["z"])
    s.do(cast_summon("gendo", booth["x"], booth["y"], booth["z"], gyaw), *L.face(ctx, "gendo", *HE_STOPS, ticks=8),
         sset("#present_gendo", 1), flick_booth, sfx("sfx.booth_light", at=(booth["x"], booth["y"] + 4, booth["z"] - 1), vol=2.5, minvol=0.7),
         note="the booth lights come on: Gendo stands in the glass, looking down")
    s.sleep(2.0, note="a beat")
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
    s.sleep(0.8, note="a held breath")
    fl1 = cg.flicker("hit1", [1, 3, 5], [(0, "off"), (3, "on"), (6, "off"), (8, "on"), (13, "off"), (15, "on")])
    s.do(fn("story/hq/impact1"), fl1, note="a deep blow from above: a third of the banks flicker, dust in the beams, the coolant rings")
    s.sleep(1.5)
    s.say("5.21")
    s.say("5.22")
    s.say("5.23")
    s.do(L.face_player("misato"), note="Misato turns to the boy")
    s.say("5.24")
    # a consent-capable wait: the bridge classifies the answer; a yes goes straight to the yes, any other answer is voiced by the character
    # and the wait ends without consent (answer_ends); 45 s of silence also go on
    s.do(sset("#consent", 0))
    s.wait_consent(speaker="misato", prompt="answer Misato", answer_ends=True, timeout=45, est=6.0, note="WAIT (a yes here goes straight to the yes)")
    s.branch(C.score("#consent", "1"), "yes_early")
    s.sleep(0.6)

    # ================================================================ Rei
    s.say("5.25")
    s.say("5.26")
    s.say("5.27")
    s.do(sset("#present_rei", 2), note="Rei on the intercom")
    s.say("5.28")
    # the hospital door opens as 5.29 begins; the gurney rolls out of the vestibule to the mark with the medics either side
    gx, gy, gz = GURNEY_START
    s.do(f"execute positioned {num(gx)} {num(gy)} {num(gz)} rotated -90 0 run function angel:cast/gurney",
         f"execute positioned {num(gx)} {num(gy)} {num(gz)} rotated -90 0 run function angel:cast/summon {{id:\"rei\"}}",
         cast_mount("rei", "gurney"), cast_pose("rei", "lying"), "function angel:cast/gurney_crew",
         f"function angel:cast/gurney_move {{x:{num(gmark['x'])},y:{num(Y)},z:{num(gmark['z'])},speed:0.15}}",
         sfx("sfx.gurney", at=(gx + 4.0, Y + 1.0, gz), vol=1.5, minvol=0.5), note="the gurney starts to roll")
    s.after(0.4, fn("story/hq/side_open"), fn("story/hq/vest_on"), sfx("sfx.door_heavy", at=(gin["x"], Y + 2.0, gin["z"]), vol=2.5, minvol=0.6),
            note="the hospital door opens")
    s.say("5.29")
    s.say("5.30")
    s.until(Cond(["if score #arrived_gurney angel.cast matches 1"], 3.0, "the gurney is at the mark"), timeout=30, est=3.0,
            note="the gurney reaches hq.gurney_mark")
    s.sleep(0.5)
    s.do(sset("#present_rei", 1), sset("#f.rei_here", 1), note="Rei is here (tries to sit up)")
    s.say("5.31")
    s.sleep(0.8)

    # ================================================================ the second impact (t = 0 here)
    s.do(sfx("sfx.impact_above_hard", at=(XC, 100.0, 72.5), vol=5.0, pitch=0.8, minvol=1.0), sfx("sfx.dust_fall", vol=0.9), fn("story/hq/all_off"), fn("story/hq/dust_heavy"),
         fn("story/hq/rings"), *ctx.audio.start("music", "decision"), "function angel:cast/dismount {id:\"rei\"}",
         note="HARDER: every light goes out; dust; the coolant rings; the music of the decision")
    # Rei is thrown from the gurney onto the deck: an arc over 0.6 s, turning to lie along the bridge
    rei = "@e[type=minecraft:mannequin,tag=angel.rei,limit=1]"
    end = (REI_MID[0], Y + 0.125, REI_MID[2] - 0.9)                 # her foot end (yaw 180: feet to the north)
    steps = 7
    mid = (REI_MID[0], Y, REI_MID[2])
    for i in range(1, steps + 1):
        u = i / float(steps)
        t_ = 0.04 + 0.085 * i
        if i < steps:
            x = SEAT[0] + (end[0] - SEAT[0]) * u
            z = SEAT[2] + (end[2] - SEAT[2]) * u
            y = SEAT[1] + (end[1] - SEAT[1]) * u + 1.5 * math.sin(math.pi * u)
            s.after(t_, f"tp {rei} {num(x)} {num(y)} {num(z)}", note="Rei is thrown from the gurney" if i == 1 else "")
        else:
            # she lands: up from the lying pose, put on the deck facing north, down again (the cast's own pose calls keep the body right)
            s.after(t_, cast_pose("rei", "standing"), f"tp {rei} {num(mid[0])} {num(mid[1])} {num(mid[2])} 180 0", cast_pose("rei", "lying"),
                    note="Rei lands on the deck, lying along the bridge")
    s.after(0.10, fn("story/hq/rig_fall"), sfx("sfx.rig_tear", at=(XC, 104.0, d2["z"]), vol=4.0, minvol=0.9), note="the lighting rig tears loose at debris_2 and falls")
    s.after(0.62, fn("story/hq/hand_up"), fn("story/hq/eyes_on"), sfx("sfx.hand_rise", at=(XC - 4.0, 50.0, 76.0), vol=4.0, minvol=0.9),
            sfx("sfx.eyes_on", at=(XC, 62.0, 58.0), vol=3.0, minvol=0.9),
            f"particle minecraft:splash {num(XC - 8)} 38 {num(76)} 6 0.5 6 0.4 80 force",
            f"particle minecraft:dust{{color:[1.0,0.55,0.2],scale:2.0}} {num(XC - 8)} 39 {num(76)} 5 1 5 0 40 force",
            note="THE HAND comes up out of the coolant (cell by cell); the eyes light, for the first time, for as long as the hand is up")
    back = cg.flicker("hit2_back", range(N_BANKS), [(0, "on"), (2, "off"), (4, "on"), (5, "off"), (7, "on")], extra_off=["booth", "vest"])
    s.after(1.3, back, sfx("sfx.lights_flicker", vol=0.9), note="the lights come back, stuttering")
    s.after(1.55, walk("medic1", gmark["x"] + 1.8, Y, gmark["z"] + 5.5, speed=0.1), walk("medic2", gmark["x"] - 1.8, Y, gmark["z"] + 5.5, speed=0.1),
            note="the medics back away")
    s.after(2.0, *L.face(ctx, "ritsuko", XC, Y + 6.0, 80.0), *L.face(ctx, "misato", XC, Y + 6.0, 80.0), note="everyone looks up at the hand")
    s.after(3.3, *ctx.audio.start("loop", "klaxon"), sset("#f.alarm", 1), note="the alarm")
    s.sleep(4.6, note="the rig meets the hand at about 2.9 s; the pieces fall; the room settles")
    s.say("5.32")
    s.say("5.33")
    s.say("5.34")
    s.say("5.35")
    s.beat(53)
    # the hand goes back down, the eyes go dark
    s.do(fn("story/hq/hand_down"), fn("story/hq/eyes_off"), sfx("sfx.hand_rise", at=(XC - 4.0, 50.0, 76.0), vol=3.0, pitch=0.6, minvol=0.8),
         f"particle minecraft:splash {num(XC - 8)} 38 76 6 0.5 6 0.4 60 force", note="the hand sinks back; the eyes go dark")

    # ================================================================ the girl
    s.until(C.near(REI_MID[0], Y, REI_MID[2], 2.0, est=8), timeout=120, est=8.0, hint=("Go to the girl on the floor.", []), hint_after=25,
            note="the player comes within 2 blocks of Rei")
    s.do(cast_pose("rei", "standing"), cast_pose("rei", "sitting"),
         f"execute at {P()} run particle minecraft:dust{{color:[0.62,0.04,0.04],scale:1.3}} ~ ~1.0 ~ 0.22 0.15 0.22 0 14 force",
         "execute at " + P() + " run playsound minecraft:item.armor.equip_leather master @a ~ ~ ~ 0.6 0.9 0.5",
         note="he lifts her: she sits up in his arms; his hand comes away red")
    s.sleep(0.6)
    s.say("5.36")
    s.say("5.37")
    s.say("5.38")
    s.do(sset("#consent", 0))
    wait_ticks = lambda lid, extra: T(ctx.lines[lid].seconds + 0.4 + extra)
    nud = Nudges(first=9.0, repeat=11.0, loop_from=1, lines=["5.39", "5.40", "5.41"], cmds=[
        [fn("say/5_39")],
        [fn("say/5_40"), cg.sched("impact_far", wait_ticks("5.40", 1.2))],
        [fn("say/5_41"), cg.sched("impact_far", wait_ticks("5.41", 1.4))]])
    s.wait_consent(speaker="rei", prompt="will you pilot it?", nudges=nud, note="WAIT FOR YES (nudged: 5.39, 5.40, 5.41, then 5.40, 5.41 ...)")
    s.goto("yes")

    # ================================================================ the early yes: Rei is only a voice
    s.label("yes_early")
    s.do(sset("#present_rei", 2), note="(the early yes: Rei has not been brought in; her 'Why?' will be a voice behind them)")

    # ================================================================ Yes
    s.label("yes")
    s.beat(54)
    s.do(*ctx.audio.stop("music"), *ctx.audio.stop("loop"), *ctx.audio.stop("bed"), f"execute if score #f.alarm {OBJ} matches 1 run " + sfx("sfx.alarm_cut"),
         note="EVERYTHING STOPS: the music, the alarm cuts (if it was sounding)")
    s.sleep(1.4, note="silence")
    s.do(*ctx.audio.start("music", "resolve"), L.face_player("misato"), L.face_player("ritsuko"), note="music: the resolve")
    s.say("5.42")
    s.say("5.43")
    # Ritsuko walks toward the door; Misato stays by Rei (late path); Gendo has not moved: two seconds on him, then the booth lights go out
    s.do(*L.walk_cmds("ritsuko", XC, Y, 125.0, SPEED),
         f"execute if score #f.rei_here {OBJ} matches 1 run " + walk("misato", REI_MID[0] - 1.0, Y, REI_MID[2] - 0.2, speed=0.12),
         note="Ritsuko walks toward the door; Misato stays by Rei")
    s.sleep(2.0, note="hold on Gendo: he has not moved, he says nothing")
    s.do(fn("story/hq/booth_off"), sfx("sfx.booth_light", at=(booth["x"], booth["y"] + 4, booth["z"] - 1), vol=2.0, pitch=0.7, minvol=0.7),
         note="the booth lights go out")
    # as the boy follows her, 5.44 from behind
    rx, rz = REI_MID[0], REI_MID[2]
    s.until(Cond([f"positioned {num(rx)} {num(Y)} {num(rz)} unless entity {P('distance=..6.5')}"], 6.0, "the boy is 6.5 blocks from Rei"),
            timeout=60, est=6.0, hint=("Follow Ritsuko.", []), hint_after=20, note="he follows Ritsuko")
    s.do(sfx("sfx.breaker_1", at=cg.bank_pos[N_BANKS - 1], vol=2.0, pitch=0.8, minvol=0.5), fn(f"story/hq/bank_off_{N_BANKS - 1}"), note="the cage goes dark behind them")
    for j, k in enumerate(range(N_BANKS - 2, 0, -1)):
        s.after(1.0 + 1.1 * j, fn(f"story/hq/bank_off_{k}"), sfx(f"sfx.breaker_{k % 3 + 1}", at=cg.bank_pos[k], vol=1.5, pitch=0.85, minvol=0.4),
                note=f"bank {k} off")
    s.say("5.44")
    s.until(L.arrived("ritsuko", est=10), timeout=60, est=10.0, note="Ritsuko reaches the middle of the bridge")
    s.until(L.near_char("ritsuko", 6.0), timeout=60, est=0.5, on_timeout=[tp_player(XC, Y, 119.5)], note="the boy is with her")
    s.do(*L.lead_off("ritsuko"), fn("story/hq/bank_off_0"), fn("story/hq/vest_off"), sfx("sfx.breaker_2", at=cg.bank_pos[0], vol=1.5, pitch=0.8, minvol=0.4), note="the last light")
    s.sleep(1.6, note="dark")
    s.do(*ctx.audio.stop("music"), *ctx.audio.stop("bed"))
    s.sleep(0.4)

    # ================================================================ the card
    s.card("EVANGELION  UNIT 01")
    s.sim_path("early_yes", take=["yes_early"], skip=("5.25", "5.41"))
    s.next_scene(6, jump=True)
