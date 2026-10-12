execute positioned 3096.0 54.0 77.4 if entity @a[limit=1,distance=..2.0] run function angel:story/s5/x190
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 190 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 190 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s5/sk190
execute if score #step angel.story matches 190 if score #stept angel.story matches 2400 run function angel:story/s5/t190
execute if score #step angel.story matches 190 if score #stept angel.story matches 500 run function angel:story/s5/h190
execute if score #step angel.story matches 190 if score #force angel.story matches 1 run function angel:story/s5/x190
