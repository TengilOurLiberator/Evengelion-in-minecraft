execute if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x74
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 74 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 74 if score #stept angel.story matches 1500 run function angel:story/s4/t74
execute if score #step angel.story matches 74 if score #stept angel.story matches 400 run function angel:story/s4/h74
execute if score #step angel.story matches 74 if score #force angel.story matches 1 run function angel:story/s4/x74
