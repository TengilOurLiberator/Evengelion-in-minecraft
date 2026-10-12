scoreboard players set #bp angel_world 0
execute in minecraft:overworld if biome 1000 112 0 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1000 112 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1000 112 319 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 112 0 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 112 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 112 319 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1319 112 0 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1319 112 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1319 112 319 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 940 36 -60 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1380 188 380 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 940 112 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 292 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 -60 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 64 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 33 160 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 64 50 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 64 76 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 64 100 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1160 64 122 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1200 64 137 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1207 86 137 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1133 64 133 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1123 64 123 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1133 64 187 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1123 64 197 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1187 64 133 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1197 64 123 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1187 64 187 angel:city run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1197 64 197 angel:city run scoreboard players add #bp angel_world 1
execute if score #bp angel_world matches 30 run say [angel] biome city: all 30 probes found angel:city
execute unless score #bp angel_world matches 30 run say [angel] BIOME CHECK FAILED for city: fewer than 30 probes found angel:city
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
forceload remove 936 -64 1151 159
forceload remove 936 160 1151 383
forceload remove 1152 -64 1375 159
forceload remove 1152 160 1375 383
forceload remove 1376 -64 1383 159
forceload remove 1376 160 1383 383
say [angel] placed city: 132 tiles, 854630 blocks
execute if score #all angel_world matches 1 run function angel:world/geofront/p0
