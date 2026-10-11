function angel:story/util/looking
execute if score #looking angel.story matches 1 run scoreboard players set #f.seen angel.story 1
execute if score #f.seen angel.story matches 1 if score #looking angel.story matches 0 run function angel:story/s1/x17
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 17 if score #stept angel.story matches 120 run function angel:story/s1/t17
execute if score #step angel.story matches 17 if score #force angel.story matches 1 run function angel:story/s1/x17
