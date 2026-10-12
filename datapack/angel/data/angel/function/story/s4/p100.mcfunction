execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s4/x100
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 100 if score #stept angel.story matches 500 run function angel:story/s4/t100
execute if score #step angel.story matches 100 if score #force angel.story matches 1 run function angel:story/s4/x100
