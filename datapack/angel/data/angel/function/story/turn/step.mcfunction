execute store result score #ty0 angel.story run data get entity @s Rotation[0] 100
$execute anchored eyes run rotate @s facing $(x) $(y) $(z)
execute store result score #ty1 angel.story run data get entity @s Rotation[0] 100
execute store result score #tp1 angel.story run data get entity @s Rotation[1] 100
scoreboard players operation #ty1 angel.story -= #ty0 angel.story
scoreboard players set #c36000 angel.story 36000
scoreboard players operation #ty1 angel.story %= #c36000 angel.story
execute if score #ty1 angel.story matches 18001.. run scoreboard players remove #ty1 angel.story 36000
execute if score #ty1 angel.story matches 1401.. run scoreboard players set #ty1 angel.story 1400
execute if score #ty1 angel.story matches ..-1401 run scoreboard players set #ty1 angel.story -1400
scoreboard players operation #ty0 angel.story += #ty1 angel.story
execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #ty0 angel.story
execute if score #tp1 angel.story matches 4501.. run scoreboard players set #tp1 angel.story 4500
execute if score #tp1 angel.story matches ..-3001 run scoreboard players set #tp1 angel.story -3000
execute store result entity @s Rotation[1] float 0.01 run scoreboard players get #tp1 angel.story
