"""Estimates how long the boss fight takes for two kinds of attacker, from the numbers in gen_fight's preset (CFG).

    python estimate.py                   # the default preset (video: ANGEL_PACE, else video)
    python estimate.py --pace full       # the earlier numbers
    python estimate.py --pace video

Not a simulation of the server: an accounting of the phases, with the assumptions written out below.  Change the preset table in gen_fight.py, run this, and
adjust until the first-time player (b) comes out where the preset is meant to (video: 2:00 to 2:30 with the scripted attacker (a) at 75 to 90 s; full: 4 to 7 min).
The assumptions are guesses about people; only a human at the controls can check them.

Assumptions (the player models are in PLAYERS, one set per preset):
  * (a) the scripted attacker of the live tests: one click every 0.95 s, never dodges, runs at 13 blocks/s, so the only thing it ever waits for is the barrier of
    a back-off.  With a core guard (hit_cd > 0) every other click is swallowed (one landed hit per 1.9 s); WITHOUT it every click that connects lands (0.95 s).
  * (b) a first-time player.  WITH the guard: a landed hit every 2.0 s.  WITHOUT it nothing swallows a swing any more, so the pace is limited by aim and the
    swing itself: one landed hit every 1.3 s (a plausible 1.2 to 1.5 s: a roomscale swing at a 6-block target that is 9 to 12 blocks away, a re-aim between swings).
    He loses 2.5 s to each arm thrust (steps out of the 9-block zone and back), needs 24 s from the start to the first hit (about 85 blocks at 6 blocks/s, the
    first beam's cover; 22 s in video, where the Angel sets off 4 s after his first steps instead of 6), 4 s of cover from the beam after each retreat and the walk back after it (the retreat distance at 6 blocks/s plus 3 s of reaction), and
    lands a hit every 1.5 s in the wrap (5.5 s to spare on its bar).
  * "slow" and "quick" first-timers scale those numbers (slow 1.3x on the swing, 3 s per thrust; quick 0.8x, 2 s per thrust).
  * Not modelled: the player dying (giant health 100: four thrusts or four beams, regenerating 2 per second after 8 s unhurt) and restarting; a player who
    rushes back and gets the first beam at close range (the barrier then waits for it exactly as much).
"""
import argparse
import math
import sys

import gen_fight
from gen_fight import CFG

TICK = 0.05
CLICK = 0.95            # the scripted attacker's click interval, seconds

# player models, per preset: keys of the first-timer; `swing` is the seconds per landed hit while free to hit
PLAYERS = {
    "full": dict(
        b=dict(hit_every=2.0, dodge=2.5, open_s=24, wrap_every=1.5, walk_bps=6.0, react=3.0, cover_s=4),
        slow=dict(hit_every=2.6, dodge=3.0, open_s=30, wrap_every=1.8, walk_bps=5.0, react=4.0, cover_s=5),
        quick=dict(hit_every=1.5, dodge=2.0, open_s=18, wrap_every=1.3, walk_bps=7.5, react=2.0, cover_s=3)),
    "video": dict(
        b=dict(hit_every=1.3, dodge=2.5, open_s=22, wrap_every=1.5, walk_bps=6.0, react=3.0, cover_s=4),
        slow=dict(hit_every=1.7, dodge=3.0, open_s=28, wrap_every=1.8, walk_bps=5.0, react=4.0, cover_s=5),
        quick=dict(hit_every=1.0, dodge=2.0, open_s=16, wrap_every=1.3, walk_bps=7.5, react=2.0, cover_s=3)),
}


def backoff_ticks():
    """(stagger, retreat walk, wait for the first attack = the barrier's gate) in ticks."""
    stag = CFG["backoff_stagger"]
    walk = math.ceil(CFG["backoff_dist"] / CFG["backoff_speed"]) + 8       # + the first stride
    gate = stag + walk + CFG["backoff_cd"] + CFG["beam_charge"] + CFG["beam_recover"]       # barrier down when the first beam is over
    return stag, walk, gate


def wrap_margin(every):
    """Seconds left on the self-destruct bar when the last hit lands, for a hitter with `every` seconds between hits (the first hit after `every` too): the bar
    starts full (wrap_ticks), loses `every` s per hit and regains wrap_bonus after each hit (the bar never goes above its start).  Negative = lost."""
    bar = CFG["wrap_ticks"] * TICK
    bonus = CFG["wrap_bonus"] * TICK
    for i in range(CFG["wrap_at"]):
        bar -= every
        if bar <= 0:
            return bar
        if i < CFG["wrap_at"] - 1:
            bar = min(CFG["wrap_ticks"] * TICK, bar + bonus)
    return bar


