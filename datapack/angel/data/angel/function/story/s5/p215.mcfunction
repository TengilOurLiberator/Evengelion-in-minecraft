execute positioned 3096.0 54.0 77.4 unless entity @a[limit=1,distance=..6.5] run function angel:story/s5/x215
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 215 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 215 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s5/sk215
execute if score #step angel.story matches 215 if score #stept angel.story matches 1200 run function angel:story/s5/t215
execute if score #step angel.story matches 215 if score #stept angel.story matches 400 run function angel:story/s5/h215
execute if score #step angel.story matches 215 if score #force angel.story matches 1 run function angel:story/s5/x215
