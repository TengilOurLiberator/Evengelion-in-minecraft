scoreboard players set #bp angel_world 0
execute in minecraft:overworld if biome 2000 72 0 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2000 72 160 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2000 72 319 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2160 72 0 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2160 72 160 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2160 72 319 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2319 72 0 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2319 72 160 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2319 72 319 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1940 4 -60 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2380 140 380 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 1940 72 160 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2160 244 160 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2160 -60 160 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2025 98 101 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2035 98 91 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2045 98 82 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2055 98 72 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2065 98 62 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2075 97 52 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2084 94 42 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2095 91 34 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2106 87 27 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2118 84 20 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2131 81 16 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2144 77 12 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2157 74 10 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2171 70 10 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2185 67 12 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2198 64 15 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2211 60 19 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2223 57 24 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2235 53 30 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2247 50 38 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2258 47 46 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2267 43 55 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2276 40 65 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2284 36 76 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2291 33 88 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2297 30 100 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2302 26 113 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2306 23 126 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2308 19 139 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2059 98 67 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2063 98 63 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2309 19 154 angel:geofront run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2298 18 150 angel:geofront run scoreboard players add #bp angel_world 1
execute if score #bp angel_world matches 47 run say [angel] biome geofront: all 47 probes found angel:geofront
execute unless score #bp angel_world matches 47 run say [angel] BIOME CHECK FAILED for geofront: fewer than 47 probes found angel:geofront
execute in minecraft:overworld run data merge block 2025 100 107 {front_text:{messages:["GEOFRONT LINE 1","SECTION 01","TO TERMINAL","NO ENTRY BEYOND"],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 2028 100 93 {front_text:{messages:["GEOFRONT LINE 1","SECTION 02","TO TERMINAL","NO ENTRY BEYOND"],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 2042 100 90 {front_text:{messages:["GEOFRONT LINE 1","SECTION 03","TO TERMINAL","NO ENTRY BEYOND"],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 2045 100 76 {front_text:{messages:["GEOFRONT LINE 1","SECTION 04","TO TERMINAL","NO ENTRY BEYOND"],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 2059 100 73 {front_text:{messages:["GEOFRONT LINE 1","SECTION 05","TO TERMINAL","NO ENTRY BEYOND"],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 2099 91 26 {front_text:{messages:["GEOFRONT LINE 1","SECTION 10","TO TERMINAL","MIND THE EDGE"],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 2133 82 11 {front_text:{messages:["GEOFRONT LINE 1","SECTION 13","TO TERMINAL","MIND THE EDGE"],color:"black"},is_waxed:1b}
forceload remove 1998 -2 2111 111
forceload remove 1985 80 2111 207
forceload remove 1988 176 2111 303
forceload remove 2050 272 2111 321
forceload remove 2080 -15 2207 111
forceload remove 2080 80 2207 207
forceload remove 2080 176 2207 303
forceload remove 2080 272 2207 334
forceload remove 2176 -12 2303 111
forceload remove 2176 80 2303 207
forceload remove 2176 176 2303 303
forceload remove 2176 272 2269 331
forceload remove 2272 50 2321 111
forceload remove 2272 80 2334 207
forceload remove 2272 176 2331 269
forceload remove 1936 -64 2159 159
forceload remove 1936 160 2159 383
forceload remove 2160 -64 2383 159
forceload remove 2160 160 2383 383
say [angel] placed geofront: 132 tiles, 3070837 blocks
execute if score #all angel_world matches 1 run function angel:world/hq/p0
