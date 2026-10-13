# one swing that hit the core (the core box, or the larger box round it).  Two outcomes, judged by ONE test (#vuln, see vis_state): the barrier is down and the
# giant is within arm's length -> LANDED (it always counts: there is no guard); otherwise BLOCKED (the octagon flares, a ringing tone, #blk_n / #blk_why).
# The wrap (phase 3) is separate: every swing that connects counts.
data remove entity @s attack
execute if score #phase angel.fight matches 4.. run return 0
execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit
function angel:fight/vis_state
execute if score #vuln angel.fight matches 1 run return run function angel:fight/core_land
function angel:fight/core_blocked
