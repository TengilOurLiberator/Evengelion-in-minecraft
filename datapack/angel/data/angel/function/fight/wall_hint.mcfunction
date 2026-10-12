# faint octagon of light, on the monster's side, facing the giant (every 10 ticks while the giant is far)
execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0
execute if score #phase angel.fight matches 3.. run return 0
scoreboard players set #wallt angel.fight 10
# (with the barrier raised after a back-off it is drawn at any distance)
execute unless score #bar angel.fight matches 1 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~2.25 ~ unless entity @e[tag=angel.giant,distance=..60] run return 0
execute unless score #bar angel.fight matches 1 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~2.25 ~ positioned ~ ~-22.0 ~ if entity @e[tag=angel.giant,distance=..12.5] run return 0
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~2.25 ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_dots
