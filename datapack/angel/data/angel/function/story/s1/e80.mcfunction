scoreboard players set #force angel.story 0
data merge entity @e[tag=angel.rig_car,tag=angel.pt_doorL,limit=1] {start_interpolation:0,interpolation_duration:10,transformation:{translation:[2.47765f,0.481f,0.34653f],left_rotation:[0.0f,-0.51504f,0.0f,0.85717f],scale:[1.0f,1.0f,1.0f],right_rotation:[0f,0f,0f,1f]}}
playsound angel:sfx.car_door master @a 97.478 65.0 128.8 0.55 1.25 0.0
scoreboard players set #beat angel.story 11
scoreboard players set #present_misato angel.story 1
function angel:cast/look {id:"misato",mode:"player"}
summon minecraft:interaction 97.5 64.0 131.0 {Tags:["angel.story","angel.ia_car"],width:6f,height:2.6f,response:1b}
scoreboard players set #step angel.story 81
function angel:story/s1/e81
