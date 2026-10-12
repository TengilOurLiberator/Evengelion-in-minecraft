scoreboard players operation #y1 angel.cast = #na_medic2 angel.cast
scoreboard players add #y1 angel.cast 5000
execute store result entity @s Rotation[0] float 0.01 run scoreboard players get #y1 angel.cast
