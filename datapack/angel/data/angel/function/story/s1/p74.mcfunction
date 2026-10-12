execute positioned 97.478 64.0 128.8 if entity @a[limit=1,distance=..2.2] run function angel:story/s1/x74
execute if score #step angel.story matches 74 if data entity @e[tag=angel.ia_car,limit=1] interaction run function angel:story/s1/x74
execute if score #step angel.story matches 74 if data entity @e[tag=angel.ia_car,limit=1] attack run function angel:story/s1/x74
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 74 if score #stept angel.story matches 1400 run function angel:story/s1/t74
execute if score #step angel.story matches 74 if score #stept angel.story matches 600 run function angel:story/s1/h74
execute if score #step angel.story matches 74 if score #nagt angel.story matches 160 run function angel:story/s1/n74
execute if score #step angel.story matches 74 if score #force angel.story matches 1 run function angel:story/s1/x74
