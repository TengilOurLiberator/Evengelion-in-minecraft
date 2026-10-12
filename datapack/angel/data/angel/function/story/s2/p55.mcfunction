execute positioned 180.125 83.0 52.955 if entity @a[limit=1,distance=..2.3] run function angel:story/s2/x55
execute if score #step angel.story matches 55 if data entity @e[tag=angel.ia_push,limit=1] interaction run function angel:story/s2/x55
execute if score #step angel.story matches 55 if data entity @e[tag=angel.ia_push,limit=1] attack run function angel:story/s2/x55
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 55 if score #stept angel.story matches 1000 run function angel:story/s2/t55
execute if score #step angel.story matches 55 if score #stept angel.story matches 500 run function angel:story/s2/h55
execute if score #step angel.story matches 55 if score #nagt angel.story matches 200 run function angel:story/s2/n55
execute if score #step angel.story matches 55 if score #force angel.story matches 1 run function angel:story/s2/x55
