execute positioned 65.5 64.5 118.0 if entity @a[limit=1,distance=..2.6] run function angel:story/s1/x19
execute if score #step angel.story matches 19 positioned 65.5 64.5 115.5 if entity @a[limit=1,distance=..1.8] run function angel:story/s1/x19
execute if score #step angel.story matches 19 if data entity @e[tag=angel.ia_phone,limit=1] interaction run function angel:story/s1/x19
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 19 if score #stept angel.story matches 3000 run function angel:story/s1/t19
execute if score #step angel.story matches 19 if score #stept angel.story matches 400 run function angel:story/s1/h19
execute if score #step angel.story matches 19 if score #force angel.story matches 1 run function angel:story/s1/x19
