execute store result score #l.y angel.story run data get entity @a[limit=1] Pos[1] 1
execute if score #l.y angel.story matches 108.. run function angel:story/s6/x93
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 93 if score #stept angel.story matches 180 run function angel:story/s6/t93
execute if score #step angel.story matches 93 if score #force angel.story matches 1 run function angel:story/s6/x93
