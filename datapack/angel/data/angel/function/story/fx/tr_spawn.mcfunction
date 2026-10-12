summon minecraft:block_display ~ ~ ~ {Tags:["angel.story","angel.trc","angel.trnew"],block_state:"minecraft:yellow_concrete",brightness:{sky:15,block:15},view_range:8.0f,teleport_duration:1,transformation:{translation:[-0.3f,-0.3f,-3.5f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.6f,0.6f,7.0f],right_rotation:[0f,0f,0f,1f]}}
tp @e[tag=angel.trnew] ^ ^-1.2 ^7 ~ ~
tag @e[tag=angel.trnew] remove angel.trnew
particle minecraft:flame ^ ^-1.0 ^6 0.3 0.3 0.3 0.02 6 force
