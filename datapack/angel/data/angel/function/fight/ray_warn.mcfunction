execute unless block ~ ~ ~ #angel:fight/beam_pass run return 0
particle minecraft:dust{color:[1.0,0.12,0.1],scale:2.2} ~ ~ ~ 0.05 0.05 0.05 0 1 force
scoreboard players remove #rs angel.fight 1
execute if score #rs angel.fight matches 1.. positioned ^ ^ ^3 run function angel:fight/ray_warn
