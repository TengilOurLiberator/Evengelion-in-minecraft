execute at @s run function angel:cast/arrive_m with storage angel:cast walk.medic2
data modify entity @s Motion[0] set value 0.0d
data modify entity @s Motion[2] set value 0.0d
scoreboard players set #walk_medic2 angel.cast 2
scoreboard players set #t_medic2 angel.cast 0
