execute if score #walk_misato angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.misato,limit=1] at @s run function angel:cast/step/misato
execute if score #walk_misato angel.cast matches 0 if score #look_misato angel.cast matches 1 as @e[type=minecraft:mannequin,tag=angel.misato,tag=!angel.lying,limit=1] at @s run function angel:cast/look_step
execute as @e[type=minecraft:mannequin,tag=angel.misato,tag=angel.mounted,limit=1] run function angel:cast/check_mounted
