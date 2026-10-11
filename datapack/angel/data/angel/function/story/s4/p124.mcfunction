execute positioned 3005.5 107.0 160.5 if entity @a[limit=1,distance=..1.2] run function angel:story/s4/x124
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 124 if score #stept angel.story matches 1000 run function angel:story/s4/t124
execute if score #step angel.story matches 124 if score #stept angel.story matches 280 run function angel:story/s4/h124
execute if score #step angel.story matches 124 if score #force angel.story matches 1 run function angel:story/s4/x124
