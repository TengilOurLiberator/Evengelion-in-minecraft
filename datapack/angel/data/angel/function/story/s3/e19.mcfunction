scoreboard players set #force angel.story 0
execute positioned 2025.484 98.0 101.851 rotated -135.0 0.0 run function angel:story/rig/cartrain_b/spawn_ride
execute positioned 2025.484 98.0 101.851 rotated 45.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}
function angel:cast/look {id:"misato",mode:"ahead"}
ride @a[limit=1] mount @e[tag=angel.seat_passenger,limit=1]
scoreboard players set #ride angel.story 1
scoreboard players set #present_misato angel.story 1
scoreboard players set #step angel.story 20
function angel:story/s3/e20
