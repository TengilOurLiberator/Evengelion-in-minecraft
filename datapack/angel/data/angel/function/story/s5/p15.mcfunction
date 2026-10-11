execute if score #arrived_ritsuko angel.cast matches 1 run function angel:story/s5/x15
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 15 if score #stept angel.story matches 3600 run function angel:story/s5/t15
execute if score #step angel.story matches 15 if score #stept angel.story matches 700 run function angel:story/s5/h15
execute if score #step angel.story matches 15 if score #force angel.story matches 1 run function angel:story/s5/x15
