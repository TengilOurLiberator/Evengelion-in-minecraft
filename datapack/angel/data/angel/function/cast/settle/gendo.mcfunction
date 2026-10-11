scoreboard players add #t_gendo angel.cast 1
execute if score #t_gendo angel.cast matches 30.. run return run function angel:cast/finish/gendo
execute if entity @s[nbt={OnGround:1b}] run function angel:cast/finish/gendo
