scoreboard players set #ok angel_world 0
execute if loaded 1152 32 160 if loaded 1375 32 160 if loaded 1152 32 383 if loaded 1375 32 383 if loaded 1263 32 271 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p78
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p77 2t
