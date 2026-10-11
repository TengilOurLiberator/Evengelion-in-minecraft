execute if score #walk_rei angel.cast matches 1.. as @e[type=minecraft:mannequin,tag=angel.rei,limit=1] at @s run function angel:cast/step/rei
execute if score #walk_rei angel.cast matches 0 if score #look_rei angel.cast matches 1 as @e[type=minecraft:mannequin,tag=angel.rei,tag=!angel.lying,limit=1] at @s run function angel:cast/look_step
execute as @e[type=minecraft:mannequin,tag=angel.rei,tag=angel.mounted,limit=1] run function angel:cast/check_mounted
