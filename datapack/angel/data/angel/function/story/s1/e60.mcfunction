scoreboard players set #force angel.story 0
execute positioned 76.0 64.5 141.0 rotated -80.24 0.0 run function angel:story/rig/car/spawn_closed
execute positioned 76.0 64.5 141.0 rotated -80.24 0 run function angel:cast/summon {id:"misato"}
function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}
function angel:cast/look {id:"misato",mode:"ahead"}
scoreboard players set #mv.route angel.story 1
scoreboard players set #mv.n angel.story 0
scoreboard players set #mv.limit angel.story 76
scoreboard players set #mv.on angel.story 1
function angel:story/m/slide_in/root
playsound angel:sfx.car_arrive master @a 87.0 64.0 135.0 1.5 1.0 0.0
scoreboard players set #step angel.story 61
function angel:story/s1/e61
