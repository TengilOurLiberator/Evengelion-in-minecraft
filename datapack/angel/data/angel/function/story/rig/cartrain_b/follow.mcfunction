tp @e[tag=angel.rig_cartrain_b,tag=angel.rpart] ~ ~ ~ ~ ~
tp @e[tag=angel.rig_cartrain_b,tag=angel.seat_driver,limit=1] ^0.72 ^0.77 ^-0.12 ~180.0 ~
tp @e[tag=angel.rig_cartrain_b,tag=angel.seat_passenger,limit=1] ^-0.72 ^0.77 ^0.12 ~180.0 ~
execute unless score #look_misato angel.cast matches 1 if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_cartrain_b,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
