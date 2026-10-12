# the barrier comes down and the monster is free to advance again
scoreboard players set #hold angel.fight 0
scoreboard players set #bar angel.fight 0
scoreboard players set #barp angel.fight 0
scoreboard players set #nav angel.fight 99
execute if score #phase angel.fight matches 1 run bossbar set angel:fight/angel name {"text":"ANGEL","color":"red"}
execute if score #phase angel.fight matches 2 run bossbar set angel:fight/angel name {"text":"ANGEL  -  core cracked","color":"red"}
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run playsound angel:sfx.barrier hostile @a ~ ~ ~ 3 0.6
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:end_rod ~ ~2.25 ~ 3 3 3 0.1 30 force
