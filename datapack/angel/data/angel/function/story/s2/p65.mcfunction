execute if score #arrived_misato angel.cast matches 1 run function angel:story/s2/x65
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 65 if score #stept angel.story matches 160 run function angel:story/s2/t65
execute if score #step angel.story matches 65 if score #force angel.story matches 1 run function angel:story/s2/x65
