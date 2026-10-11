$execute as @e[type=minecraft:mannequin,tag=angel.$(id),limit=1] at @s run function angel:cast/stand_up {id:"$(id)"}