def estimate(name, *, hit_every, dodge, open_s, wrap_every, approach_s, cover_s, player=True, quiet=False):
    """hit_every   seconds per LANDED hit while it is free to hit (with a guard 1.2 s is the floor)
    dodge       seconds lost per arm thrust (stepping out of the 9-block zone and back), 0 = never dodges
    open_s      from the start to the first hit (walking up the avenue, the first beam included)
    wrap_every  seconds per landed hit in the final wrap (no guard there: every swing that connects counts; the monster is wrapped round the giant,
                a 14 x 30 block target)
    approach_s  seconds to close the retreat distance after a back-off, cover_s extra seconds for taking cover from the beam
    """
    stag, walk, gate = backoff_ticks()
    hits_before_wrap = CFG["core_hp"] - CFG["wrap_at"]
    n_backoff = (hits_before_wrap - 1) // CFG["backoff_hits"]
    # arm thrust cycle (windup + recover + cooldown), phase A until the crack, phase B after
    cyc_a = (CFG["thrust_windup"] + CFG["thrust_recover"] + CFG["cd_thrust"]) * TICK
    cyc_b = (CFG["thrust_windup"] + CFG["thrust_recover"] + CFG["cd_thrust_b"]) * TICK
    n_a = CFG["core_hp"] - CFG["crack_at"]
    n_b = hits_before_wrap - n_a
    free_a = max(0.2, (cyc_a - dodge) / cyc_a)
    free_b = max(0.2, (cyc_b - dodge) / cyc_b)
    engaged = n_a * hit_every / free_a + n_b * hit_every / free_b
    if not player:                      # barrier-gated: the attacker waits for the barrier, which drops after the first beam
        per_backoff = gate * TICK
    else:                               # the player: retreat, then the approach and the cover, if that is longer than the gate
        per_backoff = max(gate * TICK, (stag + walk) * TICK + approach_s + cover_s)
    wrap = CFG["wrap_at"] * wrap_every
    total = open_s + engaged + n_backoff * per_backoff + 1.5 + wrap
    margin = wrap_margin(wrap_every)
    if not quiet:
        print(f"{name}: {total:5.0f} s = {int(total // 60)}:{int(round(total % 60)):02d}   (opening {open_s:.0f} s, {hits_before_wrap} hits in {engaged:.0f} s, "
              f"{n_backoff} back-offs x {per_backoff:.1f} s = {n_backoff * per_backoff:.0f} s, wrap {wrap:.0f} s, margin in the countdown {margin:.1f} s)")
    return total


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--pace", choices=sorted(gen_fight.PRESETS), help="the preset (default: ANGEL_PACE, else video)")
    a = ap.parse_args(argv)
    if a.pace:
        gen_fight.set_pace(a.pace)
    pace = gen_fight.PACE
    pl = PLAYERS[pace]
    print(f"pace: {pace}   core hits to win {CFG['core_hp']} (cracks at {CFG['crack_at']} left, wraps at {CFG['wrap_at']}), back-off every {CFG['backoff_hits']} landed hits, "
          f"retreat {CFG['backoff_dist']} blocks, core guard {CFG['hit_cd'] * TICK:.1f} s" if CFG["hit_cd"] else
          f"pace: {pace}   core hits to win {CFG['core_hp']} (cracks at {CFG['crack_at']} left, wraps at {CFG['wrap_at']}), back-off every {CFG['backoff_hits']} landed hits, "
          f"retreat {CFG['backoff_dist']} blocks, no core guard")
    stag, walk, gate = backoff_ticks()
    print(f"back-off: stagger {stag} + retreat {walk} ticks, barrier up {gate} ticks = {gate * TICK:.1f} s until the first attack is over")
    print(f"wrap: {CFG['wrap_at']} hits in {CFG['wrap_ticks'] * TICK:.0f} s + {CFG['wrap_bonus'] * TICK:.1f} s per hit, no guard: spare time at the last hit "
          f"{wrap_margin(1.5):.1f} s for a hit every 1.5 s, {wrap_margin(1.0):.1f} s at 1.0 s, {wrap_margin(0.95):.1f} s at 0.95 s (the scripted clicker), "
          f"{wrap_margin(2.0):.1f} s at 2.0 s; a 1.5 s hitter who also stops for 6 s in all: {wrap_margin(1.5) - 6:.1f} s (lost)")
    guard = CFG["hit_cd"] * TICK
    scripted_every = math.ceil(guard / CLICK) * CLICK if guard else CLICK          # with a guard a click every 0.95 s loses every other one
    # (a) the scripted attacker: one click per 0.95 s, never dodges, runs at 13 blocks/s, so the barrier's gate is all it waits for
    res = {}
    res["a"] = estimate("(a) scripted, never dodges", hit_every=scripted_every, dodge=0.0, open_s=9, wrap_every=CLICK, approach_s=0, cover_s=0, player=False)
    for key, label in (("b", "(b) first-time player"),
                       ("slow", "    slow player (%.1f s per hit, %.0f s per thrust)"),
                       ("quick", "    quick player (%.1f s per hit, %.0f s per thrust)")):
        p = pl[key]
        approach = CFG["backoff_dist"] / p["walk_bps"] + p["react"]
        name = label if key == "b" else label % (p["hit_every"], p["dodge"])
        res[key] = estimate(name, hit_every=p["hit_every"], dodge=p["dodge"], open_s=p["open_s"], wrap_every=p["wrap_every"], approach_s=approach, cover_s=p["cover_s"])
    return res


if __name__ == "__main__":
    main()
