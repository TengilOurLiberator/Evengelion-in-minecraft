scoreboard players set #force angel.story 0
scoreboard players set #br angel.story 0
execute if score #consent angel.story matches 1 run scoreboard players set #br angel.story 1
execute if score #br angel.story matches 1 run function angel:story/s5/b124
execute if score #br angel.story matches 0 run function angel:story/s5/b124n
