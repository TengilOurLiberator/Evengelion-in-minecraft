scoreboard players set #ok angel_world 0
execute if loaded 1176 32 176 if loaded 1303 32 176 if loaded 1176 32 303 if loaded 1303 32 303 if loaded 1239 32 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/c148
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/c147 2t
