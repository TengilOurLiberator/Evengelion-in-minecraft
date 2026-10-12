execute positioned 1160.0 64.0 160.0 if entity @a[limit=1,distance=..8.0] run function angel:story/s6/x104
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 104 if score #stept angel.story matches 80 run function angel:story/s6/t104
execute if score #step angel.story matches 104 if score #nagt angel.story matches 8 run function angel:story/s6/n104
execute if score #step angel.story matches 104 if score #force angel.story matches 1 run function angel:story/s6/x104
