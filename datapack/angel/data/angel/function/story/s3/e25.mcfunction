scoreboard players set #force angel.story 0
scoreboard players set #ride angel.story 0
kill @e[tag=angel.rig_cartrain_a]
kill @e[tag=angel.gate]
function angel:cast/remove {id:"misato"}
forceload add 2000 80
forceload add 2000 96
forceload add 2000 112
forceload add 2016 80
forceload add 2016 96
forceload add 2016 112
forceload add 2032 80
forceload add 2032 96
forceload add 2032 112
tp @a[limit=1] 2025.484 98.0 101.851
function angel:world/sky_geofront
scoreboard players set #step angel.story 26
function angel:story/s3/e26
