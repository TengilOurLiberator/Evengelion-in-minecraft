scoreboard players set #st angel.fight 1
scoreboard players set #t angel.fight 0
scoreboard players set #locked angel.fight 0
execute if score #phase angel.fight matches 1 run scoreboard players set #bt angel.fight 40
execute if score #phase angel.fight matches 2.. run scoreboard players set #bt angel.fight 34
function angel:angel/stop_walking
scoreboard players set #dur angel.mon 14
function angel:angel/pose_charging
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.sonic_charge hostile @a ~ ~ ~ 8 0.9
function angel:fight/bark_beam
