execute as @a[limit=1] store result score #tut.y1 angel.story run data get entity @s Rotation[0] 10
scoreboard players operation #tut.d angel.story = #tut.y1 angel.story
scoreboard players operation #tut.d angel.story -= #tut.y0 angel.story
scoreboard players operation #tut.d angel.story %= #c3600 angel.story
execute if score #tut.d angel.story matches 1801.. run scoreboard players remove #tut.d angel.story 3600
execute unless score #tut.d angel.story matches -599..599 run scoreboard players set #tut.m angel.story 1
execute if score #tut.m angel.story matches 1 run function angel:story/s1/x21
scoreboard players add #stept angel.story 1
scoreboard players add #nagt angel.story 1
execute if score #step angel.story matches 21 run scoreboard players add #stk angel.story 1
execute if score #step angel.story matches 21 if score #stept angel.story matches 160 run function angel:story/s1/t21
execute if score #step angel.story matches 21 if score #force angel.story matches 1 run function angel:story/s1/x21
