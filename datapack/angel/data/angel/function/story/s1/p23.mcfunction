execute as @e[tag=angel.tut_mark,limit=1] at @s unless entity @a[limit=1,distance=..3] run function angel:story/s1/x23
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 23 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 23 if score #stept angel.story matches 160 run function angel:story/s1/t23
execute if score #step angel.story matches 23 if score #force angel.story matches 1 run function angel:story/s1/x23
