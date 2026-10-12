data merge entity @e[tag=angel.larm_w,tag=angel.pt_wb,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-9.8f,0.0f,-1.6f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[2.6f,4.0f,3.2f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_w,tag=angel.pt_ws,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-9.8f,4.0f,-1.6f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[2.6f,0.2f,3.2f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_w,tag=angel.pt_wt,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-7.7f,-0.2f,-1.9f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.5f,4.4f,3.8f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_w,tag=angel.pt_wp,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-9.8f,1.2f,-0.45f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[2.6f,1.6f,0.9f],right_rotation:[0f,0f,0f,1f]}}
particle minecraft:electric_spark 3003.8 27.0 9.0 1.0 1.2 1.0 0.3 50 force
particle minecraft:dust_plume 3003.8 27.0 9.0 1.4 1.4 1.4 0.04 40 force
particle minecraft:explosion 3003.8 27.0 9.0 0.6 0.6 0.6 0 2 force
playsound angel:sfx.bolt_1 master @a 3003.8 27.0 9.0 3.0 1.0 0.8
particle minecraft:falling_dust{block_state:"minecraft:gray_concrete"} 3003.8 33.0 9.0 2.5 2 2.5 0 60 force
