data merge entity @e[tag=angel.larm_e,tag=angel.pt_eb,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[7.2f,0.0f,-1.6f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[2.6f,4.0f,3.2f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_e,tag=angel.pt_es,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[7.2f,4.0f,-1.6f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[2.6f,0.2f,3.2f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_e,tag=angel.pt_et,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[7.2f,-0.2f,-1.9f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.5f,4.4f,3.8f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_e,tag=angel.pt_ep,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[7.2f,1.2f,-0.45f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[2.6f,1.6f,0.9f],right_rotation:[0f,0f,0f,1f]}}
particle minecraft:electric_spark 3014.2 27.0 9.0 1.0 1.2 1.0 0.3 50 force
particle minecraft:dust_plume 3014.2 27.0 9.0 1.4 1.4 1.4 0.04 40 force
particle minecraft:explosion 3014.2 27.0 9.0 0.6 0.6 0.6 0 2 force
playsound angel:sfx.bolt_2 master @a 3014.2 27.0 9.0 3.0 0.94 0.8
particle minecraft:falling_dust{block_state:"minecraft:gray_concrete"} 3014.2 33.0 9.0 2.5 2 2.5 0 60 force
