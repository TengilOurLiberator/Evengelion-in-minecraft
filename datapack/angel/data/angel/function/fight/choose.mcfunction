# the first attack after a back-off (it is holding its ground, barrier up) is always the eye beam, wherever the giant stands: the player must meet the beam
execute if score #hold angel.fight matches 1 as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..140] run return run function angel:fight/begin_beam
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..24] run return run function angel:fight/begin_thrust
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..140] run return run function angel:fight/begin_beam
