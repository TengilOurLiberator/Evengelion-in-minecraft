# where to walk: the giant if it is near, else down the avenue; kept on the avenue
scoreboard players set #nav angel.fight 0
execute store result score #rz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[2] 10
scoreboard players add #rz angel.fight 260
data modify entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos set value [1160.0d,64.0d,0.0d]
execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] double 0.1 run scoreboard players get #rz angel.fight
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..75] run tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]
execute store result score #tx angel.fight run data get entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[0] 10
execute store result score #tz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] 10
execute if score #tx angel.fight matches ..11520 run scoreboard players set #tx angel.fight 11520
execute if score #tx angel.fight matches 11680.. run scoreboard players set #tx angel.fight 11680
execute if score #tz angel.fight matches 1400.. run scoreboard players set #tz angel.fight 1400
execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[0] double 0.1 run scoreboard players get #tx angel.fight
execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] double 0.1 run scoreboard players get #tz angel.fight
execute if score #phase angel.fight matches 1 run data modify storage angel:mon walk set value {speed:0.3,stop:17.0d}
execute if score #phase angel.fight matches 2 run data modify storage angel:mon walk set value {speed:0.42,stop:17.0d}
# walk only while it is farther than the stand-off distance (+ a margin)
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s unless entity @e[tag=angel.giant,distance=..20.0] run function angel:angel/walk_go
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s if entity @e[tag=angel.giant,distance=..20.0] run function angel:fight/face_giant
