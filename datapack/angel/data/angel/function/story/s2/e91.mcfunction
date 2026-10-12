scoreboard players set #force angel.story 0
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorL,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[1.382f,0.481f,-0.17f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[1.0f,1.0f,1.0f],right_rotation:[0f,0f,0f,1f]}}
playsound angel:sfx.car_door master @a 179.118 84.0 58.667 1.2 1.0 0.0
scoreboard players set #step angel.story 92
function angel:story/s2/e92
