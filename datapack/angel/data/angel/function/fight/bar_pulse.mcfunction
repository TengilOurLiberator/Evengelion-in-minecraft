# while the barrier is up after a back-off, the octagon flares every 1.2 s (no sound)
scoreboard players set #barp angel.fight 0
execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~2.25 ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_draw
