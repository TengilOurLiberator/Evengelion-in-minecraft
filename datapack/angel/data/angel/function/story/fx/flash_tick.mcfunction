execute as @e[tag=angel.flash,tag=!angel.big] run data merge entity @s {start_interpolation:0,interpolation_duration:5,transformation:{translation:[-3.0f,-3.0f,-3.0f],left_rotation:[0.0f,0.0f,0.0f,1.0f],scale:[6.0f,6.0f,6.0f],right_rotation:[0f,0f,0f,1f]}}
tag @e[tag=angel.flash,tag=!angel.big] add angel.big
scoreboard players add @e[tag=angel.flash] angel.story 1
kill @e[tag=angel.flash,scores={angel.story=7..}]
