execute if score #wait angel.story matches 0 run function angel:story/s2/x61
execute if score #step angel.story matches 61 if score #wait angel.story matches 1.. if score #wt angel.story matches 0.. run function angel:story/wait_tick
execute if score #step angel.story matches 61 if score #talking angel.story matches 0 unless score #bridge_speaking angel.story matches 1.. run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 61 if score #bridge_speaking angel.story matches 1.. run scoreboard players set #stk angel.story 0
execute if score #step angel.story matches 61 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s2/sk61
execute if score #step angel.story matches 61 if score #talking angel.story matches 0 unless score #bridge_speaking angel.story matches 1.. run scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 61 if score #nagt angel.story matches 240 run function angel:story/s2/nn61
execute if score #step angel.story matches 61 if score #force angel.story matches 1 run function angel:story/s2/x61
