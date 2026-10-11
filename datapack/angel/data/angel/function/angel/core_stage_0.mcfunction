execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {block_state:"minecraft:red_concrete"}
