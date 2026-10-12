scoreboard players set #ok angel_world 0
execute if loaded -64 32 -64 if loaded 159 32 -64 if loaded -64 32 159 if loaded 159 32 159 if loaded 47 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p82
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p81 2t
