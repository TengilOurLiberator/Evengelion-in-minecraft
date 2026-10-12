"""Scene 7, The fight, and the ending.

The fight itself is angel:fight/* (tools/fight): it summons the monster, makes the boy the giant, says 7.01 to 7.20 when the things they
describe happen, and tells the story how it went by calling `angel:story/fight_done {result:"won"}` (when that function exists at the
time the fight is built).  This scene starts the fight, keeps the beat right, and plays the ending.

  hand-over order: scene 6 has made the boy the giant on the lift at city.launch_top, night, and has already put the monster standing at
  city.angel_start so that he sees it while 6.20 and 6.21 are said; scene 7 (`cont`) then runs `angel:fight/start` as the boy, which clears
  that monster and builds an identical one in the same tick (nobody sees the swap), bossbars, the barks 7.01 and 7.02.

  beats: 70 while fighting; 81 from the moment the defeat begins (the fight's phase 5: its 7.19, 7.20 and the fade) until the fight has
  restarted; then 70 again.  The fight restarts itself; the beat is the only thing this scene does about a defeat.

  music (cue-sheet rule: the fight is scored): the story polls the fight's phase scoreboard (#phase angel.fight: 0 intro, 1 the whole core, 2 cracked, 3 wrapped
  and counting down, 4 won, 5 lost) beside the beat, and keeps its own state #mus (0 none yet, 1 music.fight, 2 music.fight_final, 3 stopped):
    phase 1           music.fight begins (the intro, 7.01 and 7.02 and the first steps, is played without it)
    phase 2 or 3      music.fight_final takes over (the core has cracked: the last stretch)
    phase 4 (won)     the music stops dead (the cross of light, 7.15-7.18 and the dawn follow; music.victory comes with the dawn)
    phase 5 (lost)    the music stops and music.defeat plays (8 s) under 7.19, 7.20 and the fade
    phase 0 again     the fight has restarted after a loss: #mus is re-armed, and phase 1 starts music.fight again
  The fight (tools/fight) is not touched: this only reads its scoreboard.

  after a win: the fight has said 7.15-7.18 and put the boy back at human size on the lift; we hold on the empty avenue, bring up a dawn
  (the sky clock runs faster and faster for 15 s), music.victory, then the card TO BE CONTINUED / an unofficial fan work, then through black
  to the cage at human size: lights on, Misato, Ritsuko, Gendo (booth), Rei on the gurney; beat 80; the story is over and they can be
  talked to.

Entering this scene directly (`angel:story/scene {n:7}`): fade, the city at night, the boy the giant on the lift, then the fight starts.
"""
import launch_cage as cg
import launch_geo as geo
import launch_hooks
import worldgen_sky
from context import tp_player
from core import OBJ, P, PA, blind, fn, num, sset
from engine import C

N = 7
TITLE = "The fight"

# ---------------------------------------------------------------------------------------------------- the ending, in seconds
HOLD_BEFORE_DAWN = 2.0                  # on the empty avenue before the sky begins to change
# The sun rises in the EAST (the sun_angle track of angel:sky is the vanilla one: its path is the x-y plane, +x east, so its azimuth never changes;
# tick 0 of the day clock is the sun 12.4 degrees above the east horizon, tick 1000 27.5, tick 1600 34.8 -- computed from the track's cubic-bezier).
# The boy stands on the lift at the plaza's centre (city 1160.5, 160.5), and the plaza's main avenue runs due EAST from there for 130 blocks to the
# mountain wall at the edge of the city plate, whose ridge stands 27 degrees above his eyes (measured in the built set: skyline 26.5..27.6 degrees
# for +-10 degrees either side of east).  He is turned to the east in a short black before the dawn begins, so that the sun comes up over that ridge:
# it is hidden below it until day tick ~490, passes it between ticks 490 and 1600 (the disc, ~17 degrees across, is clear of it by tick ~1600) and
# stands ~35 degrees high at the end of the run.
DAWN_FACING = (-90.0, -8.0)             # yaw (east), pitch the boy is turned to during the black (checked in the game: at tick 500 the sun is hidden behind the
                                        # ridge, at 1000 it stands on it, at 1300 it is clear of it: a white disc over the mountain wall at the end of the avenue)
DAWN_BLACK = 1.2                        # seconds of black for the turn
# (seconds, clock rate): the clock runs from 18000 (midnight) through the twilight (22400..24000) to day tick 1600 (25600 in all):
DAWN = ((4.0, 30), (4.0, 30), (3.0, 14), (3.0, 14), (8.0, 7))          # 2400 + 2400 + 840 + 840 + 1120 = 7600 ticks in 22 s
DAWN_AFTER = 1.5                        # rate once the sun stands over the ridge
CARD_AT = 30.0                          # seconds after the dawn begins that the card cuts in (music.victory is 40 s and thinning by then)
CAGE_DARK = 4.5                         # seconds of black after the card for the move to the cage (the chunks must reach the headset)


