scoreboard players set #ok angel_world 0
execute if loaded 2272 0 50 if loaded 2321 0 50 if loaded 2272 0 111 if loaded 2321 0 111 if loaded 2296 0 80 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p101
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p100 2t
