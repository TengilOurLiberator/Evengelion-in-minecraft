execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s5/x14
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 14 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 14 if score #stept angel.story matches 1500 run function angel:story/s5/t14
execute if score #step angel.story matches 14 if score #stept angel.story matches 400 run function angel:story/s5/h14
execute if score #step angel.story matches 14 if score #force angel.story matches 1 run function angel:story/s5/x14
