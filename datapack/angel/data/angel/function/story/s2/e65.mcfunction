scoreboard players set #force angel.story 0
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorL,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[1.85f,0.15f,-1.5f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.15f,0.85f,2.0f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorGlass,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[1.9f,1.0f,-1.4f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.1f,0.9f,1.8f],right_rotation:[0f,0f,0f,1f]}}
playsound angel:sfx.car_door master @a 179.101 84.0 58.765 1.2 1.0 0.0
scoreboard players set #step angel.story 66
function angel:story/s2/e66
