execute positioned 93.5 64.0 128.5 if entity @a[limit=1,distance=..3.0] run function angel:story/s1/x15
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 15 if score #stept angel.story matches 3000 run function angel:story/s1/t15
execute if score #step angel.story matches 15 if score #stept angel.story matches 900 run function angel:story/s1/h15
execute if score #step angel.story matches 15 if score #force angel.story matches 1 run function angel:story/s1/x15
