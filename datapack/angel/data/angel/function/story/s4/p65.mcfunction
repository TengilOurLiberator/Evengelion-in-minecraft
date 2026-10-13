execute as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s if entity @a[limit=1,distance=..11.0] run function angel:story/s4/x65
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 65 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 65 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s4/sk65
execute if score #step angel.story matches 65 if score #stept angel.story matches 1800 run function angel:story/s4/t65
execute if score #step angel.story matches 65 if score #force angel.story matches 1 run function angel:story/s4/x65
