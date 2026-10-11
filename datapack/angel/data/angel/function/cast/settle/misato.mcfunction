scoreboard players add #t_misato angel.cast 1
execute if score #t_misato angel.cast matches 30.. run return run function angel:cast/finish/misato
execute if entity @s[nbt={OnGround:1b}] run function angel:cast/finish/misato
