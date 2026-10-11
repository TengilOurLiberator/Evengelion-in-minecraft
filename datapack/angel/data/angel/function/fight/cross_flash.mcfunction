# a cross-shaped flash at the current position
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:white_concrete",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-0.650f,-17.000f,-0.650f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[1.300f,34.000f,1.300f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:white_concrete",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-8.000f,-0.650f,-0.650f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[16.000f,1.300f,1.300f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:white_concrete",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-0.650f,-0.650f,-8.000f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[1.300f,1.300f,16.000f],right_rotation:[0f,0f,0f,1f]}}
tag @e[tag=angel.wnew] remove angel.wnew
particle minecraft:flash{color:[1.0,1.0,1.0,1.0]} ~ ~ ~ 0 0 0 0 1 force
particle minecraft:end_rod ~ ~ ~ 3 6 3 0.25 40 force
playsound minecraft:entity.lightning_bolt.impact hostile @a ~ ~ ~ 6 1.4
playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 6 0.7
schedule function angel:fight/fx_fade 4t
schedule function angel:fight/fx_clear 16t
