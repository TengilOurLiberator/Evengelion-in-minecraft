execute positioned 3096.0 54.0 77.4 unless entity @a[limit=1,distance=..6.5] run function angel:story/s5/x213
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 213 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 213 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s5/sk213
execute if score #step angel.story matches 213 if score #stept angel.story matches 1200 run function angel:story/s5/t213
execute if score #step angel.story matches 213 if score #stept angel.story matches 400 run function angel:story/s5/h213
execute if score #step angel.story matches 213 if score #force angel.story matches 1 run function angel:story/s5/x213
