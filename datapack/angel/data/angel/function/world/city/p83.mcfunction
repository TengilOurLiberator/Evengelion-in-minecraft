scoreboard players set #ok angel_world 0
execute if loaded 1376 32 160 if loaded 1383 32 160 if loaded 1376 32 383 if loaded 1383 32 383 if loaded 1379 32 271 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p84
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p83 2t
