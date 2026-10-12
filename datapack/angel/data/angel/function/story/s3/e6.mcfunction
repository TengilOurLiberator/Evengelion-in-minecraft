scoreboard players set #force angel.story 0
execute positioned 190.5 76.0 31.5 rotated 180.0 0.0 run function angel:story/rig/car/spawn_closed
execute positioned 190.5 76.0 31.5 rotated 180.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}
function angel:cast/look {id:"misato",mode:"ahead"}
execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_car,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
ride @a[limit=1] mount @e[tag=angel.seat_passenger,limit=1]
scoreboard players set #ride angel.story 1
scoreboard players set #beat angel.story 30
scoreboard players set #present_misato angel.story 1
scoreboard players set #present_ritsuko angel.story 0
scoreboard players set #present_gendo angel.story 0
scoreboard players set #present_rei angel.story 0
function angel:story/snd/bed_car_interior/start
scoreboard players set #step angel.story 7
function angel:story/s3/e7
