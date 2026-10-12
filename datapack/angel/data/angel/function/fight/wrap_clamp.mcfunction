scoreboard players set #st angel.fight 7
scoreboard players set #t angel.fight 0
scoreboard players set #wt angel.fight 400
function angel:angel/stop_walking
function angel:fight/wrap_follow
scoreboard players set #dur angel.mon 8
function angel:angel/pose_wrapping
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.sonic_charge hostile @a ~ ~ ~ 10 0.6
bossbar set angel:fight/wrap players @e[tag=angel.giant,type=minecraft:player]
bossbar set angel:fight/wrap visible true
bossbar set angel:fight/angel name {"text":"ANGEL  -  break loose: hit the core","color":"red"}
function angel:fight/bark {id:"7_14"}
