execute positioned 3009.5 107.0 160.5 if entity @a[limit=1,distance=..15.0] run function angel:story/s4/x83
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 83 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 83 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s4/sk83
execute if score #step angel.story matches 83 if score #stept angel.story matches 1800 run function angel:story/s4/t83
execute if score #step angel.story matches 83 if score #force angel.story matches 1 run function angel:story/s4/x83
