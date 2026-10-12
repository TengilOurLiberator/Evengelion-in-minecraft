data merge entity @e[tag=angel.larm_n,tag=angel.pt_nb,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-1.6f,0.0f,-9.8f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.2f,4.0f,2.6f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_n,tag=angel.pt_ns,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-1.6f,4.0f,-9.8f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.2f,0.2f,2.6f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_n,tag=angel.pt_nt,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-1.9f,-0.2f,-7.7f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.8f,4.4f,0.5f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_n,tag=angel.pt_np,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-0.45f,1.2f,-9.8f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.9f,1.6f,2.6f],right_rotation:[0f,0f,0f,1f]}}
particle minecraft:electric_spark 3009.0 27.0 3.8 1.0 1.2 1.0 0.3 50 force
particle minecraft:dust_plume 3009.0 27.0 3.8 1.4 1.4 1.4 0.04 40 force
particle minecraft:explosion 3009.0 27.0 3.8 0.6 0.6 0.6 0 2 force
playsound angel:sfx.bolt_3 master @a 3009.0 27.0 3.8 3.0 0.88 0.8
particle minecraft:falling_dust{block_state:"minecraft:gray_concrete"} 3009.0 33.0 3.8 2.5 2 2.5 0 60 force
