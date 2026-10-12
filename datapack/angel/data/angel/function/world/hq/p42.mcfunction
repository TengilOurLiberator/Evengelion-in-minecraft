scoreboard players set #bp angel_world 0
execute in minecraft:overworld if biome 3000 80 0 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3000 80 96 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3000 80 191 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 80 0 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 80 96 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 80 191 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3191 80 0 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3191 80 96 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3191 80 191 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2940 4 -60 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3252 156 252 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 2940 80 96 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 260 96 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 -60 96 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3015 54 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3060 54 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 54 145 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3103 57 62 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3009 107 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3005 107 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3180 131 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3160 131 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3136 131 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3116 131 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3109 131 154 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3097 131 165 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3085 131 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3026 107 160 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3030 12 11 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3009 4 9 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3009 150 9 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3003 149 9 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 54 135 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 54 72 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3094 54 76 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3098 54 76 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3062 54 80 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 54 80 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 54 78 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 105 73 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 105 78 angel:hq run scoreboard players add #bp angel_world 1
execute in minecraft:overworld if biome 3096 105 84 angel:hq run scoreboard players add #bp angel_world 1
execute if score #bp angel_world matches 42 run say [angel] biome hq: all 42 probes found angel:hq
execute unless score #bp angel_world matches 42 run say [angel] BIOME CHECK FAILED for hq: fewer than 42 probes found angel:hq
forceload remove 2984 -16 3111 111
forceload remove 2984 80 3111 204
forceload remove 3080 4 3148 111
forceload remove 3080 80 3201 204
forceload remove 2936 -64 3151 159
forceload remove 2936 160 3151 255
forceload remove 3152 -64 3255 159
forceload remove 3152 160 3255 255
say [angel] placed hq: 40 tiles, 733391 blocks
scoreboard players set #all angel_world 0
say [angel] every set is placed
