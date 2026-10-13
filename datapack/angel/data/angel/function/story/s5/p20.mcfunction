execute if score #arrived_misato angel.cast matches 1 run function angel:story/s5/x20
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 20 if score #stept angel.story matches 200 run function angel:story/s5/t20
execute if score #step angel.story matches 20 if score #force angel.story matches 1 run function angel:story/s5/x20
