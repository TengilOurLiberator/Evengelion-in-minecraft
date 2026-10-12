data merge entity @e[tag=angel.larm_s,tag=angel.pt_sb,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-1.6f,0.0f,7.2f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.2f,4.0f,2.6f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_s,tag=angel.pt_ss,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-1.6f,4.0f,7.2f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.2f,0.2f,2.6f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_s,tag=angel.pt_st,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-1.9f,-0.2f,7.2f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[3.8f,4.4f,0.5f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.larm_s,tag=angel.pt_sp,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[-0.45f,1.2f,7.2f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[0.9f,1.6f,2.6f],right_rotation:[0f,0f,0f,1f]}}
particle minecraft:electric_spark 3009.0 27.0 14.2 1.0 1.2 1.0 0.3 50 force
particle minecraft:dust_plume 3009.0 27.0 14.2 1.4 1.4 1.4 0.04 40 force
particle minecraft:explosion 3009.0 27.0 14.2 0.6 0.6 0.6 0 2 force
playsound angel:sfx.bolt_1 master @a 3009.0 27.0 14.2 3.0 0.82 0.8
particle minecraft:falling_dust{block_state:"minecraft:gray_concrete"} 3009.0 33.0 14.2 2.5 2 2.5 0 60 force
