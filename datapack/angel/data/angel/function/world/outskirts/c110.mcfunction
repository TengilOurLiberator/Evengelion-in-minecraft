forceload remove -16 -16 111 111
forceload remove -16 80 111 207
forceload remove -16 176 111 271
forceload remove 80 -16 207 111
forceload remove 80 80 207 207
forceload remove 80 176 207 271
forceload remove 176 -16 271 111
forceload remove 176 80 271 207
forceload remove 176 176 271 271
say [angel] cleared outskirts
scoreboard players operation #go angel_world = #rebuild angel_world
scoreboard players set #rebuild angel_world 0
execute if score #go angel_world matches 1 run function angel:world/outskirts/p0
