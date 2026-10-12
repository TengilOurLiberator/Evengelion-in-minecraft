execute unless score #f.beacon angel.story matches 1 run return 0
scoreboard players add #l.bk angel.story 1
execute if score #l.bk angel.story matches 6.. run scoreboard players set #l.bk angel.story 0
execute if score #l.bk angel.story matches 0 as @e[tag=angel.lbeam] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-1.8f,-0.07f,-0.07f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.6f,0.14f,0.14f],right_rotation:[0f,0f,0f,1f]}}
execute if score #l.bk angel.story matches 1 as @e[tag=angel.lbeam] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.96062f,-0.07f,1.52385f],left_rotation:[0.0f,0.5f,0.0f,0.86603f],scale:[3.6f,0.14f,0.14f],right_rotation:[0f,0f,0f,1f]}}
execute if score #l.bk angel.story matches 2 as @e[tag=angel.lbeam] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[0.83938f,-0.07f,1.59385f],left_rotation:[0.0f,0.86603f,0.0f,0.5f],scale:[3.6f,0.14f,0.14f],right_rotation:[0f,0f,0f,1f]}}
execute if score #l.bk angel.story matches 3 as @e[tag=angel.lbeam] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[1.8f,-0.07f,0.07f],left_rotation:[0.0f,1.0f,0.0f,0.0f],scale:[3.6f,0.14f,0.14f],right_rotation:[0f,0f,0f,1f]}}
execute if score #l.bk angel.story matches 4 as @e[tag=angel.lbeam] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[0.96062f,-0.07f,-1.52385f],left_rotation:[0.0f,0.86603f,0.0f,-0.5f],scale:[3.6f,0.14f,0.14f],right_rotation:[0f,0f,0f,1f]}}
execute if score #l.bk angel.story matches 5 as @e[tag=angel.lbeam] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-0.83938f,-0.07f,-1.59385f],left_rotation:[0.0f,0.5f,0.0f,-0.86603f],scale:[3.6f,0.14f,0.14f],right_rotation:[0f,0f,0f,1f]}}
schedule function angel:story/launch/beacon_step 5t
