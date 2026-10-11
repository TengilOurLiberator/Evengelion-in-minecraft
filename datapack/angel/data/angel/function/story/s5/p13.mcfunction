execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s5/x13
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 13 if score #stept angel.story matches 3600 run function angel:story/s5/t13
execute if score #step angel.story matches 13 if score #stept angel.story matches 700 run function angel:story/s5/h13
execute if score #step angel.story matches 13 if score #force angel.story matches 1 run function angel:story/s5/x13
