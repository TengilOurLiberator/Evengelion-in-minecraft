scoreboard players set #force angel.story 0
scoreboard players set #ride angel.story 0
kill @e[tag=angel.rig_car]
kill @e[tag=angel.rig_wagon_o]
function angel:cast/remove {id:"misato"}
execute positioned 191.5 77.0 15.5 rotated 180.0 0.0 run function angel:story/rig/cartrain_a/spawn_loaded
execute positioned 191.5 77.0 15.5 rotated 180.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}
function angel:cast/look {id:"misato",mode:"ahead"}
execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_cartrain_a,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
ride @a[limit=1] mount @e[tag=angel.seat_passenger,limit=1]
scoreboard players set #ride angel.story 1
scoreboard players set #step angel.story 51
function angel:story/s3/e51
