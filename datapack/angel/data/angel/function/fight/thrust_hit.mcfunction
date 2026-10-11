scoreboard players set #dmg angel.fight 15
function angel:fight/hurt
execute as @e[tag=angel.giant,type=minecraft:player] run effect give @s minecraft:slowness 2 2 true
execute at @e[tag=angel.giant,limit=1] run particle minecraft:crit ~ ~14 ~ 4 8 4 0.5 40 force
