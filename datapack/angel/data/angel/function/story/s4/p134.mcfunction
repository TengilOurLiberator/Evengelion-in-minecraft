execute if score #arrived_ritsuko angel.cast matches 1 if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x134
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 134 if score #stept angel.story matches 300 run function angel:story/s4/t134
execute if score #step angel.story matches 134 if score #force angel.story matches 1 run function angel:story/s4/x134
