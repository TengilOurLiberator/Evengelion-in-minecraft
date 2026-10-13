execute positioned 93.5 64.0 128.5 if entity @a[limit=1,distance=..3.0] run function angel:story/s1/x39
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 39 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 39 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s1/sk39
execute if score #step angel.story matches 39 if score #stept angel.story matches 3000 run function angel:story/s1/t39
execute if score #step angel.story matches 39 if score #stept angel.story matches 900 run function angel:story/s1/h39
execute if score #step angel.story matches 39 if score #force angel.story matches 1 run function angel:story/s1/x39
