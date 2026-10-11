execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s5/x11
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 11 if score #stept angel.story matches 3600 run function angel:story/s5/t11
execute if score #step angel.story matches 11 if score #stept angel.story matches 700 run function angel:story/s5/h11
execute if score #step angel.story matches 11 if score #force angel.story matches 1 run function angel:story/s5/x11
