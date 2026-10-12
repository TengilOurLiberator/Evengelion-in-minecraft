execute positioned 1160.0 64.0 160.0 if entity @a[limit=1,distance=..8.0] run function angel:story/s6/x131
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 131 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 131 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s6/sk131
execute if score #step angel.story matches 131 if score #stk angel.story >= #stk_hint angel.story unless score #stkh angel.story matches 1 run function angel:story/s6/sh131
execute if score #step angel.story matches 131 if score #stept angel.story matches 80 run function angel:story/s6/t131
execute if score #step angel.story matches 131 if score #nagt angel.story matches 8 run function angel:story/s6/n131
execute if score #step angel.story matches 131 if score #force angel.story matches 1 run function angel:story/s6/x131
