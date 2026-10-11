execute at @e[tag=angel.giant,limit=1] run function angel:fight/cross_flash
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run particle minecraft:explosion_emitter ~ ~10 ~ 6 6 6 0 8 force
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.generic.explode hostile @a ~ ~ ~ 16 0.5
scoreboard players set #lost_reason angel.fight 2
function angel:fight/lost_start
