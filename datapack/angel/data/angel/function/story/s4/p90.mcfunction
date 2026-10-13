execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s4/x90
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 90 if score #stept angel.story matches 500 run function angel:story/s4/t90
execute if score #step angel.story matches 90 if score #force angel.story matches 1 run function angel:story/s4/x90
