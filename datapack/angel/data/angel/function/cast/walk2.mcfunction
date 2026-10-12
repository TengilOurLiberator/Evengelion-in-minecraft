execute if entity @s[tag=angel.lying] run function angel:cast/unlie
execute if entity @s[tag=angel.mounted] run ride @s dismount
$kill @e[type=minecraft:armor_stand,tag=angel.autoseat_$(id)]
tag @s remove angel.mounted
tag @s remove angel.sitting
$scoreboard players set #np_$(id) angel.cast 0
effect clear @s minecraft:invisibility
data merge entity @s {immovable:0b,NoGravity:0b}
$summon minecraft:marker ^ ^ ^$(speed) {Tags:["angel.tmp"]}
execute store result score #ax angel.cast run data get entity @s Pos[0] 100000
execute store result score #az angel.cast run data get entity @s Pos[2] 100000
execute store result score #bx angel.cast run data get entity @e[type=minecraft:marker,tag=angel.tmp,limit=1] Pos[0] 100000
execute store result score #bz angel.cast run data get entity @e[type=minecraft:marker,tag=angel.tmp,limit=1] Pos[2] 100000
kill @e[type=minecraft:marker,tag=angel.tmp]
scoreboard players operation #bx angel.cast -= #ax angel.cast
scoreboard players operation #bz angel.cast -= #az angel.cast
$scoreboard players operation #mx_$(id) angel.cast = #bx angel.cast
$scoreboard players operation #mz_$(id) angel.cast = #bz angel.cast
$execute store result score #tx_$(id) angel.cast run data get storage angel:cast walk.$(id).x 100
$execute store result score #tz_$(id) angel.cast run data get storage angel:cast walk.$(id).z 100
$execute store result score #sp_$(id) angel.cast run data get storage angel:cast walk.$(id).speed 100
$execute if score #sp_$(id) angel.cast matches ..0 run scoreboard players set #sp_$(id) angel.cast 1
scoreboard players operation #ax angel.cast /= #k1000 angel.cast
scoreboard players operation #az angel.cast /= #k1000 angel.cast
$scoreboard players operation #dx angel.cast = #tx_$(id) angel.cast
$scoreboard players operation #dz angel.cast = #tz_$(id) angel.cast
scoreboard players operation #dx angel.cast -= #ax angel.cast
scoreboard players operation #dz angel.cast -= #az angel.cast
execute if score #dx angel.cast matches ..-1 run scoreboard players operation #dx angel.cast *= #km1 angel.cast
execute if score #dz angel.cast matches ..-1 run scoreboard players operation #dz angel.cast *= #km1 angel.cast
scoreboard players operation #dx angel.cast += #dz angel.cast
$scoreboard players operation #dx angel.cast /= #sp_$(id) angel.cast
scoreboard players operation #dx angel.cast *= #k2 angel.cast
scoreboard players add #dx angel.cast 60
$scoreboard players operation #tmax_$(id) angel.cast = #dx angel.cast
$scoreboard players set #t_$(id) angel.cast 0
$scoreboard players set #arrived_$(id) angel.cast 0
$scoreboard players set #walk_$(id) angel.cast 1
scoreboard players set #active angel.cast 1
