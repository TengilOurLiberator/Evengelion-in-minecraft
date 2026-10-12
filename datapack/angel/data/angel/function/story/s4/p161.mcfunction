execute as @e[type=minecraft:mannequin,tag=angel.ritsuko,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/s4/x161
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 161 if score #stept angel.story matches 3600 run function angel:story/s4/t161
execute if score #step angel.story matches 161 if score #stept angel.story matches 700 run function angel:story/s4/h161
execute if score #step angel.story matches 161 if score #force angel.story matches 1 run function angel:story/s4/x161
