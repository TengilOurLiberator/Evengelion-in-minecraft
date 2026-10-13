execute if score #ginv angel.fight matches 1.. run scoreboard players remove #ginv angel.fight 1
execute if score #cd09 angel.fight matches 1.. run scoreboard players remove #cd09 angel.fight 1
execute if score #blockcd angel.fight matches 1.. run scoreboard players remove #blockcd angel.fight 1
execute if score #sparkcd angel.fight matches 1.. run scoreboard players remove #sparkcd angel.fight 1
execute if score #barsnd angel.fight matches 1.. run scoreboard players remove #barsnd angel.fight 1
execute if score #ptcd angel.fight matches 1.. run scoreboard players remove #ptcd angel.fight 1
scoreboard players add #gcalm angel.fight 1
scoreboard players add #t20 angel.fight 1
execute if score #t20 angel.fight matches 20.. run function angel:fight/second
execute store result bossbar angel:fight/giant value run scoreboard players get #gh angel.fight
execute store result bossbar angel:fight/angel value run scoreboard players get #ch angel.fight
execute if score #steps angel.fight matches 0 at @e[type=minecraft:marker,tag=angel.origin,limit=1] unless entity @e[tag=angel.giant,distance=..8] run function angel:fight/first_steps
# the two states, drawn: the octagon of light and the dimmed core while shielded, the burning core and its halo while vulnerable (and #vuln)
function angel:fight/vis_tick
