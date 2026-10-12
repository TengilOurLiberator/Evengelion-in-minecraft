scoreboard players set #fx.fall angel.story 0
scoreboard players set #fx.wreck angel.story 1
scoreboard players set #f.crash angel.story 1
kill @e[tag=angel.rig_ac3d]
particle minecraft:explosion_emitter 84.5 65.5 142.5 0 0 0 0 1 force
particle minecraft:flash{color:[1.0,0.7,0.3,1.0]} 84.5 67.5 142.5 0 0 0 0 1 force
particle minecraft:lava 84.5 65.5 142.5 3 2 3 0.1 50 force
particle minecraft:flame 84.5 65.5 142.5 4 2 4 0.1 120 force
particle minecraft:large_smoke 84.5 67.5 142.5 3 3 3 0.08 120 force
particle minecraft:block{block_state:"minecraft:gray_concrete"} 84.5 65.5 142.5 4 1 4 0.5 80 force
playsound angel:sfx.explosion_near master @a 84.5 64.5 142.5 0.8 1.0 0.0
summon minecraft:block_display 84.5 64.5 142.5 {Tags:["angel.wreck","angel.story"],block_state:"minecraft:gray_concrete",teleport_duration:0,view_range:2.0f,transformation:{translation:[-1.8f,0.0f,-0.5f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.6f,0.9f,1.4f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.5 64.5 142.5 {Tags:["angel.wreck","angel.story"],block_state:"minecraft:black_concrete",teleport_duration:0,view_range:2.0f,transformation:{translation:[-1.22182f,0.0f,1.9254f],left_rotation:[0.0f,0.98883f,0.0f,0.14905f],scale:[1.5f,0.5f,2.5f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.5 64.5 142.5 {Tags:["angel.wreck","angel.story"],block_state:"minecraft:light_gray_concrete",teleport_duration:0,view_range:2.0f,transformation:{translation:[2.72287f,0.0f,-2.36346f],left_rotation:[0.0f,0.98242f,0.0f,-0.18668f],scale:[1.6f,0.35f,1.5f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.5 64.5 142.5 {Tags:["angel.wreck","angel.story"],block_state:"minecraft:black_concrete",teleport_duration:0,view_range:2.0f,transformation:{translation:[1.54267f,0.0f,1.80836f],left_rotation:[0.0f,0.23586f,0.0f,-0.97179f],scale:[0.8f,1.1f,0.8f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.5 64.5 142.5 {Tags:["angel.wreck","angel.story"],block_state:"minecraft:gray_concrete",teleport_duration:0,view_range:2.0f,transformation:{translation:[0.73337f,0.0f,-1.47722f],left_rotation:[0.0f,0.99418f,0.0f,0.1077f],scale:[1.1f,0.4f,1.6f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.5 64.5 142.5 {Tags:["angel.wreck","angel.story"],block_state:"minecraft:orange_concrete",teleport_duration:0,view_range:2.0f,transformation:{translation:[1.06773f,0.1f,1.34905f],left_rotation:[0.0f,0.9997f,0.0f,-0.02463f],scale:[1.2f,0.4f,1.2f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.225 64.8 140.131 {Tags:["angel.story","angel.wreck"],block_state:{id:"minecraft:fire"},brightness:{sky:15,block:15},view_range:1.5f,transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[1.45834f,1.45834f,1.45834f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.592 64.8 143.441 {Tags:["angel.story","angel.wreck"],block_state:{id:"minecraft:fire"},brightness:{sky:15,block:15},view_range:1.5f,transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[1.16589f,1.16589f,1.16589f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 82.644 64.8 139.538 {Tags:["angel.story","angel.wreck"],block_state:{id:"minecraft:fire"},brightness:{sky:15,block:15},view_range:1.5f,transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[1.66675f,1.66675f,1.66675f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 84.612 64.8 139.224 {Tags:["angel.story","angel.wreck"],block_state:{id:"minecraft:fire"},brightness:{sky:15,block:15},view_range:1.5f,transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[1.78754f,1.78754f,1.78754f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 86.151 64.8 142.535 {Tags:["angel.story","angel.wreck"],block_state:{id:"minecraft:fire"},brightness:{sky:15,block:15},view_range:1.5f,transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[1.53089f,1.53089f,1.53089f],right_rotation:[0f,0f,0f,1f]}}
