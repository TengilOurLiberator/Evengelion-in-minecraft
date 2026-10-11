execute if score #on_misato angel.cast matches 1 run function angel:cast/tick/misato
execute if score #on_ritsuko angel.cast matches 1 run function angel:cast/tick/ritsuko
execute if score #on_gendo angel.cast matches 1 run function angel:cast/tick/gendo
execute if score #on_rei angel.cast matches 1 run function angel:cast/tick/rei
execute if score #on_rei_uniform angel.cast matches 1 run function angel:cast/tick/rei_uniform
execute if score #on_medic1 angel.cast matches 1 run function angel:cast/tick/medic1
execute if score #on_medic2 angel.cast matches 1 run function angel:cast/tick/medic2
execute if score #gmove angel.cast matches 1 run function angel:cast/gm_step
scoreboard players add #idle angel.cast 1
execute if score #idle angel.cast matches 100.. run function angel:cast/idle_check
