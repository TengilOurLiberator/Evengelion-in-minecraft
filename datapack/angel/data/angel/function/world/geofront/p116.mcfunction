scoreboard players set #ok angel_world 0
execute if loaded 1936 0 160 if loaded 2159 0 160 if loaded 1936 0 383 if loaded 2159 0 383 if loaded 2047 0 271 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p117
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p116 2t
