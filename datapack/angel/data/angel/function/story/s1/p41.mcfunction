function angel:story/s1/f_look40
execute if score #looking angel.story matches 1 run function angel:story/s1/x41
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 41 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 41 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s1/sk41
execute if score #step angel.story matches 41 if score #stept angel.story matches 240 run function angel:story/s1/t41
execute if score #step angel.story matches 41 if score #stept angel.story matches 240 run function angel:story/s1/h41
execute if score #step angel.story matches 41 if score #force angel.story matches 1 run function angel:story/s1/x41
