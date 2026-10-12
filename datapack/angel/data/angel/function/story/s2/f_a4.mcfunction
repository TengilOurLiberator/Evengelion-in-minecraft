scoreboard players set #ride angel.story 0
ride @a[limit=1] dismount
function angel:cast/remove {id:"misato"}
kill @e[tag=angel.rig_car]
execute positioned 179.5 83.0 56.5 rotated 100.0 0.0 run function angel:story/rig/car/spawn_side
tp @a[limit=1] 181.503 82.5 49.745
execute positioned 179.14 82.5 49.329 rotated -2.88 0 run function angel:cast/summon {id:"misato"}
function angel:cast/look {id:"misato",mode:"player"}
scoreboard players set #beat angel.story 21
function angel:angel/pose {pose:"regenerating"}
summon minecraft:interaction 180.021 83.0 53.546 {Tags:["angel.story","angel.ia_push"],width:7.4f,height:4.4f,response:1b}
playsound angel:sfx.car_roll master @a 180.021 84.0 53.546 1.5 1.0 0.0
