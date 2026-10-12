execute positioned 65.5 64.5 118.0 if entity @a[limit=1,distance=..2.6] run function angel:story/s1/x31
execute if score #step angel.story matches 31 positioned 65.5 64.5 115.5 if entity @a[limit=1,distance=..1.8] run function angel:story/s1/x31
execute if score #step angel.story matches 31 if data entity @e[tag=angel.ia_phone,limit=1] interaction run function angel:story/s1/x31
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 31 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 31 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s1/sk31
execute if score #step angel.story matches 31 if score #stept angel.story matches 3000 run function angel:story/s1/t31
execute if score #step angel.story matches 31 if score #stept angel.story matches 400 run function angel:story/s1/h31
execute if score #step angel.story matches 31 if score #force angel.story matches 1 run function angel:story/s1/x31
