execute positioned 179.101 83.0 58.765 if entity @a[limit=1,distance=..2.2] run function angel:story/s2/x64
execute if score #step angel.story matches 64 if data entity @e[tag=angel.ia_car,limit=1] interaction run function angel:story/s2/x64
execute if score #step angel.story matches 64 if data entity @e[tag=angel.ia_car,limit=1] attack run function angel:story/s2/x64
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 64 if score #stept angel.story matches 400 run function angel:story/s2/t64
execute if score #step angel.story matches 64 if score #stept angel.story matches 160 run function angel:story/s2/h64
execute if score #step angel.story matches 64 if score #force angel.story matches 1 run function angel:story/s2/x64
