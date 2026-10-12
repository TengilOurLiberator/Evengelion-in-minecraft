execute if score #wait angel.story matches 0 run function angel:story/s5/x127
execute if score #step angel.story matches 127 if score #wait angel.story matches 1.. if score #wt angel.story matches 0.. run function angel:story/wait_tick
execute if score #step angel.story matches 127 if score #bsa angel.story matches -1 unless score #bridge_speaking angel.story matches 1.. run scoreboard players set #bsa angel.story 0
execute if score #step angel.story matches 127 if score #bsa angel.story matches 0 if score #bridge_speaking angel.story matches 1.. run scoreboard players set #bsa angel.story 1
execute if score #step angel.story matches 127 if score #bsa angel.story matches 1 unless score #bridge_speaking angel.story matches 1.. run scoreboard players set #wait angel.story 0
execute if score #step angel.story matches 127 if score #talking angel.story matches 0 unless score #bridge_speaking angel.story matches 1.. run scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 127 if score #nagt angel.story matches 240 run function angel:story/s5/nn127
execute if score #step angel.story matches 127 if score #force angel.story matches 1 run function angel:story/s5/x127
