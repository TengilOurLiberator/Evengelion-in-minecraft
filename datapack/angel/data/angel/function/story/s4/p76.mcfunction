execute if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x76
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 76 if score #stept angel.story matches 3600 run function angel:story/s4/t76
execute if score #step angel.story matches 76 if score #stept angel.story matches 700 run function angel:story/s4/h76
execute if score #step angel.story matches 76 if score #force angel.story matches 1 run function angel:story/s4/x76
