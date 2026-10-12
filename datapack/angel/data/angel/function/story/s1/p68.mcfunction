execute positioned 97.477 64.0 128.7 if entity @a[limit=1,distance=..2.2] run function angel:story/s1/x68
execute if score #step angel.story matches 68 if data entity @e[tag=angel.ia_car,limit=1] interaction run function angel:story/s1/x68
execute if score #step angel.story matches 68 if data entity @e[tag=angel.ia_car,limit=1] attack run function angel:story/s1/x68
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 68 if score #stept angel.story matches 1400 run function angel:story/s1/t68
execute if score #step angel.story matches 68 if score #stept angel.story matches 600 run function angel:story/s1/h68
execute if score #step angel.story matches 68 if score #nagt angel.story matches 160 run function angel:story/s1/n68
execute if score #step angel.story matches 68 if score #force angel.story matches 1 run function angel:story/s1/x68
