scoreboard players set #st angel.fight 3
scoreboard players set #t angel.fight 0
scoreboard players set #locked angel.fight 0
function angel:angel/stop_walking
scoreboard players set #dur angel.mon 14
function angel:angel/pose_windup
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.agitated hostile @a ~ ~ ~ 8 0.8
