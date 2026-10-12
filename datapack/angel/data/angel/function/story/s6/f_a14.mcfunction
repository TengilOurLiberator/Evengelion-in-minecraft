scoreboard players set #ride angel.story 0
ride @a[limit=1] dismount
kill @e[tag=angel.lseat]
summon minecraft:item_display 3096.5 61.78 63.2 {Tags:["angel.seat","angel.seat_passenger","angel.story","angel.launch","angel.lseat"],teleport_duration:0,item_display:"none"}
execute as @a[limit=1] if entity @s[y_rotation=-100..100] run tp @s 3096.5 61.18 63.2
execute as @a[limit=1] unless entity @s[y_rotation=-100..100] run tp @s 3096.5 61.18 63.2 0 0
ride @a[limit=1] mount @e[tag=angel.lseat,limit=1]
scoreboard players set #ride angel.story 1
summon minecraft:block_display 3095.0 61.3 61.7 {Tags:["angel.story","angel.launch","angel.lcock","angel.lcock_w"],block_state:"minecraft:white_concrete",teleport_duration:0,interpolation_duration:0,view_range:1.0f,brightness:{sky:13,block:13},transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0f,0f,0f,1f],scale:[0.03f,3.0f,3.0f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 3097.97 61.3 61.7 {Tags:["angel.story","angel.launch","angel.lcock","angel.lcock_e"],block_state:"minecraft:white_concrete",teleport_duration:0,interpolation_duration:0,view_range:1.0f,brightness:{sky:13,block:13},transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0f,0f,0f,1f],scale:[0.03f,3.0f,3.0f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 3095.0 61.3 61.7 {Tags:["angel.story","angel.launch","angel.lcock","angel.lcock_n"],block_state:"minecraft:white_concrete",teleport_duration:0,interpolation_duration:0,view_range:1.0f,brightness:{sky:13,block:13},transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0f,0f,0f,1f],scale:[3.0f,3.0f,0.03f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 3095.0 61.3 64.67 {Tags:["angel.story","angel.launch","angel.lcock","angel.lcock_s"],block_state:"minecraft:white_concrete",teleport_duration:0,interpolation_duration:0,view_range:1.0f,brightness:{sky:13,block:13},transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0f,0f,0f,1f],scale:[3.0f,3.0f,0.03f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 3095.0 61.3 61.7 {Tags:["angel.story","angel.launch","angel.lcock","angel.lcock_d"],block_state:"minecraft:white_concrete",teleport_duration:0,interpolation_duration:0,view_range:1.0f,brightness:{sky:13,block:13},transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0f,0f,0f,1f],scale:[3.0f,0.03f,3.0f],right_rotation:[0f,0f,0f,1f]}}
summon minecraft:block_display 3095.0 64.27 61.7 {Tags:["angel.story","angel.launch","angel.lcock","angel.lcock_u"],block_state:"minecraft:white_concrete",teleport_duration:0,interpolation_duration:0,view_range:1.0f,brightness:{sky:13,block:13},transformation:{translation:[0.0f,0.0f,0.0f],left_rotation:[0f,0f,0f,1f],scale:[3.0f,0.03f,3.0f],right_rotation:[0f,0f,0f,1f]}}
kill @e[tag=angel.lfluid]
kill @e[tag=angel.lmen]
