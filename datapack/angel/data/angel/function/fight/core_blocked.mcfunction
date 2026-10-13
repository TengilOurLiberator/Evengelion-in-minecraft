# a swing the barrier stopped: the giant is too far (#blk_why 1) or the back-off barrier is up (#blk_why 2).  Every one is counted (#blk_n since the last landed hit /
# barrier change, #blk_tot in all); the effects are rate-limited so that flailing is not a wall of noise
scoreboard players add #blk_n angel.fight 1
scoreboard players add #blk_tot angel.fight 1
execute if score #bar angel.fight matches 1 run scoreboard players set #blk_why angel.fight 2
execute unless score #bar angel.fight matches 1 run scoreboard players set #blk_why angel.fight 1
execute if score #blockcd angel.fight matches 1.. run return 0
scoreboard players set #blockcd angel.fight 6
execute if score #blocked1 angel.fight matches 0 run function angel:fight/first_blocked
# the octagon flares white and rings (at the core box's foot, the tone is a 3.6 s sound: at most one per 2 s)
function angel:fight/shield_flare
execute unless score #barsnd angel.fight matches 1.. run function angel:fight/barrier_tone
