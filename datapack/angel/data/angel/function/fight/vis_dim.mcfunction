# SHIELDED: the core is dimmed (dull terracotta, low light), the glow strips and veil are out, the halo is gone, and the octagon of light stands in front of the monster
scoreboard players set #vs angel.fight 2
kill @e[type=minecraft:block_display,tag=angel.hot]
execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {block_state:"minecraft:red_terracotta",brightness:{block:4,sky:4}}
execute as @e[type=minecraft:block_display,tag=angel.halo] run data merge entity @s {block_state:"minecraft:gray_stained_glass"}
execute as @e[type=minecraft:block_display,tag=angel.coreglow] run data merge entity @s {block_state:"minecraft:red_terracotta",brightness:{block:4,sky:4}}
execute as @e[type=minecraft:block_display,tag=angel.veil] run data merge entity @s {block_state:"minecraft:air"}
kill @e[type=minecraft:block_display,tag=angel.shield]
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~3.00 ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/shield_make
