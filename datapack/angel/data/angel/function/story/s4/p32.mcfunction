execute if score #arrived_misato angel.cast matches 1 run function angel:story/s4/x32
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 32 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 32 if score #stept angel.story matches 3600 run function angel:story/s4/t32
execute if score #step angel.story matches 32 if score #stept angel.story matches 700 run function angel:story/s4/h32
execute if score #step angel.story matches 32 if score #force angel.story matches 1 run function angel:story/s4/x32
