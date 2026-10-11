execute if score #wait angel.story matches 0 run function angel:story/s3/x25
execute if score #step angel.story matches 25 if score #wait angel.story matches 1.. if score #wt angel.story matches 0.. run function angel:story/wait_tick
execute if score #step angel.story matches 25 if score #force angel.story matches 1 run function angel:story/s3/x25
