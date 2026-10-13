execute as @e[type=minecraft:mannequin,tag=angel.ritsuko,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/s4/x166
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 166 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 166 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s4/sk166
execute if score #step angel.story matches 166 if score #stept angel.story matches 1500 run function angel:story/s4/t166
execute if score #step angel.story matches 166 if score #stept angel.story matches 400 run function angel:story/s4/h166
execute if score #step angel.story matches 166 if score #force angel.story matches 1 run function angel:story/s4/x166
