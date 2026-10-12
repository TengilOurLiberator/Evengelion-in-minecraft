"""Estimates how long the boss fight takes for two kinds of attacker, from the numbers in gen_fight.CFG.

    python estimate.py

Not a simulation of the server: an accounting of the phases, with the assumptions written out below.  Change CFG in gen_fight.py,
run this, and adjust until the first-time player (b) comes out between 4 and 7 minutes.  The assumptions are guesses about people;
only a human at the controls can check them.
"""
import math

from gen_fight import CFG

TICK = 0.05


def backoff_ticks():
    """(stagger, retreat walk, wait for the first attack = the barrier's gate) in ticks."""
    stag = CFG["backoff_stagger"]
    walk = math.ceil(CFG["backoff_dist"] / CFG["backoff_speed"]) + 8       # + the first stride
    gate = stag + walk + CFG["backoff_cd"] + CFG["beam_charge"] + CFG["beam_recover"]       # barrier down when the first beam is over
    return stag, walk, gate


def estimate(name, *, hit_every, dodge, open_s, wrap_every, approach_s, cover_s, player=True):
    """hit_every   seconds per LANDED hit while it is free to hit (the guard makes 1.2 s the floor)
    dodge       seconds lost per arm thrust (stepping out of the 9-block zone and back), 0 = never dodges
    open_s      from the start to the first hit (walking up the avenue, the first beam included)
    wrap_every  seconds per landed hit in the final wrap (the monster is wrapped round the giant: close, big target)
    approach_s  seconds to close the 30 blocks after a retreat, cover_s extra seconds for taking cover from the beam
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
    margin = CFG["wrap_ticks"] * TICK - (CFG["wrap_at"] - 1) * wrap_every - 1.0
    print(f"{name}: {total:5.0f} s = {total / 60:.1f} min   (opening {open_s:.0f} s, {CFG['core_hp'] - CFG['wrap_at']} hits in {engaged:.0f} s, "
          f"{n_backoff} back-offs x {per_backoff:.1f} s = {n_backoff * per_backoff:.0f} s, wrap {wrap:.0f} s, margin in the countdown {margin:.1f} s)")
    return total


if __name__ == "__main__":
    stag, walk, gate = backoff_ticks()
    print(f"back-off: stagger {stag} + retreat {walk} ticks, barrier up {gate} ticks = {gate * TICK:.1f} s until the first attack is over")
    guard = CFG["hit_cd"] * TICK
    click = 0.95
    scripted_every = math.ceil(guard / click) * click          # a click every 0.95 s, the guard swallows every other one
    # (a) the scripted attacker of the earlier test: one click per 0.95 s, never dodges, runs at 13 blocks/s, so the barrier's gate is all it waits
    estimate("(a) scripted, never dodges", hit_every=scripted_every, dodge=0.0, open_s=9, wrap_every=scripted_every, approach_s=0, cover_s=0, player=False)
    # (b) a first-time player: a landed hit every 2.0 s (swing, aim at a 4.5-block target, the guard), loses 2.5 s to every arm thrust,
    # walks to the monster at 6 blocks/s and takes cover once from the first beam (4 s), 8 s to close the 30 blocks after a retreat plus
    # 4 s of cover from its beam, a landed hit every 1.5 s in the wrap (close, big target, no dodging to do)
    estimate("(b) first-time player", hit_every=2.0, dodge=2.5, open_s=24, wrap_every=1.5, approach_s=8, cover_s=4, player=True)
    # sensitivity: slower and faster first-timers
    estimate("    slow player (2.6 s per hit, 3 s per thrust)", hit_every=2.6, dodge=3.0, open_s=30, wrap_every=1.8, approach_s=10, cover_s=5, player=True)
    estimate("    quick player (1.5 s per hit, 2 s per thrust)", hit_every=1.5, dodge=2.0, open_s=18, wrap_every=1.3, approach_s=6, cover_s=3, player=True)

