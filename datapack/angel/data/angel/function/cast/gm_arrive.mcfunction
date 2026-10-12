$tp @e[tag=angel.gurney] $(x) $(y) $(z)
execute at @s run function angel:cast/gm_followers
execute if entity @e[type=minecraft:mannequin,tag=angel.medic1] run scoreboard players set #look_medic1 angel.cast 1
execute if entity @e[type=minecraft:mannequin,tag=angel.medic2] run scoreboard players set #look_medic2 angel.cast 1
scoreboard players set #gmove angel.cast 0
scoreboard players set #arrived_gurney angel.cast 1
