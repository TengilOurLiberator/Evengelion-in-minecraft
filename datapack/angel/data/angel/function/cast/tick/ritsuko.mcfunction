execute if score #walk_ritsuko angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.ritsuko,limit=1] at @s run function angel:cast/step/ritsuko
execute if score #walk_ritsuko angel.cast matches 0 if score #look_ritsuko angel.cast matches 1 as @e[type=minecraft:mannequin,tag=angel.ritsuko,tag=!angel.lying,limit=1] at @s run function angel:cast/look_step
execute as @e[type=minecraft:mannequin,tag=angel.ritsuko,tag=angel.mounted,limit=1] run function angel:cast/check_mounted
