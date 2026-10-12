scoreboard players operation #y1 angel.cast = #na_misato angel.cast
scoreboard players add #y1 angel.cast 0
execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #y1 angel.cast
