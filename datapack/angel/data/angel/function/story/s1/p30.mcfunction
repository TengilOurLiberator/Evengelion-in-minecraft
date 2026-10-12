execute positioned 53.5 65.0 128.5 if entity @a[limit=1,distance=..5.0] run function angel:story/s1/x30
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 30 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 30 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s1/sk30
execute if score #step angel.story matches 30 if score #stept angel.story matches 2400 run function angel:story/s1/t30
execute if score #step angel.story matches 30 if score #force angel.story matches 1 run function angel:story/s1/x30
