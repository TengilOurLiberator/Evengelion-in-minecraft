# free when no fight is running: one score check
execute unless score #run angel.fight matches 1 run return 0
scoreboard players add #tick angel.fight 1
function angel:fight/pump
execute if score #phase angel.fight matches 4 run return run function angel:fight/won_tick
execute if score #phase angel.fight matches 5 run return run function angel:fight/lost_tick
function angel:fight/giant_tick
function angel:fight/hit_tick
function angel:fight/ai_tick
