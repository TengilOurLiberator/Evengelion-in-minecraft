scoreboard players set #y1 angel.cast -9000
scoreboard players operation #y1 angel.cast -= #y0 angel.cast
scoreboard players operation #y1 angel.cast %= #k36000 angel.cast
execute if score #y1 angel.cast matches 18001.. run scoreboard players remove #y1 angel.cast 36000
scoreboard players operation #y0 angel.cast = #y1 angel.cast
