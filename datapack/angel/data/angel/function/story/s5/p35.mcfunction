execute positioned 3096.5 54.0 72.5 if entity @a[limit=1,distance=..4] run scoreboard players add #f.hold angel.story 1
execute positioned 3096.5 54.0 72.5 unless entity @a[limit=1,distance=..4] run scoreboard players set #f.hold angel.story 0
execute positioned 3096.5 54.0 72.5 if entity @a[limit=1,distance=..1.5] run function angel:story/s5/x35
execute if score #step angel.story matches 35 if score #f.hold angel.story matches 60.. run function angel:story/s5/x35
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 35 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 35 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s5/sk35
execute if score #step angel.story matches 35 if score #stept angel.story matches 3000 run function angel:story/s5/t35
execute if score #step angel.story matches 35 if score #stept angel.story matches 800 run function angel:story/s5/h35
execute if score #step angel.story matches 35 if score #force angel.story matches 1 run function angel:story/s5/x35
