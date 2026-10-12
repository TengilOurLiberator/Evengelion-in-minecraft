scoreboard players set #force angel.story 0
function angel:cast/look {id:"misato",mode:"ahead"}
execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_car,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing 174.5 119.0 128.5
scoreboard players set #step angel.story 36
function angel:story/s2/e36
