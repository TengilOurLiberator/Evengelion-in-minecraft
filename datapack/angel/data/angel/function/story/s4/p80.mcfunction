execute if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x80
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 80 if score #stept angel.story matches 3600 run function angel:story/s4/t80
execute if score #step angel.story matches 80 if score #stept angel.story matches 700 run function angel:story/s4/h80
execute if score #step angel.story matches 80 if score #force angel.story matches 1 run function angel:story/s4/x80
