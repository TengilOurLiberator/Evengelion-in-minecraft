# one click on the core box.  Three outcomes: landed (in reach, core not guarded), guarded (in reach, 1.2 s after a landed hit: sparks, a dull clank,
# nothing else) and blocked (beyond arm's length, or the barrier is up after a back-off: the octagon of light).
# Only a LANDED hit arms the guard (#hitcd); blocked, guarded and body hits never do.
data remove entity @s attack
execute if score #phase angel.fight matches 4.. run return 0
# the wrap (phase 3): no guard, no reach, no barrier - every click that connects counts
execute if score #phase angel.fight matches 3 run return run function angel:fight/wrap_hit
execute if score #bar angel.fight matches 1 run return run function angel:fight/core_blocked
# the giant's reach point is 22.0 up; the box's foot is half its height below the core centre
execute store success score #inreach angel.fight positioned ~ ~-19.75 ~ if entity @e[tag=angel.giant,distance=..12.5]
execute if score #inreach angel.fight matches 1 if score #hitcd angel.fight matches 1.. run return run function angel:fight/core_guarded
execute if score #inreach angel.fight matches 1 run return run function angel:fight/core_land
function angel:fight/core_blocked
