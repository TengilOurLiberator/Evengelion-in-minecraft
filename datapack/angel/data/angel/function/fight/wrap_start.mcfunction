scoreboard players set #phase angel.fight 3
scoreboard players set #st angel.fight 6
scoreboard players set #t angel.fight 0
scoreboard players set #nav angel.fight 99
scoreboard players set #bar angel.fight 0
scoreboard players set #hold angel.fight 0
scoreboard players set #bo angel.fight 0
scoreboard players set #wgo angel.fight 0
scoreboard players set #wwait angel.fight 0
scoreboard players set #wstage angel.fight 0
scoreboard players set #shud angel.fight 0
scoreboard players set #hbt angel.fight 0
function angel:angel/stop_walking
function angel:fight/heartbeat_stop
scoreboard players set #dur angel.mon 10
function angel:angel/pose_wrap_open
data modify storage angel:mon walk set value {speed:0.9,stop:10.0d}
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.roar hostile @a ~ ~ ~ 12 0.5
bossbar set angel:fight/angel name {"text":"ANGEL  -  it is closing in","color":"red"}
