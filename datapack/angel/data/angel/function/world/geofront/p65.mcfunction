scoreboard players set #ok angel_world 0
execute if loaded 2176 0 -12 if loaded 2303 0 -12 if loaded 2176 0 111 if loaded 2303 0 111 if loaded 2239 0 49 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p66
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p65 2t
