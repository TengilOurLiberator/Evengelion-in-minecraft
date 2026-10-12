execute positioned 179.118 83.0 58.667 if entity @a[limit=1,distance=..2.2] run function angel:story/s2/x90
execute if score #step angel.story matches 90 if data entity @e[tag=angel.ia_car,limit=1] interaction run function angel:story/s2/x90
execute if score #step angel.story matches 90 if data entity @e[tag=angel.ia_car,limit=1] attack run function angel:story/s2/x90
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 90 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 90 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s2/sk90
execute if score #step angel.story matches 90 if score #stept angel.story matches 400 run function angel:story/s2/t90
execute if score #step angel.story matches 90 if score #stept angel.story matches 160 run function angel:story/s2/h90
execute if score #step angel.story matches 90 if score #force angel.story matches 1 run function angel:story/s2/x90
