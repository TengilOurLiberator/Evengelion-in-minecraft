execute positioned 2305.772 18.0 156.45 if entity @a[limit=1,distance=..2.5] run scoreboard players add #mvok angel.story 1
execute positioned 2305.772 18.0 156.45 unless entity @a[limit=1,distance=..2.5] run scoreboard players set #mvok angel.story 0
execute if score #mvok angel.story matches 8.. run function angel:story/s3/x109
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 109 if score #stept angel.story matches 240 run function angel:story/s3/t109
execute if score #step angel.story matches 109 if score #nagt angel.story matches 20 run function angel:story/s3/n109
execute if score #step angel.story matches 109 if score #force angel.story matches 1 run function angel:story/s3/x109
