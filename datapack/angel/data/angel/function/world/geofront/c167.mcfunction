scoreboard players set #ok angel_world 0
execute if loaded 2272 0 176 if loaded 2335 0 176 if loaded 2272 0 303 if loaded 2335 0 303 if loaded 2303 0 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c168
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c167 2t
