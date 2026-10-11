scoreboard players add #t_medic2 angel.cast 1
execute if score #t_medic2 angel.cast matches 30.. run return run function angel:cast/finish/medic2
execute if entity @s[nbt={OnGround:1b}] run function angel:cast/finish/medic2