def build(s, ctx):
    launch_hooks.register(ctx, geo)
    cg.register(ctx)
    audio = ctx.audio
    A = ctx.anchor
    top, angel_start, face = A("city.launch_top"), A("city.angel_start"), A("hq.face")
    ap = launch_hooks.players()

    # the fight calls this; "won" lets the story go on, "lost" only sets the beat (the fight restarts itself)
    s.function("done_won", ["execute if score #scene angel.story matches 7 run scoreboard players set #f.fight_won angel.story 1"])
    s.function("done_lost", ["execute if score #scene angel.story matches 7 run scoreboard players set #beat angel.story 81"])
    ctx.extra_functions["story/fight_done"] = ["$function angel:story/s7/f_done_$(result)"]

    # ================================================================ setup (for a direct entry; the hand-over from scene 6 skips it)
    s.do(blind(4.5), note="fade out")
    s.sleep(0.4)
    s.do(*ctx.preload(angel_start["x"], angel_start["z"]), fn("cast/remove_all"),
         "function angel:cast/gurney_remove", *audio.stop("bed"), sset("#ride", 0), note="preload the city")
    s.move_player(top["x"], top["y"], top["z"], yaw=180.0, pitch=0.0, settle=0.9, note="the player to the lift in the city")
    s.do(*worldgen_sky.sky("city"),
         f"execute as {P()} run function angel:fight/become_giant",
         sset("#present_misato", 2), sset("#present_ritsuko", 2), sset("#present_gendo", 2), sset("#present_rei", 0), sset("#beat", 70),
         f"gamemode adventure {PA()}", note="the boy is the giant on the lift at night")
    s.bed("city_night")
    s.sleep(1.4)
    s.setup_done()

    # ================================================================ the fight
    s.do(f"tag {P()} add angel.giant", sset("#mus", 0), f"execute as {P()} run function angel:fight/start",
         note="THE FIGHT: the monster is rebuilt in place, the giant's numbers set, 7.01 and 7.02 queued")
    audio_ = ctx.audio
    mus_fight = s.function("mus_fight", [sset("#mus", 1), *audio_.start("music", "fight")])
    mus_final = s.function("mus_final", [sset("#mus", 2), *audio_.start("music", "fight_final")])
    mus_stop = s.function("mus_stop", [sset("#mus", 3), *audio_.stop("music")])
    mus_defeat = s.function("mus_defeat", [sset("#mus", 3), *audio_.start("music", "defeat")])
    ph = "if score #phase angel.fight matches"
    mus = [f"execute {ph} 1 if score #mus {OBJ} matches 0 run {mus_fight}",
           f"execute {ph} 2..3 if score #mus {OBJ} matches 0..1 run {mus_final}",
           f"execute {ph} 4 if score #mus {OBJ} matches 0..2 run {mus_stop}",
           f"execute {ph} 5 if score #mus {OBJ} matches 0..2 run {mus_defeat}",
           f"execute {ph} 0 if score #mus {OBJ} matches 3 run scoreboard players set #mus {OBJ} 0"]
    to_81 = "execute if score #phase angel.fight matches 5 run scoreboard players set #beat angel.story 81"
    to_70 = ("execute if score #beat angel.story matches 81 if score #run angel.fight matches 1 if score #phase angel.fight matches 0..3 "
             "run scoreboard players set #beat angel.story 70")
    s.until(C.flag("fight_won", est=420.0), tick=[to_81, to_70, *mus], on_done=["function angel:fight/stop", *audio_.stop("music")],
            note="the fight (its own timeline); beat 81 during a defeat, 70 again when it restarts; music.fight / fight_final / defeat follow its phase; "
                 "ends when the fight calls fight_done won")

    # ================================================================ after the win: the dawn
    s.sleep(HOLD_BEFORE_DAWN, note="the empty avenue")
    # a short black: he is turned to the east, where the sun will rise over the mountain wall at the end of the avenue (see DAWN_FACING), and the
    # dawn starts under it; the head is turned only here, in the dark
    turn = f"execute as {P()} at @s run tp @s ~ ~ ~ {num(DAWN_FACING[0])} {num(DAWN_FACING[1])}"
    s.do(blind(DAWN_BLACK + 1.0), note="to black for the turn to the east")
    s.sleep(0.5, note="dark")
    s.do(turn, *cg.forceload_cage(), note="turned east (yaw -90): down the avenue to the mountain wall where the sun will come up")
    s.sleep(DAWN_BLACK - 0.5, note="the black lifts")
    s.do("time of angel:day resume", f"time of angel:day rate {num(DAWN[0][1])}", note="the dawn begins (the sky clock speeds up)")
    s.music("victory")
    t_ = 0.0
    for (sec, r), (_, r_next) in zip(DAWN, list(DAWN[1:]) + [(0, DAWN_AFTER)]):
        t_ += sec
        s.after(t_, f"time of angel:day rate {num(r_next)}", note=f"sky clock x{r_next}" + (" (the sun stands over the ridge)" if r_next == DAWN_AFTER else ""))
    s.sleep(CARD_AT, note="dawn over the empty avenue: the sun climbs over the ridge")

    # ================================================================ the card, and the cage
    s.music(None, note="silence for the card")
    s.bed(None)
    s.card("TO BE CONTINUED", small="an unofficial fan work")
    s.do(blind(CAGE_DARK + 1.0), note="black a little longer: the cage must arrive")
    s.do("time of angel:day rate 1.0", *worldgen_sky.sky("hq"), note="the clock stops its run; the cage's sky")
    # city -> hq is 2000 blocks: the guarded move (forceload the cage, dismount, teleport, wait until he is really there)
    s.move_player(face["x"], face["y"], face["z"], yaw=face["yaw"], pitch=face["pitch"], settle=1.2, before=cg.forceload_cage(),
                  note="the player to the cage (hq.face), turned to the giant's face (he was facing east in the city)")
    s.do(cg.lights_on(), fn("story/launch/eyes_off"), *cg.cast_for_ending(ctx),
         sset("#present_misato", 1), sset("#present_ritsuko", 1), sset("#present_gendo", 1), sset("#present_rei", 1), sset("#beat", 80),
         note="the cage at human size: lights on, eyes dark, Misato and Ritsuko on their marks, Gendo in the booth, Rei on the gurney; beat 80")
    s.bed("cage")
    s.sleep(CAGE_DARK, note="the black lifts")
    # the story is over: the boy is free in the cage at human size, everyone present; the bridge lets them talk

