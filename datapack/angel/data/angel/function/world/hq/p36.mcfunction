scoreboard players set #ok angel_world 0
execute if loaded 3152 0 -64 if loaded 3255 0 -64 if loaded 3152 0 159 if loaded 3255 0 159 if loaded 3203 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p37
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p36 2t
