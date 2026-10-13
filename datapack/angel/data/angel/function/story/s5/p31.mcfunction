execute as @e[type=minecraft:mannequin,tag=angel.ritsuko,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/s5/x31
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 31 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 31 if score #stk angel.story >= #stk_skip angel.story run function angel:story/s5/sk31
execute if score #step angel.story matches 31 if score #stept angel.story matches 1500 run function angel:story/s5/t31
execute if score #step angel.story matches 31 if score #stept angel.story matches 400 run function angel:story/s5/h31
execute if score #step angel.story matches 31 if score #force angel.story matches 1 run function angel:story/s5/x31
