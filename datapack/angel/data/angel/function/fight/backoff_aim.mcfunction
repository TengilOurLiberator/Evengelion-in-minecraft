# the retreat point goes into the angel.target marker: backoff_dist along the avenue away from the giant, kept inside its far end;
# with less than backoff_min of room it steps to the other side of the avenue instead (it still retreats what room there is)
execute store result score #rx angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[0] 10
execute store result score #rz angel.fight run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Pos[2] 10
execute store result score #gz angel.fight run data get entity @e[tag=angel.giant,limit=1] Pos[2] 10
scoreboard players operation #tx angel.fight = #rx angel.fight
scoreboard players operation #tz angel.fight = #rz angel.fight
execute if score #gz angel.fight >= #rz angel.fight run scoreboard players remove #tz angel.fight 200
execute if score #gz angel.fight >= #rz angel.fight run scoreboard players operation #room angel.fight = #rz angel.fight
execute if score #gz angel.fight >= #rz angel.fight run scoreboard players remove #room angel.fight 500
execute if score #gz angel.fight >= #rz angel.fight if score #tz angel.fight matches ..500 run scoreboard players set #tz angel.fight 500
execute if score #gz angel.fight < #rz angel.fight run scoreboard players add #tz angel.fight 200
execute if score #gz angel.fight < #rz angel.fight run scoreboard players set #room angel.fight 1400
execute if score #gz angel.fight < #rz angel.fight run scoreboard players operation #room angel.fight -= #rz angel.fight
execute if score #gz angel.fight < #rz angel.fight if score #tz angel.fight matches 1400.. run scoreboard players set #tz angel.fight 1400
execute if score #room angel.fight matches ..99 run function angel:fight/backoff_side
data modify entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos set value [1160.0d,64.0d,0.0d]
execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[0] double 0.1 run scoreboard players get #tx angel.fight
execute store result entity @e[type=minecraft:marker,tag=angel.target,limit=1] Pos[2] double 0.1 run scoreboard players get #tz angel.fight
