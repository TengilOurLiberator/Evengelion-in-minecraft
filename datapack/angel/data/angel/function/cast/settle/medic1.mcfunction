scoreboard players add #t_medic1 angel.cast 1
execute if score #t_medic1 angel.cast matches 30.. run return run function angel:cast/finish/medic1
execute if entity @s[nbt={OnGround:1b}] run function angel:cast/finish/medic1
