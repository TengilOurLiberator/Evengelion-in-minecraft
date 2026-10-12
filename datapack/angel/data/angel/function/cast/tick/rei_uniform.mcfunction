execute if score #np_rei_uniform angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.rei_uniform,limit=1] run function angel:cast/nud/rei_uniform
execute if score #walk_rei_uniform angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.rei_uniform,limit=1] at @s run function angel:cast/step/rei_uniform
execute if score #walk_rei_uniform angel.cast matches 0 if score #look_rei_uniform angel.cast matches 1 if score #np_rei_uniform angel.cast matches 0 as @e[type=minecraft:mannequin,tag=angel.rei_uniform,tag=!angel.lying,limit=1] at @s run function angel:cast/look_step
execute as @e[type=minecraft:mannequin,tag=angel.rei_uniform,tag=angel.mounted,limit=1] run function angel:cast/check_mounted
