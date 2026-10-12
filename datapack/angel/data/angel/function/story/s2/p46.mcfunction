execute positioned 180.247 83.0 52.265 if entity @a[limit=1,distance=..2.3] run function angel:story/s2/x46
execute if score #step angel.story matches 46 if data entity @e[tag=angel.ia_push,limit=1] interaction run function angel:story/s2/x46
execute if score #step angel.story matches 46 if data entity @e[tag=angel.ia_push,limit=1] attack run function angel:story/s2/x46
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 46 if score #stept angel.story matches 1000 run function angel:story/s2/t46
execute if score #step angel.story matches 46 if score #stept angel.story matches 500 run function angel:story/s2/h46
execute if score #step angel.story matches 46 if score #nagt angel.story matches 200 run function angel:story/s2/n46
execute if score #step angel.story matches 46 if score #force angel.story matches 1 run function angel:story/s2/x46
