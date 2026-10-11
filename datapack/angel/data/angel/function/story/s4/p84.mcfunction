execute positioned 3009.5 107.0 160.5 if entity @a[limit=1,distance=..8.5] run function angel:story/s4/x84
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 84 if score #stept angel.story matches 1800 run function angel:story/s4/t84
execute if score #step angel.story matches 84 if score #force angel.story matches 1 run function angel:story/s4/x84
