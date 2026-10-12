scoreboard players set #ok angel_world 0
execute if loaded 3152 0 160 if loaded 3255 0 160 if loaded 3152 0 255 if loaded 3255 0 255 if loaded 3203 0 207 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p40
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p39 2t
