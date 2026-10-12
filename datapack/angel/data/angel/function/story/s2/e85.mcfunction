scoreboard players set #force angel.story 0
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorL,limit=1] {start_interpolation:0,interpolation_duration:8,transformation:{translation:[2.47765f,0.481f,0.34653f],left_rotation:[0.0f,-0.51504f,0.0f,0.85717f],scale:[1.0f,1.0f,1.0f],right_rotation:[0f,0f,0f,1f]}}
playsound angel:sfx.car_door master @a 179.118 84.0 58.667 0.55 1.25 0.0
function angel:cast/look {id:"misato",mode:"ahead"}
function angel:cast/walk {id:"misato",x:179.781,y:82.5,z:54.214,speed:0.11}
summon minecraft:interaction 179.5 83.0 56.5 {Tags:["angel.story","angel.ia_car"],width:6f,height:2.6f,response:1b}
scoreboard players set #step angel.story 86
function angel:story/s2/e86
