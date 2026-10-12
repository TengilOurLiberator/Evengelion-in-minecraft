execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s4/x175
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 175 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 175 if score #stept angel.story matches 3600 run function angel:story/s4/t175
execute if score #step angel.story matches 175 if score #stept angel.story matches 700 run function angel:story/s4/h175
execute if score #step angel.story matches 175 if score #force angel.story matches 1 run function angel:story/s4/x175
