scoreboard players set #ok angel_world 0
execute if loaded 1936 0 -64 if loaded 2159 0 -64 if loaded 1936 0 159 if loaded 2159 0 159 if loaded 2047 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p114
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p113 2t
