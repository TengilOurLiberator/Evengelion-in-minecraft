execute at @a[limit=1] run playsound angel:sfx.speak_chime master @a ~ ~ ~ 0.6 1.0 0.5
data merge entity @e[tag=angel.prompt_main,limit=1] {start_interpolation:0,interpolation_duration:4,transformation:{translation:[0f,0f,0f],left_rotation:[0f,0f,0f,1f],scale:[0.7936f,0.7936f,0.7936f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.prompt_sub,limit=1] {start_interpolation:0,interpolation_duration:4,transformation:{translation:[0f,-0.2688f,0f],left_rotation:[0f,0f,0f,1f],scale:[0.512f,0.512f,0.512f],right_rotation:[0f,0f,0f,1f]}}
schedule function angel:story/prompt/pulse_back 5t
