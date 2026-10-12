execute if score #wait angel.story matches 0 run function angel:story/s5/x110
execute if score #step angel.story matches 110 if score #wait angel.story matches 1.. if score #wt angel.story matches 0.. run function angel:story/wait_tick
execute if score #step angel.story matches 110 if score #talking angel.story matches 0 unless score #bridge_speaking angel.story matches 1.. run scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 110 if score #nagt angel.story matches 240 run function angel:story/s5/nn110
execute if score #step angel.story matches 110 if score #force angel.story matches 1 run function angel:story/s5/x110
