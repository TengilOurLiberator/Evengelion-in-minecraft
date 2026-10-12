scoreboard players set #force angel.story 0
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorL,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[3.69547f,0.15f,-0.57139f],left_rotation:[0.0f,-0.51504f,0.0f,0.85717f],scale:[0.15f,0.85f,2.0f],right_rotation:[0f,0f,0f,1f]}}
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorGlass,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[3.63065f,1.0f,-0.48029f],left_rotation:[0.0f,-0.51504f,0.0f,0.85717f],scale:[0.1f,0.9f,1.8f],right_rotation:[0f,0f,0f,1f]}}
playsound angel:sfx.car_door master @a 179.101 84.0 58.765 0.55 1.25 0.0
function angel:cast/remove {id:"misato"}
execute positioned 179.5 83.0 56.5 rotated 100.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}
summon minecraft:interaction 179.5 83.0 56.5 {Tags:["angel.story","angel.ia_car"],width:6f,height:2.6f,response:1b}
scoreboard players set #step angel.story 62
function angel:story/s2/e62
