scoreboard players set #ride angel.story 0
ride @a[limit=1] dismount
function angel:cast/remove {id:"misato"}
kill @e[tag=angel.rig_car]
execute positioned 179.5 83.0 56.5 rotated 100.0 0.0 run function angel:story/rig/car/spawn_side
tp @a[limit=1] 181.503 82.5 49.745
execute positioned 179.14 82.5 49.329 rotated -2.88 0 run function angel:cast/summon {id:"misato"}
function angel:cast/look {id:"misato",mode:"player"}
scoreboard players set #beat angel.story 21
function angel:angel/pose {pose:"regenerating"}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb0"],block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,30.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb1"],block_state:"minecraft:yellow_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,30.0f,0.0f],left_rotation:[0.0f,0.38268f,0.0f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb2"],block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,30.0f,0.0f],left_rotation:[0.38268f,0.0f,0.0f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_fb3"],block_state:"minecraft:yellow_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,30.0f,0.0f],left_rotation:[0.0f,0.0f,0.38268f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_stem"],block_state:"minecraft:gray_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[-2.0f,0.0f,-2.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[4.0f,0.05f,4.0f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_capA"],block_state:"minecraft:white_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,30.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_capB"],block_state:"minecraft:light_gray_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,30.0f,0.0f],left_rotation:[0.0f,0.38268f,0.0f,0.92388f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 174.5 64.0 128.5 {Tags:["angel.story","angel.cloud","angel.cl_skirt"],block_state:"minecraft:gray_concrete",brightness:{sky:15,block:15},view_range:16.0f,interpolation_duration:20,transformation:{translation:[0.0f,30.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.05f,0.05f,0.05f],right_rotation:[0f,0f,0f,1f]}}
schedule function angel:story/fx/cloud_1 3t
schedule function angel:story/fx/cloud_2 40t
summon minecraft:interaction 180.021 83.0 53.546 {Tags:["angel.story","angel.ia_push"],width:7.4f,height:4.4f,response:1b}
