execute if score #never angel.story matches 1 run function angel:story/s1/x24
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 24 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 24 if score #stept angel.story matches 100 run function angel:story/s1/t24
execute if score #step angel.story matches 24 if score #force angel.story matches 1 run function angel:story/s1/x24
