execute unless entity @p[distance=..96] run return 0
execute store result score #y0 angel.cast run data get entity @s Rotation[0] 100
execute anchored eyes run rotate @s facing entity @p eyes
execute store result score #y1 angel.cast run data get entity @s Rotation[0] 100
scoreboard players operation #y1 angel.cast -= #y0 angel.cast
scoreboard players operation #y1 angel.cast %= #k36000 angel.cast
execute if score #y1 angel.cast matches 18001.. run scoreboard players remove #y1 angel.cast 36000
execute if score #y1 angel.cast matches 1201.. run function angel:cast/look_clamp_pos
execute if score #y1 angel.cast matches ..-1201 run function angel:cast/look_clamp_neg
execute store result score #p0 angel.cast run data get entity @s Rotation[1] 100
execute if score #p0 angel.cast matches 3001.. run data modify entity @s Rotation[1] set value 30.0f
execute if score #p0 angel.cast matches ..-3001 run data modify entity @s Rotation[1] set value -30.0f
