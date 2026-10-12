function angel:cast/look {id:"misato",mode:"ahead"}
execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_car,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
