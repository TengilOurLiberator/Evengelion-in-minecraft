scoreboard objectives add angel_world dummy
scoreboard players set #all angel_world 0
scoreboard players set #rebuild angel_world 1
execute in minecraft:overworld run function angel:world/geofront/c0
