$scoreboard players set #walk_$(id) angel.cast 0
$execute as @e[type=minecraft:mannequin,tag=angel.$(id),limit=1] run data merge entity @s {immovable:1b,NoGravity:1b,Motion:[0.0d,0.0d,0.0d]}
