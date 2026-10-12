execute if score #np_medic1 angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.medic1,limit=1] run function angel:cast/nud/medic1
execute if score #walk_medic1 angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.medic1,limit=1] at @s run function angel:cast/step/medic1
execute if score #walk_medic1 angel.cast matches 0 if score #look_medic1 angel.cast matches 1 if score #np_medic1 angel.cast matches 0 as @e[type=minecraft:mannequin,tag=angel.medic1,tag=!angel.lying,limit=1] at @s run function angel:cast/look_step
execute as @e[type=minecraft:mannequin,tag=angel.medic1,tag=angel.mounted,limit=1] run function angel:cast/check_mounted
