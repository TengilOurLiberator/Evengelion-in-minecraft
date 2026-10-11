forceload remove 984 -16 1111 111
forceload remove 984 80 1111 207
forceload remove 984 176 1111 303
forceload remove 984 272 1111 335
forceload remove 1080 -16 1207 111
forceload remove 1080 80 1207 207
forceload remove 1080 176 1207 303
forceload remove 1080 272 1207 335
forceload remove 1176 -16 1303 111
forceload remove 1176 80 1303 207
forceload remove 1176 176 1303 303
forceload remove 1176 272 1303 335
forceload remove 1272 -16 1335 111
forceload remove 1272 80 1335 207
forceload remove 1272 176 1335 303
forceload remove 1272 272 1335 335
say [angel] cleared city
scoreboard players operation #go angel_world = #rebuild angel_world
scoreboard players set #rebuild angel_world 0
execute if score #go angel_world matches 1 run function angel:world/city/p0
