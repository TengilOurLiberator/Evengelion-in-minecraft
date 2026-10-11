execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..24] run return run function angel:fight/begin_thrust
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..140] run return run function angel:fight/begin_beam
