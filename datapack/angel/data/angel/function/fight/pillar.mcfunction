# the Angel's end: a tall cross of light where it stood (bars at a high crossing)
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:white_concrete",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-2.500f,-65.000f,-2.500f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[5.000f,190.000f,5.000f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:white_concrete",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-30.000f,27.500f,-2.500f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[60.000f,5.000f,5.000f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:white_concrete",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-2.500f,27.500f,-30.000f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[5.000f,5.000f,60.000f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:light_blue_stained_glass",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-4.500f,-65.000f,-4.500f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[9.000f,190.000f,9.000f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:light_blue_stained_glass",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-30.000f,25.500f,-4.500f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[60.000f,9.000f,9.000f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.fight","angel.flash","angel.wnew"],block_state:"minecraft:light_blue_stained_glass",view_range:16f,interpolation_duration:0,brightness:{block:15,sky:15},transformation:{translation:[-4.500f,25.500f,-30.000f],left_rotation:[0f,0f,0.0000f,1.0000f],scale:[9.000f,9.000f,60.000f],right_rotation:[0f,0f,0f,1f]}}
tag @e[tag=angel.wnew] remove angel.wnew
particle minecraft:flash{color:[1.0,1.0,1.0,1.0]} ~ ~10 ~ 0 0 0 0 1 force
particle minecraft:end_rod ~ ~ ~ 4 40 4 0.3 200 force
particle minecraft:explosion_emitter ~ ~12 ~ 5 5 5 0 6 force
playsound minecraft:entity.lightning_bolt.thunder hostile @a ~ ~ ~ 12 0.6
playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 12 0.5
playsound minecraft:entity.wither.death hostile @a ~ ~ ~ 12 0.6
schedule function angel:fight/fx_fade 90t
schedule function angel:fight/fx_clear 112t
