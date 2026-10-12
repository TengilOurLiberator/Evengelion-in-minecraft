scoreboard players set #force angel.story 0
execute positioned 97.5 64.0 131.0 rotated -90.0 0.0 run function angel:story/rig/car/spawn_dooropen
execute positioned 97.5 64.0 131.0 rotated -90.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/mount {id:"misato",tag:"angel.seat_driver"}
ride @a[limit=1] mount @e[tag=angel.seat_passenger,limit=1]
scoreboard players set #ride angel.story 1
execute positioned 174.5 64.0 128.5 rotated 90 0 run function angel:angel/summon {height:100}
scoreboard players set #beat angel.story 20
scoreboard players set #present_misato angel.story 1
scoreboard players set #present_ritsuko angel.story 0
scoreboard players set #present_gendo angel.story 0
scoreboard players set #present_rei angel.story 0
scoreboard players set #step angel.story 5
function angel:story/s2/e5
