scoreboard players set #ride angel.story 0
ride @a[limit=1] dismount
function angel:cast/remove {id:"misato"}
kill @e[tag=angel.rig_car]
execute positioned 179.5 83.0 56.5 rotated 100.0 0.0 run function angel:story/rig/car/spawn_side
tp @a[limit=1] 181.382 83.0 50.435
execute positioned 179.018 82.5 50.018 rotated -4.25 0 run function angel:cast/summon {id:"misato"}
function angel:cast/look {id:"misato",mode:"player"}
scoreboard players set #beat angel.story 21
function angel:angel/pose {pose:"regenerating"}
summon minecraft:interaction 179.934 83.0 54.038 {Tags:["angel.story","angel.ia_push"],width:7.6f,height:4.2f,response:1b}
playsound angel:sfx.car_roll master @a 179.934 84.0 54.038 1.5 1.0 0.0
