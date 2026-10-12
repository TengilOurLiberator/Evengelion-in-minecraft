execute positioned 37.5 65.0 128.5 if entity @a[limit=1,distance=..4.0] run scoreboard players add #mvok angel.story 1
execute positioned 37.5 65.0 128.5 unless entity @a[limit=1,distance=..4.0] run scoreboard players set #mvok angel.story 0
execute if score #mvok angel.story matches 8.. run function angel:story/s1/x6
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 6 if score #stept angel.story matches 240 run function angel:story/s1/t6
execute if score #step angel.story matches 6 if score #nagt angel.story matches 20 run function angel:story/s1/n6
execute if score #step angel.story matches 6 if score #force angel.story matches 1 run function angel:story/s1/x6
