# follows the core and breathes (a pulse every halo_period ticks: the cubes grow to halo_big over half of it, shrink back over the other half)
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~3.00 ~ run tp @e[type=minecraft:block_display,tag=angel.hot] ~ ~ ~
scoreboard players add #vp angel.fight 1
execute if score #vp angel.fight matches 1 run function angel:fight/hot_big
execute if score #vp angel.fight matches 11 run function angel:fight/hot_small
execute if score #vp angel.fight matches 20.. run scoreboard players set #vp angel.fight 0
