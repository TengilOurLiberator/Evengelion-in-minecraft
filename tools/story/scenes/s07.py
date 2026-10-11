"""Scene 7, The fight, and the ending.

The fight itself is angel:fight/* (tools/fight): it summons the monster, makes the boy the giant, says 7.01 to 7.20 when the things they
describe happen, and tells the story how it went by calling `angel:story/fight_done {result:"won"}` (when that function exists at the
time the fight is built).  This scene starts the fight, keeps the beat right, and plays the ending.

  hand-over order: scene 6 has made the boy the giant on the lift at city.launch_top, night, and has already put the monster standing at
  city.angel_start so that he sees it while 6.20 and 6.21 are said; scene 7 (`cont`) then runs `angel:fight/start` as the boy, which clears
  that monster and builds an identical one in the same tick (nobody sees the swap), bossbars, the barks 7.01 and 7.02.

  beats: 70 while fighting; 81 from the moment the defeat begins (the fight's phase 5: its 7.19, 7.20 and the fade) until the fight has
  restarted; then 70 again.  The fight restarts itself; the beat is the only thing this scene does about a defeat.

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
from core import P, PA, blind, fn, num, sset
from engine import C

N = 7
TITLE = "The fight"

# ---------------------------------------------------------------------------------------------------- the ending, in seconds
HOLD_BEFORE_DAWN = 2.0                  # on the empty avenue before the sky begins to change
DAWN_STEP = 2.5                         # the sky clock changes speed every 2.5 s ...
DAWN_RATES = (6, 10, 15, 22, 30, 36)    # ... through these rates (x normal clock speed): 15 s from the middle of the night to the rim of the sun
DAWN_AFTER = 3                          # rate once the sun is up
CARD_AT = 27.0                          # seconds after the dawn begins that the card cuts in (music.victory is 40 s and thinning by then)
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
    s.do(blind(3.5), note="fade out")
    s.sleep(0.4)
    s.do(*ctx.preload(top["x"], top["z"]), *ctx.preload(angel_start["x"], angel_start["z"]), fn("cast/remove_all"),
         "function angel:cast/gurney_remove", *audio.stop("bed"), sset("#ride", 0), note="preload the city")
    s.sleep(0.9)
    s.do(*worldgen_sky.sky("city"), f"tp {P()} {num(top['x'])} {num(top['y'])} {num(top['z'])} 180 0",
         f"execute as {P()} run function angel:fight/become_giant",
         sset("#present_misato", 2), sset("#present_ritsuko", 2), sset("#present_gendo", 2), sset("#present_rei", 0), sset("#beat", 70),
         f"gamemode adventure {PA()}", note="the boy is the giant on the lift at night")
    s.bed("city_night")
    s.sleep(1.4)
    s.setup_done()

    # ================================================================ the fight
    s.do(f"tag {P()} add angel.giant", f"execute as {P()} run function angel:fight/start",
         note="THE FIGHT: the monster is rebuilt in place, the giant's numbers set, 7.01 and 7.02 queued")
    to_81 = "execute if score #phase angel.fight matches 5 run scoreboard players set #beat angel.story 81"
    to_70 = ("execute if score #beat angel.story matches 81 if score #run angel.fight matches 1 if score #phase angel.fight matches 0..3 "
             "run scoreboard players set #beat angel.story 70")
    s.until(C.flag("fight_won", est=420.0), tick=[to_81, to_70], on_done=["function angel:fight/stop"],
            note="the fight (its own timeline); beat 81 during a defeat, 70 again when it restarts; ends when the fight calls fight_done won")

    # ================================================================ after the win: the dawn
    s.sleep(HOLD_BEFORE_DAWN, note="the empty avenue")
    s.do(*cg.forceload_cage(), "time of angel:day resume", f"time of angel:day rate {DAWN_RATES[0]}.0",
         note="the dawn begins (the sky clock speeds up)")
    s.music("victory")
    for k, r in enumerate(DAWN_RATES[1:], 1):
        s.after(DAWN_STEP * k, f"time of angel:day rate {r}.0", note=f"sky clock x{r}")
    s.after(DAWN_STEP * len(DAWN_RATES), f"time of angel:day rate {DAWN_AFTER}.0", note="the sun is up")
    s.sleep(CARD_AT, note="dawn over the empty avenue")

    # ================================================================ the card, and the cage
    s.music(None, note="silence for the card")
    s.bed(None)
    s.card("TO BE CONTINUED", small="an unofficial fan work")
    s.do(blind(CAGE_DARK), note="black a little longer: the cage must arrive")
    s.do("time of angel:day rate 1.0", *worldgen_sky.sky("hq"),
         tp_player(face["x"], face["y"], face["z"]),
         cg.lights_on(), fn("story/launch/eyes_off"), *cg.cast_for_ending(ctx),
         sset("#present_misato", 1), sset("#present_ritsuko", 1), sset("#present_gendo", 1), sset("#present_rei", 1), sset("#beat", 80),
         note="the cage at human size: lights on, eyes dark, Misato and Ritsuko on their marks, Gendo in the booth, Rei on the gurney; beat 80")
    s.bed("cage")
    s.sleep(CAGE_DARK, note="the black lifts")
    # the story is over: the boy is free in the cage at human size, everyone present; the bridge lets them talk
