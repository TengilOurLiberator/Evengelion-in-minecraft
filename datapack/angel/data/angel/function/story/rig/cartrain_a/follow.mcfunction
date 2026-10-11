tp @e[tag=angel.rig_cartrain_a,tag=angel.part] ~ ~ ~ ~ ~
tp @e[tag=angel.rig_cartrain_a,tag=angel.seat_driver,limit=1] ^-0.5 ^0.6 ^0.0 ~ ~
tp @e[tag=angel.rig_cartrain_a,tag=angel.seat_passenger,limit=1] ^0.5 ^0.6 ^0.0 ~ ~
execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_cartrain_a,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] ~ 0
