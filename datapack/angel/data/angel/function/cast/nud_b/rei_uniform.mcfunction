scoreboard players operation #y1 angel.cast = #na_rei_uniform angel.cast
scoreboard players remove #y1 angel.cast 5000
execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #y1 angel.cast
