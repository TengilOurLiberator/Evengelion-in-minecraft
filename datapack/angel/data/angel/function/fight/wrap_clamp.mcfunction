scoreboard players set #st angel.fight 7
scoreboard players set #t angel.fight 0
scoreboard players set #wt angel.fight 320
scoreboard players set #wgo angel.fight 0
scoreboard players set #wwait angel.fight 0
scoreboard players set #wstage angel.fight 0
scoreboard players set #shud angel.fight 0
scoreboard players set #hbt angel.fight 0
function angel:angel/stop_walking
function angel:fight/wrap_follow
function angel:angel/pose_wrapping
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.sonic_charge hostile @a ~ ~ ~ 10 0.6
bossbar set angel:fight/wrap players @e[tag=angel.giant,type=minecraft:player]
bossbar set angel:fight/wrap visible true
bossbar set angel:fight/wrap color red
execute store result bossbar angel:fight/wrap value run scoreboard players get #wt angel.fight
bossbar set angel:fight/angel name {"text":"ANGEL  -  break loose: hit the core","color":"red"}
# the tell: what to do, big, at once; the core flares
execute as @e[tag=angel.giant,type=minecraft:player] run title @s times 0 50 10
execute as @e[tag=angel.giant,type=minecraft:player] run title @s subtitle {"text":"hit the core - keep swinging","color":"gold"}
execute as @e[tag=angel.giant,type=minecraft:player] run title @s title {"text":"BREAK LOOSE","color":"red","bold":true}
function angel:fight/wrap_flare
function angel:fight/bark_front {id:"7_14"}
