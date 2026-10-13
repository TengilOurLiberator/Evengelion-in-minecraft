execute as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/s4/x29
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 29 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 29 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s4/sk29
execute if score #step angel.story matches 29 if score #stept angel.story matches 1500 run function angel:story/s4/t29
execute if score #step angel.story matches 29 if score #stept angel.story matches 400 run function angel:story/s4/h29
execute if score #step angel.story matches 29 if score #force angel.story matches 1 run function angel:story/s4/x29
