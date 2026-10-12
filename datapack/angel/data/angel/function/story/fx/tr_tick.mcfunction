execute as @e[tag=angel.trc] at @s run tp @s ^ ^ ^3.5
execute as @e[tag=angel.trc] at @s run particle minecraft:large_smoke ~ ~ ~ 0.4 0.4 0.4 0.0 2 force
execute as @e[tag=angel.trc] at @s run particle minecraft:flame ~ ~ ~ 0.25 0.25 0.25 0.01 2 force
execute as @e[tag=angel.trc] at @s if entity @e[tag=angel.cmark,distance=..17.0] run function angel:story/fx/tr_hit
scoreboard players add @e[tag=angel.trc] angel.story 1
kill @e[tag=angel.trc,scores={angel.story=70..}]
