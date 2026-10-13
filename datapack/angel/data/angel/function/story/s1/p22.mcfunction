execute as @e[tag=angel.tut_mark,limit=1] at @s unless entity @a[limit=1,distance=..7.0] run function angel:story/s1/x22
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 22 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 22 if score #stept angel.story matches 80 run function angel:story/s1/t22
execute if score #step angel.story matches 22 if score #force angel.story matches 1 run function angel:story/s1/x22
