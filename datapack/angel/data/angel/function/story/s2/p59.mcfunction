execute positioned 180.125 83.0 52.955 if entity @a[limit=1,distance=..2.3] run function angel:story/s2/x59
execute if score #step angel.story matches 59 if data entity @e[tag=angel.ia_push,limit=1] interaction run function angel:story/s2/x59
execute if score #step angel.story matches 59 if data entity @e[tag=angel.ia_push,limit=1] attack run function angel:story/s2/x59
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 59 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 59 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s2/sk59
execute if score #step angel.story matches 59 if score #stept angel.story matches 1000 run function angel:story/s2/t59
execute if score #step angel.story matches 59 if score #stept angel.story matches 500 run function angel:story/s2/h59
execute if score #step angel.story matches 59 if score #nagt angel.story matches 200 run function angel:story/s2/n59
execute if score #step angel.story matches 59 if score #force angel.story matches 1 run function angel:story/s2/x59
