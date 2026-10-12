execute as @e[type=minecraft:mannequin,tag=angel.ritsuko,limit=1] at @s if entity @a[limit=1,distance=..11.0] run function angel:story/s4/x153
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 153 if score #stept angel.story matches 1800 run function angel:story/s4/t153
execute if score #step angel.story matches 153 if score #force angel.story matches 1 run function angel:story/s4/x153
