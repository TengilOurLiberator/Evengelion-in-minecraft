tp @e[tag=angel.rig_car,tag=angel.rpart] ~ ~ ~ ~ ~
tp @e[tag=angel.rig_car,tag=angel.seat_driver,limit=1] ^-0.72 ^0.77 ^0.12 ~ ~
tp @e[tag=angel.rig_car,tag=angel.seat_passenger,limit=1] ^0.72 ^0.77 ^-0.12 ~ ~
execute unless score #look_misato angel.cast matches 1 if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_car,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
