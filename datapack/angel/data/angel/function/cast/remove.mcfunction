$kill @e[type=minecraft:mannequin,tag=angel.$(id)]
$kill @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id)]
$scoreboard players set #on_$(id) angel.cast 0
$scoreboard players set #walk_$(id) angel.cast 0
$scoreboard players set #look_$(id) angel.cast 0
$scoreboard players set #arrived_$(id) angel.cast 0
