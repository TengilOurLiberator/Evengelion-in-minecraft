execute if score #phase angel.fight matches 5 run scoreboard players set #beat angel.story 81
execute if score #beat angel.story matches 81 if score #run angel.fight matches 1 if score #phase angel.fight matches 0..3 run scoreboard players set #beat angel.story 70
execute if score #f.fight_won angel.story matches 1 run function angel:story/s7/x8
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 8 if score #force angel.story matches 1 run function angel:story/s7/x8
