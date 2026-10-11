scoreboard players add #t_rei angel.cast 1
execute if score #t_rei angel.cast matches 30.. run return run function angel:cast/finish/rei
execute if entity @s[nbt={OnGround:1b}] run function angel:cast/finish/rei
