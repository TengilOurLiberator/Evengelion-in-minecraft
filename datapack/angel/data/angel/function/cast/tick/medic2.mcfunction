execute if score #walk_medic2 angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.medic2,limit=1] at @s run function angel:cast/step/medic2
execute if score #walk_medic2 angel.cast matches 0 if score #look_medic2 angel.cast matches 1 as @e[type=minecraft:mannequin,tag=angel.medic2,tag=!angel.lying,limit=1] at @s run function angel:cast/look_step
execute as @e[type=minecraft:mannequin,tag=angel.medic2,tag=angel.mounted,limit=1] run function angel:cast/check_mounted
