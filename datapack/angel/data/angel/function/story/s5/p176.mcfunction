execute positioned 3096.0 54.0 77.4 if entity @a[limit=1,distance=..2.0] run function angel:story/s5/x176
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 176 if score #stept angel.story matches 2400 run function angel:story/s5/t176
execute if score #step angel.story matches 176 if score #stept angel.story matches 500 run function angel:story/s5/h176
execute if score #step angel.story matches 176 if score #force angel.story matches 1 run function angel:story/s5/x176
