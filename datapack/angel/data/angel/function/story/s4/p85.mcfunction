execute as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/s4/x85
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 85 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 85 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s4/sk85
execute if score #step angel.story matches 85 if score #stept angel.story matches 3600 run function angel:story/s4/t85
execute if score #step angel.story matches 85 if score #stept angel.story matches 700 run function angel:story/s4/h85
execute if score #step angel.story matches 85 if score #force angel.story matches 1 run function angel:story/s4/x85
