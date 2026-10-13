execute if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x72
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 72 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 72 if score #stept angel.story matches 1500 run function angel:story/s4/t72
execute if score #step angel.story matches 72 if score #stept angel.story matches 400 run function angel:story/s4/h72
execute if score #step angel.story matches 72 if score #force angel.story matches 1 run function angel:story/s4/x72
