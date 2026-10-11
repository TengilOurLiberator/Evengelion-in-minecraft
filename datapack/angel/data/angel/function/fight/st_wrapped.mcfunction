scoreboard players remove #wt angel.fight 1
execute store result bossbar angel:fight/wrap value run scoreboard players get #wt angel.fight
function angel:fight/wrap_follow
execute as @e[tag=angel.giant,type=minecraft:player] if score #wt angel.fight matches 1.. run effect give @s minecraft:slowness 2 3 true
execute if score #t angel.fight matches 20.. run function angel:fight/wrap_beep
execute if score #wt angel.fight matches ..100 if score #t angel.fight matches 10 run function angel:fight/wrap_beep
execute if score #t angel.fight matches 20.. run scoreboard players set #t angel.fight 0
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~2.25 ~ 1.5 1.5 1.5 0 3 force
execute if score #wt angel.fight matches ..0 run function angel:fight/self_destruct
