execute if score #wait angel.story matches 0 run function angel:story/s3/x41
execute if score #step angel.story matches 41 if score #wait angel.story matches 1.. if score #wt angel.story matches 0.. run function angel:story/wait_tick
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 41 if score #nagt angel.story matches 320 run function angel:story/s3/n41
execute if score #step angel.story matches 41 if score #force angel.story matches 1 run function angel:story/s3/x41
