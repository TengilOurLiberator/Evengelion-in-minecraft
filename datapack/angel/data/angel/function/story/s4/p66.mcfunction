execute if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x66
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 66 if score #stept angel.story matches 3600 run function angel:story/s4/t66
execute if score #step angel.story matches 66 if score #stept angel.story matches 700 run function angel:story/s4/h66
execute if score #step angel.story matches 66 if score #force angel.story matches 1 run function angel:story/s4/x66
