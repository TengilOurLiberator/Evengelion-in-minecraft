scoreboard players set #phase angel.fight 2
scoreboard players set #st angel.fight 5
scoreboard players set #t angel.fight 0
scoreboard players set #sl angel.fight 80
function angel:angel/stop_walking
function angel:angel/core_stage {stage:1}
function angel:angel/pose_regenerating
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.roar hostile @a ~ ~ ~ 10 0.7
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.glass.break hostile @a ~ ~ ~ 10 0.5
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:lava ~ ~2.25 ~ 1 1 1 0.2 30 force
bossbar set angel:fight/angel name {"text":"ANGEL  -  core cracked","color":"red"}
function angel:fight/bark {id:"7_12"}
function angel:fight/bark {id:"7_13"}
