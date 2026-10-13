execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s5/x27
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 27 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 27 if score #stept angel.story matches 1500 run function angel:story/s5/t27
execute if score #step angel.story matches 27 if score #stept angel.story matches 400 run function angel:story/s5/h27
execute if score #step angel.story matches 27 if score #force angel.story matches 1 run function angel:story/s5/x27
