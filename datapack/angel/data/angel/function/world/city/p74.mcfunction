scoreboard players set #ok angel_world 0
execute if loaded 1152 32 -64 if loaded 1375 32 -64 if loaded 1152 32 159 if loaded 1375 32 159 if loaded 1263 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p75
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p74 2t
