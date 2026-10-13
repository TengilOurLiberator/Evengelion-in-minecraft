# the core flashes once (at most one per 0.7 s) so that a swing at the body points him at the place to hit
scoreboard players set #ptcd angel.fight 14
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~3.00 ~ run function angel:fight/core_point_at
