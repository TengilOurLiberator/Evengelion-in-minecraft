summon minecraft:marker ~ ~ ~ {Tags:["angel.fight","angel.bi"]}
execute at @e[type=minecraft:marker,tag=angel.bi,limit=1] run function angel:fight/cross_flash
scoreboard players set #dmg angel.fight 25
function angel:fight/hurt
