scoreboard players set #ok angel_world 0
execute if loaded 2272 0 80 if loaded 2335 0 80 if loaded 2272 0 207 if loaded 2335 0 207 if loaded 2303 0 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c160
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c159 2t
