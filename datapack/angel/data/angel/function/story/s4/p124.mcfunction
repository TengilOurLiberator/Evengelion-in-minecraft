execute if score #arrived_ritsuko angel.cast matches 1 if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x124
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 124 if score #stept angel.story matches 300 run function angel:story/s4/t124
execute if score #step angel.story matches 124 if score #force angel.story matches 1 run function angel:story/s4/x124
