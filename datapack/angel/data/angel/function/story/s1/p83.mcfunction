execute positioned 97.478 64.0 128.8 if entity @a[limit=1,distance=..2.2] run function angel:story/s1/x83
execute if score #step angel.story matches 83 if data entity @e[tag=angel.ia_car,limit=1] interaction run function angel:story/s1/x83
execute if score #step angel.story matches 83 if data entity @e[tag=angel.ia_car,limit=1] attack run function angel:story/s1/x83
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 83 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 83 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s1/sk83
execute if score #step angel.story matches 83 if score #stept angel.story matches 1400 run function angel:story/s1/t83
execute if score #step angel.story matches 83 if score #stept angel.story matches 600 run function angel:story/s1/h83
execute if score #step angel.story matches 83 if score #nagt angel.story matches 160 run function angel:story/s1/n83
execute if score #step angel.story matches 83 if score #force angel.story matches 1 run function angel:story/s1/x83
