execute positioned 3006.1 107.0 160.5 if entity @a[limit=1,distance=..0.9] run function angel:story/s4/x133
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 133 if score #stept angel.story matches 1000 run function angel:story/s4/t133
execute if score #step angel.story matches 133 if score #stept angel.story matches 280 run function angel:story/s4/h133
execute if score #step angel.story matches 133 if score #force angel.story matches 1 run function angel:story/s4/x133
