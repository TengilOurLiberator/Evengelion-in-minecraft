execute if score #mv.route angel.story matches 3 if score #mv.n angel.story matches 512.. run function angel:story/s2/x102
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 102 if score #stept angel.story matches 1800 run function angel:story/s2/t102
execute if score #step angel.story matches 102 if score #force angel.story matches 1 run function angel:story/s2/x102
