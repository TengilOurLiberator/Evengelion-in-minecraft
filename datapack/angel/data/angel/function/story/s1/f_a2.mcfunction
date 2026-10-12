execute positioned 228.5 63.0 128.5 rotated 90.0 0 run function angel:angel/summon {height:100}
summon minecraft:marker 228.5 118.0 128.5 {Tags:["angel.story","angel.cmark"],Rotation:[0f,0f]}
scoreboard players set #fx.t angel.story 0
scoreboard players set #c36 angel.story 36
scoreboard players set #fx.air angel.story 1
execute positioned 228.5 84.0 178.5 rotated 90.0 0.0 run function angel:story/rig/ac1/spawn_fly
execute positioned 173.339 106.0 146.423 rotated 162.0 0.0 run function angel:story/rig/ac2/spawn_fly
execute positioned 196.76 124.0 84.813 rotated 234.0 0.0 run function angel:story/rig/ac3/spawn_fly
execute positioned 264.943 140.0 78.341 rotated 306.0 0.0 run function angel:story/rig/ac4/spawn_fly
execute positioned 274.151 96.0 143.333 rotated 378.0 0.0 run function angel:story/rig/ac5/spawn_fly
