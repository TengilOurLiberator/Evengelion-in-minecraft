execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:falling_dust{block_state:"minecraft:gray_concrete"} ~ ~0.5 ~ 1.6 0.2 1.4 0 8 force
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:falling_lava ~ ~0.2 ~ 1.4 0.2 1.2 0 7 force
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:white_ash ~ ~-1 ~ 2 3 2 0.01 8 force
execute if score #rg.near angel.story matches 1 as @a[limit=1] at @s rotated ~ 0 positioned ^ ^3.5 ^1.0 run particle minecraft:falling_dust{block_state:"minecraft:gray_concrete"} ~ ~ ~ 0.9 1.2 0.9 0 14 force
execute if score #rg.near angel.story matches 1 as @a[limit=1] at @s rotated ~ 0 positioned ^ ^3.2 ^1.0 run particle minecraft:falling_lava ~ ~ ~ 0.6 1 0.6 0 6 force
execute if score #rg.near angel.story matches 1 as @a[limit=1] at @s rotated ~ 0 positioned ^ ^2.4 ^0.8 run particle minecraft:electric_spark ~ ~ ~ 0.5 0.8 0.5 0.05 12 force
