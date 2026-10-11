execute at @s run function angel:cast/arrive_m with storage angel:cast walk.rei_uniform
data modify entity @s Motion[0] set value 0.0d
data modify entity @s Motion[2] set value 0.0d
scoreboard players set #walk_rei_uniform angel.cast 2
scoreboard players set #t_rei_uniform angel.cast 0
