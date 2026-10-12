# a thin red sighting line along the locked beam path
scoreboard players set #rs angel.fight 45
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^25.36 ^5.35 facing entity @e[type=minecraft:marker,tag=angel.aimpt,limit=1] feet run function angel:fight/ray_warn
