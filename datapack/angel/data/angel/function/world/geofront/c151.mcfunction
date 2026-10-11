scoreboard players set #ok angel_world 0
execute if loaded 2272 0 -16 if loaded 2335 0 -16 if loaded 2272 0 111 if loaded 2335 0 111 if loaded 2303 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c152
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c151 2t
