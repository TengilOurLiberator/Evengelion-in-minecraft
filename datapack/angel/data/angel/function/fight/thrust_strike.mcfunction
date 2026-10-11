scoreboard players set #st angel.fight 4
scoreboard players set #t angel.fight 0
scoreboard players set #dur angel.mon 3
function angel:angel/pose_thrust
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:entity.warden.attack_impact hostile @a ~ ~ ~ 10 0.7
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^ ^18.6 run particle minecraft:explosion ~ ~1 ~ 2 1 2 0 6 force
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s positioned ^ ^ ^18.6 positioned ~-4.5 ~-2 ~-4.5 if entity @e[tag=angel.giant,dx=9,dy=26,dz=9] run function angel:fight/thrust_hit
