execute if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x59
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 59 if score #stept angel.story matches 400 run function angel:story/s4/t59
execute if score #step angel.story matches 59 if score #force angel.story matches 1 run function angel:story/s4/x59
