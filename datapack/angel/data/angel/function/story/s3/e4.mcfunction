scoreboard players set #force angel.story 0
execute positioned 190.5 76.0 31.5 rotated 180.0 0.0 run function angel:story/rig/car/spawn_closed
execute positioned 190.5 76.0 31.5 rotated 180.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}
function angel:cast/look {id:"misato",mode:"ahead"}
ride @a[limit=1] mount @e[tag=angel.seat_passenger,limit=1]
scoreboard players set #ride angel.story 1
scoreboard players set #beat angel.story 30
scoreboard players set #present_misato angel.story 1
scoreboard players set #present_ritsuko angel.story 0
scoreboard players set #present_gendo angel.story 0
scoreboard players set #present_rei angel.story 0
scoreboard players set #step angel.story 5
function angel:story/s3/e5
