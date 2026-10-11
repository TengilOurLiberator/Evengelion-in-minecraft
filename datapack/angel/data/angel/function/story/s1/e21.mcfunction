scoreboard players set #force angel.story 0
execute positioned 228.5 63.0 128.5 rotated 90.0 0 run function angel:angel/summon {height:60}
summon minecraft:marker 228.5 93 128.5 {Tags:["angel.story","angel.cmark"],Rotation:[0f,0f]}
scoreboard players set #fx.t angel.story 0
scoreboard players set #c36 angel.story 36
scoreboard players set #fx.air angel.story 1
execute positioned 228.5 99.0 180.5 rotated 90.0 0.0 run function angel:story/rig/ac1/spawn_fly
execute positioned 170.5 108.0 128.5 rotated 180.0 0.0 run function angel:story/rig/ac2/spawn_fly
execute positioned 228.5 90.0 78.5 rotated 270.0 0.0 run function angel:story/rig/ac3/spawn_fly
execute positioned 284.5 103.0 128.5 rotated 360.0 0.0 run function angel:story/rig/ac4/spawn_fly
scoreboard players set #step angel.story 22
function angel:story/s1/e22
