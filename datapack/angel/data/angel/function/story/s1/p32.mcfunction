function angel:story/s1/f_look40
execute if score #looking angel.story matches 1 run function angel:story/s1/x32
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 32 if score #stept angel.story matches 900 run function angel:story/s1/t32
execute if score #step angel.story matches 32 if score #stept angel.story matches 240 run function angel:story/s1/h32
execute if score #step angel.story matches 32 if score #force angel.story matches 1 run function angel:story/s1/x32
