# VULNERABLE: the core burns (stage block: whole = red concrete, cracked = magma), full bright; its glow strips and veil are back; a halo of red glass pulses round it; no octagon
scoreboard players set #vs angel.fight 1
scoreboard players set #vp angel.fight 0
scoreboard players set #blk_n angel.fight 0
scoreboard players set #blk_why angel.fight 0
kill @e[type=minecraft:block_display,tag=angel.shield]
execute if score #phase angel.fight matches ..1 as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {block_state:"minecraft:red_concrete",brightness:{block:15,sky:15}}
execute if score #phase angel.fight matches 2.. as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {block_state:"minecraft:magma_block",brightness:{block:15,sky:15}}
execute as @e[type=minecraft:block_display,tag=angel.halo] run data merge entity @s {block_state:"minecraft:red_stained_glass"}
execute as @e[type=minecraft:block_display,tag=angel.coreglow] run data merge entity @s {block_state:"minecraft:red_concrete",brightness:{block:15,sky:15}}
execute as @e[type=minecraft:block_display,tag=angel.veil] run data merge entity @s {block_state:"minecraft:red_stained_glass"}
kill @e[type=minecraft:block_display,tag=angel.hot]
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~3.00 ~ run function angel:fight/hot_make
