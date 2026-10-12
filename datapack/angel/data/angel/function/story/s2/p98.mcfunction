execute if score #mv.route angel.story matches 3 if score #mv.n angel.story matches 512.. run function angel:story/s2/x98
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 98 if score #stept angel.story matches 1800 run function angel:story/s2/t98
execute if score #step angel.story matches 98 if score #force angel.story matches 1 run function angel:story/s2/x98
