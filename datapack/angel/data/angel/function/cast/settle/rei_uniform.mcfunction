scoreboard players add #t_rei_uniform angel.cast 1
execute if score #t_rei_uniform angel.cast matches 30.. run return run function angel:cast/finish/rei_uniform
execute if entity @s[nbt={OnGround:1b}] run function angel:cast/finish/rei_uniform
