execute as @e[type=minecraft:block_display,tag=angel.corebody] unless entity @s[tag=angel.halo] run data merge entity @s {block_state:"minecraft:magma_block"}
execute as @e[type=minecraft:block_display,tag=angel.crack1] run data merge entity @s {block_state:"minecraft:air"}
execute as @e[type=minecraft:block_display,tag=angel.crack2] run data merge entity @s {block_state:"minecraft:air"}
execute as @e[type=minecraft:block_display,tag=angel.crack3] run data merge entity @s {block_state:"minecraft:air"}
execute as @e[type=minecraft:block_display,tag=angel.crack4] run data merge entity @s {block_state:"minecraft:air"}
