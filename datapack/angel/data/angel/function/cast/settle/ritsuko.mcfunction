scoreboard players add #t_ritsuko angel.cast 1
execute if score #t_ritsuko angel.cast matches 30.. run return run function angel:cast/finish/ritsuko
execute if entity @s[nbt={OnGround:1b}] run function angel:cast/finish/ritsuko
