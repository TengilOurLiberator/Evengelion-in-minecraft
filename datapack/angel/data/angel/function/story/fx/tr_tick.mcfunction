execute as @e[tag=angel.trc] at @s run tp @s ^ ^ ^6
execute as @e[tag=angel.trc] at @s if entity @e[tag=angel.cmark,distance=..17.0] run function angel:story/fx/tr_hit
scoreboard players add @e[tag=angel.trc] angel.story 1
kill @e[tag=angel.trc,scores={angel.story=45..}]
