execute as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/s4/x27
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 27 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 27 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s4/sk27
execute if score #step angel.story matches 27 if score #stept angel.story matches 3600 run function angel:story/s4/t27
execute if score #step angel.story matches 27 if score #stept angel.story matches 700 run function angel:story/s4/h27
execute if score #step angel.story matches 27 if score #force angel.story matches 1 run function angel:story/s4/x27
