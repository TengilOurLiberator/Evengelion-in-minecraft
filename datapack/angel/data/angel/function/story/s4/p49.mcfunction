execute as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s if entity @a[limit=1,distance=..6.0] run function angel:story/s4/x49
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 49 if score #stept angel.story matches 2400 run function angel:story/s4/t49
execute if score #step angel.story matches 49 if score #stept angel.story matches 600 run function angel:story/s4/h49
execute if score #step angel.story matches 49 if score #force angel.story matches 1 run function angel:story/s4/x49
