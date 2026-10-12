execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s5/x226
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 226 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 226 if score #stept angel.story matches 1200 run function angel:story/s5/t226
execute if score #step angel.story matches 226 if score #force angel.story matches 1 run function angel:story/s5/x226
