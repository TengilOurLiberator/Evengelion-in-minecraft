$summon minecraft:armor_stand ~ ~0.6 ~ {Tags:["angel.cast","angel.seat","angel.autoseat_$(id)"],Marker:1b,Invisible:1b,NoGravity:1b,Silent:1b,Invulnerable:1b}
$ride @s mount @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id),limit=1]
tag @s add angel.sitting
tag @s add angel.mounted
data merge entity @s {immovable:1b,NoGravity:1b}
$scoreboard players set #walk_$(id) angel.cast 0
scoreboard players set #active angel.cast 1
