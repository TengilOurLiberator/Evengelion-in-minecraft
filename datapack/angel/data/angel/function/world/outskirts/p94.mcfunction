scoreboard players set #bp angel_world 0
execute in minecraft:overworld if biome 0 96 0 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 0 96 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 0 96 255 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 128 96 0 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 128 96 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 128 96 255 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 255 96 0 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 255 96 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 255 96 255 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome -60 36 -60 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 316 156 316 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome -60 96 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 128 260 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 128 -60 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 37 65 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 65 65 113 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 65 64 115 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 93 64 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 133 64 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 84 64 142 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 97 64 131 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 97 64 130 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 194 82 56 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 179 83 56 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 228 63 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 212 63 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 196 63 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 184 64 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 174 64 128 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 190 76 31 angel:outskirts run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 191 76 15 angel:outskirts run scoreboard players add #bp angel_world 1
execute if score #bp angel_world matches 31 run say [angel] biome outskirts: all 31 probes found angel:outskirts
execute unless score #bp angel_world matches 31 run say [angel] BIOME CHECK FAILED for outskirts: fewer than 31 probes found angel:outskirts
execute in minecraft:overworld run data merge block 55 68 126 {front_text:{messages:["\u6f6e\u898b\u99c5","SHIOMI STATION","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 55 68 130 {front_text:{messages:["\u6f6e\u898b\u99c5","SHIOMI STATION","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 48 68 128 {front_text:{messages:["\u6539\u672d\u53e3","TICKET GATES","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 46 68 128 {front_text:{messages:["\u6539\u672d\u53e3","TICKET GATES","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 40 66 116 {front_text:{messages:["\u6642\u523b\u8868","TIMETABLE","ALL SERVICES","SUSPENDED"],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 37 68 84 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 34 68 84 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 37 68 112 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 34 68 112 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 37 68 144 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 34 68 144 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 37 68 176 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 34 68 176 {front_text:{messages:["\u6f6e\u898b","SHIOMI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 41 67 120 {front_text:{messages:["\u907f\u96e3\u547d\u4ee4","ALL TRAINS","SUSPENDED",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 190 84 46 {front_text:{messages:["\u5c55\u671b\u53f0","LOOKOUT","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 178 82 20 {front_text:{messages:["\u30ab\u30fc\u30c8\u30ec\u30a4\u30f3","CAR TRAIN","PLATFORM 1",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 202 82 20 {front_text:{messages:["\u30ab\u30fc\u30c8\u30ec\u30a4\u30f3","CAR TRAIN","PLATFORM 1",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 190 87 23 {front_text:{messages:["NO ENTRY","\u7acb\u5165\u7981\u6b62","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 171 80 12 {front_text:{messages:["\u7ba1\u5236\u5ba4","CONTROL","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 100 66 119 {front_text:{messages:["\u4e2d\u83ef","RAMEN","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 132 66 119 {front_text:{messages:["\u30d1\u30f3","BAKERY","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 164 66 119 {front_text:{messages:["\u6642\u8a08","WATCH","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 100 66 137 {front_text:{messages:["\u30d1\u30f3","BAKERY","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 130 66 137 {front_text:{messages:["\u7530\u4e2d","TANAKA","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 140 66 137 {front_text:{messages:["\u85ac","DRUGS","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 146 66 137 {front_text:{messages:["\u7530\u4e2d","TANAKA","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 156 66 137 {front_text:{messages:["\u3086","BATH","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 165 66 137 {front_text:{messages:["\u7406\u5bb9","BARBER","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 64 66 98 {front_text:{messages:["\u7406\u5bb9","BARBER","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 72 66 98 {front_text:{messages:["\u6642\u8a08","WATCH","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 85 66 98 {front_text:{messages:["\u30d1\u30f3","BAKERY","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 65 66 158 {front_text:{messages:["\u55ab\u8336","CAFE","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 76 66 158 {front_text:{messages:["\u6642\u8a08","WATCH","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 85 66 158 {front_text:{messages:["\u9774","SHOES","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 55 66 101 {front_text:{messages:["\u907f\u96e3\u547d\u4ee4","EVACUATION","ORDER",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 56 65 101 {front_text:{messages:["\u7279\u5225\u975e\u5e38\u4e8b\u614b\u5ba3\u8a00","STATE OF","EMERGENCY",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 78 66 101 {front_text:{messages:["\u907f\u96e3\u547d\u4ee4","EVACUATION","ORDER",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 79 65 101 {front_text:{messages:["\u7279\u5225\u975e\u5e38\u4e8b\u614b\u5ba3\u8a00","STATE OF","EMERGENCY",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 140 66 135 {front_text:{messages:["\u907f\u96e3\u547d\u4ee4","EVACUATION","ORDER",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 139 65 135 {front_text:{messages:["\u7279\u5225\u975e\u5e38\u4e8b\u614b\u5ba3\u8a00","STATE OF","EMERGENCY",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 76 66 157 {front_text:{messages:["\u907f\u96e3\u547d\u4ee4","EVACUATION","ORDER",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 75 65 157 {front_text:{messages:["\u7279\u5225\u975e\u5e38\u4e8b\u614b\u5ba3\u8a00","STATE OF","EMERGENCY",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 162 66 121 {front_text:{messages:["\u907f\u96e3\u547d\u4ee4","EVACUATION","ORDER",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 163 65 121 {front_text:{messages:["\u7279\u5225\u975e\u5e38\u4e8b\u614b\u5ba3\u8a00","STATE OF","EMERGENCY",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 65 69 116 {front_text:{messages:["\u516c\u8846\u96fb\u8a71","PUBLIC","TELEPHONE",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 63 69 116 {front_text:{messages:["\u516c\u8846\u96fb\u8a71","PUBLIC","TELEPHONE",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 67 66 140 {front_text:{messages:["\u4e2d\u83ef","RAMEN","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 68 70 115 {front_text:{messages:["\u30bf\u30af\u30b7\u30fc","TAXI","",""],color:"black"},is_waxed:1b}
execute in minecraft:overworld run data merge block 68 70 113 {front_text:{messages:["\u30bf\u30af\u30b7\u30fc","TAXI","",""],color:"black"},is_waxed:1b}
forceload remove -16 -16 111 111
forceload remove -16 80 111 207
forceload remove -16 176 111 271
forceload remove 80 -16 207 111
forceload remove 80 80 207 207
forceload remove 80 176 207 271
forceload remove 176 -16 271 111
forceload remove 176 80 271 207
forceload remove 176 176 271 271
forceload remove -64 -64 159 159
forceload remove -64 160 159 319
forceload remove 160 -64 319 159
forceload remove 160 160 319 319
say [angel] placed outskirts: 83 tiles, 3516997 blocks
execute if score #all angel_world matches 1 run function angel:world/city/p0
