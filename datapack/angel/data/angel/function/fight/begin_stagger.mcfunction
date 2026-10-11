scoreboard players set #st angel.fight 5
scoreboard players set #t angel.fight 0
scoreboard players set #sl angel.fight 36
scoreboard players set #dur angel.mon 6
function angel:angel/pose_stagger
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.hurt hostile @a ~ ~ ~ 8 0.6
