execute if score #np_gendo angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.gendo,limit=1] run function angel:cast/nud/gendo
execute if score #walk_gendo angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.gendo,limit=1] at @s run function angel:cast/step/gendo
execute if score #walk_gendo angel.cast matches 0 if score #look_gendo angel.cast matches 1 if score #np_gendo angel.cast matches 0 as @e[type=minecraft:mannequin,tag=angel.gendo,tag=!angel.lying,limit=1] at @s run function angel:cast/look_step
execute as @e[type=minecraft:mannequin,tag=angel.gendo,tag=angel.mounted,limit=1] run function angel:cast/check_mounted
