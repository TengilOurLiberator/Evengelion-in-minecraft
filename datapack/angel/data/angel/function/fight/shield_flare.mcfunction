# a swing hit the barrier (or it just went up / down): the octagon flares white for 3 ticks, with a burst of light
execute unless entity @e[type=minecraft:block_display,tag=angel.sbar,limit=1] run return 0
execute as @e[type=minecraft:block_display,tag=angel.sbar] run data merge entity @s {block_state:"minecraft:white_concrete"}
execute as @e[type=minecraft:block_display,tag=angel.sfill] run data merge entity @s {block_state:"minecraft:white_stained_glass"}
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~3.00 ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/shield_flare_fx
schedule function angel:fight/shield_calm 3t
