execute positioned 1160.0 64.0 160.0 if entity @a[limit=1,distance=..4.0] run scoreboard players add #mvok angel.story 1
execute positioned 1160.0 64.0 160.0 unless entity @a[limit=1,distance=..4.0] run scoreboard players set #mvok angel.story 0
execute if score #mvok angel.story matches 8.. run function angel:story/s7/x6
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 6 if score #stept angel.story matches 240 run function angel:story/s7/t6
execute if score #step angel.story matches 6 if score #nagt angel.story matches 20 run function angel:story/s7/n6
execute if score #step angel.story matches 6 if score #force angel.story matches 1 run function angel:story/s7/x6
