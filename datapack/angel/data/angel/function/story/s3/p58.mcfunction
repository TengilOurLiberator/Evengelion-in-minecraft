execute positioned 2025.484 98.0 101.851 if entity @a[limit=1,distance=..4.0] run scoreboard players add #mvok angel.story 1
execute positioned 2025.484 98.0 101.851 unless entity @a[limit=1,distance=..4.0] run scoreboard players set #mvok angel.story 0
execute if score #mvok angel.story matches 8.. run function angel:story/s3/x58
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 58 if score #stept angel.story matches 240 run function angel:story/s3/t58
execute if score #step angel.story matches 58 if score #nagt angel.story matches 20 run function angel:story/s3/n58
execute if score #step angel.story matches 58 if score #force angel.story matches 1 run function angel:story/s3/x58
