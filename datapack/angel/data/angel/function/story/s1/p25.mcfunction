execute if score #never angel.story matches 1 run function angel:story/s1/x25
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 25 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 25 if score #stept angel.story matches 120 run function angel:story/s1/t25
execute if score #step angel.story matches 25 if score #force angel.story matches 1 run function angel:story/s1/x25
