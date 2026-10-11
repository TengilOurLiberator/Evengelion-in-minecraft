$execute as @e[type=minecraft:mannequin,tag=angel.$(id),tag=!angel.mounted,tag=!angel.lying,limit=1] at @s run function angel:cast/sit {id:"$(id)"}
