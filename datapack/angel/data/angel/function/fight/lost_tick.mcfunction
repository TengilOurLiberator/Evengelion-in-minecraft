scoreboard players add #pt angel.fight 1
execute if score #pt angel.fight matches ..60 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~2 ~ 1.5 1.5 1.5 0 2 force
execute if score #pt angel.fight matches 140.. if function angel:fight/queue_empty run function angel:fight/restart
execute if score #pt angel.fight matches 1200.. run function angel:fight/restart
