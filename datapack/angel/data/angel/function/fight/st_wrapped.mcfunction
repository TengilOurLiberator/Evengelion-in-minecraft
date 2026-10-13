# the countdown waits for the bark 7.14 to begin (or wrap_wait ticks)
execute if score #wgo angel.fight matches 0 run function angel:fight/wrap_wait
execute if score #wgo angel.fight matches 1 run scoreboard players remove #wt angel.fight 1
execute store result bossbar angel:fight/wrap value run scoreboard players get #wt angel.fight
function angel:fight/wrap_follow
execute as @e[tag=angel.giant,type=minecraft:player] if score #wt angel.fight matches 1.. run effect give @s minecraft:slowness 2 3 true
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run particle minecraft:dust{color:[1.0,0.1,0.1],scale:2.5} ~ ~3.00 ~ 1.5 1.5 1.5 0 3 force
# the shudder of a hit lasts 4 ticks, then the stage pose comes back
execute if score #shud angel.fight matches 2.. run scoreboard players remove #shud angel.fight 1
execute if score #shud angel.fight matches 1 run function angel:fight/wrap_restore
execute if score #wgo angel.fight matches 1 run function angel:fight/wrap_count
execute if score #wt angel.fight matches ..0 run function angel:fight/self_destruct
