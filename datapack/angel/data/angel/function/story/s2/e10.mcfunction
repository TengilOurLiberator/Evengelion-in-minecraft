scoreboard players set #force angel.story 0
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorL,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[1.22f,0.14f,-1.2f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.28f,0.58f,2.06f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.rig_car,tag=angel.pt_coamingL,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[1.2f,0.72f,-1.2f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.32f,0.02f,2.06f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.rig_car,tag=angel.pt_handleL,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[1.5f,0.56f,-0.7f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.07f,0.08f,0.3f],right_rotation:[0f,0f,0f,1f]}}
playsound angel:sfx.car_door master @a 97.5 65.0 128.8 1.2 1.0 0.0
function angel:cast/look {id:"misato",mode:"ahead"}
execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_car,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
scoreboard players set #step angel.story 11
function angel:story/s2/e11
