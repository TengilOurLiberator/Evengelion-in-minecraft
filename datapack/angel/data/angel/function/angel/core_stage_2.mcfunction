execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {block_state:"minecraft:black_concrete"}
execute as @e[type=minecraft:block_display,tag=angel.halo] run data merge entity @s {block_state:"minecraft:gray_stained_glass"}
