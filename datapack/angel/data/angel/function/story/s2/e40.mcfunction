scoreboard players set #force angel.story 0
function angel:story/snd/silence
execute at @a[limit=1] run playsound angel:sfx.mine master @a ~ ~ ~ 4.0 1.0 1.0
execute at @a[limit=1] anchored eyes positioned ^ ^ ^ run function angel:story/s2/whiteout
execute at @a[limit=1] anchored eyes positioned ^ ^ ^0.4 run particle minecraft:flash{color:[1.0,1.0,1.0,1.0]} ~ ~ ~ 0 0 0 0 1 force
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb0"],block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,50.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb1"],block_state:"minecraft:yellow_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,50.0f,0.0f],left_rotation:[0.0f,0.38268f,0.0f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb2"],block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,50.0f,0.0f],left_rotation:[0.38268f,0.0f,0.0f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb3"],block_state:"minecraft:yellow_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,50.0f,0.0f],left_rotation:[0.0f,0.0f,0.38268f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_stem"],block_state:"minecraft:gray_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[-3.33333f,0.0f,-3.33333f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[6.66667f,0.05f,6.66667f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_capA"],block_state:"minecraft:white_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,50.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_capB"],block_state:"minecraft:light_gray_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,50.0f,0.0f],left_rotation:[0.0f,0.38268f,0.0f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_skirt"],block_state:"minecraft:gray_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,50.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
schedule function angel:story/fx/cloud_1 3t
schedule function angel:story/fx/cloud_2 40t
scoreboard players set #fx.air angel.story 0
kill @e[tag=angel.cmark]
kill @e[tag=angel.rig_ac1]
kill @e[tag=angel.rig_ac2]
kill @e[tag=angel.rig_ac3]
kill @e[tag=angel.rig_ac4]
kill @e[tag=angel.rig_ac5]
kill @e[tag=angel.rig_ac3d]
kill @e[tag=angel.trc]
kill @e[tag=angel.flash]
kill @e[tag=angel.lvtmp]
scoreboard players set #fx.leave angel.story 0
scoreboard players set #step angel.story 41
function angel:story/s2/e41
