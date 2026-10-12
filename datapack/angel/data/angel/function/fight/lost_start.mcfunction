# giant health 0, or the self-destruct went off. #lost_reason: 1 health, 2 countdown
execute if score #phase angel.fight matches 4.. run return 0
scoreboard players set #phase angel.fight 5
scoreboard players set #pt angel.fight 0
scoreboard players set #st angel.fight 8
function angel:fight/heartbeat_stop
execute unless score #lost_reason angel.fight matches 2 run scoreboard players set #lost_reason angel.fight 1
function angel:angel/stop_walking
bossbar set angel:fight/wrap visible false
execute as @e[tag=angel.giant] run effect clear @s minecraft:slowness
data modify storage angel:fight q set value []
scoreboard players reset #7_19 angel.barks
scoreboard players reset #7_20 angel.barks
function angel:fight/bark {id:"7_19"}
function angel:fight/bark {id:"7_20"}
execute at @e[tag=angel.giant,limit=1] run playsound minecraft:entity.warden.death hostile @a ~ ~ ~ 8 0.7
execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:blindness 12 0 true
execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:slowness 12 6 true
