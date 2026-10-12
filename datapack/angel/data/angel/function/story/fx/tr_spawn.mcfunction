summon minecraft:block_display ~ ~ ~ {Tags:["angel.story","angel.trc","angel.trnew"],block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15},view_range:8.0f,teleport_duration:1,transformation:{translation:[-0.65f,-0.65f,-5.5f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[1.3f,1.3f,11.0f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display ~ ~ ~ {Tags:["angel.story","angel.trc","angel.trnew"],block_state:"minecraft:white_concrete",brightness:{sky:15,block:15},view_range:8.0f,teleport_duration:1,transformation:{translation:[-0.3f,-0.3f,-5.6f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.6f,0.6f,11.2f],right_rotation:[0f,0f,0f,1f]}}
tp @e[tag=angel.trnew] ^ ^-1.2 ^7 ~ ~
tag @e[tag=angel.trnew] remove angel.trnew
particle minecraft:flame ^ ^-1.0 ^6 0.5 0.5 0.5 0.03 12 force
particle minecraft:large_smoke ^ ^-1.0 ^6 0.5 0.5 0.5 0.02 6 force
