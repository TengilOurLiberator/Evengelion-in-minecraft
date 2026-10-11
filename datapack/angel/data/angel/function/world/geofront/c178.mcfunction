forceload remove 1984 -16 2111 111
forceload remove 1984 80 2111 207
forceload remove 1984 176 2111 303
forceload remove 1984 272 2111 335
forceload remove 2080 -16 2207 111
forceload remove 2080 80 2207 207
forceload remove 2080 176 2207 303
forceload remove 2080 272 2207 335
forceload remove 2176 -16 2303 111
forceload remove 2176 80 2303 207
forceload remove 2176 176 2303 303
forceload remove 2176 272 2303 335
forceload remove 2272 -16 2335 111
forceload remove 2272 80 2335 207
forceload remove 2272 176 2335 303
forceload remove 2272 272 2335 335
say [angel] cleared geofront
scoreboard players operation #go angel_world = #rebuild angel_world
scoreboard players set #rebuild angel_world 0
execute if score #go angel_world matches 1 run function angel:world/geofront/p0
