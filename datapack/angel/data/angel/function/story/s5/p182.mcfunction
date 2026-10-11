execute if score #wait angel.story matches 0 run function angel:story/s5/x182
execute if score #step angel.story matches 182 if score #wait angel.story matches 1.. if score #wt angel.story matches 0.. run function angel:story/wait_tick
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 182 if score #nagt angel.story matches 180 run function angel:story/s5/n182
execute if score #step angel.story matches 182 if score #force angel.story matches 1 run function angel:story/s5/x182
