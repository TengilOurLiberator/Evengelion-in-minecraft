execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s4/x162
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 162 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 162 if score #stept angel.story matches 1500 run function angel:story/s4/t162
execute if score #step angel.story matches 162 if score #stept angel.story matches 400 run function angel:story/s4/h162
execute if score #step angel.story matches 162 if score #force angel.story matches 1 run function angel:story/s4/x162
