summon minecraft:block_display ~ ~ ~ {Tags:["angel.story","angel.flash"],block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15},view_range:8.0f,interpolation_duration:4,transformation:{translation:[-0.4f,-0.4f,-0.4f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.8f,0.8f,0.8f],right_rotation:[0f,0f,0f,1f]}}
particle minecraft:explosion ~ ~ ~ 1.5 1.5 1.5 0 3 force
particle minecraft:flash{color:[1.0,0.85,0.5,1.0]} ~ ~ ~ 0 0 0 0 1 force
kill @s
