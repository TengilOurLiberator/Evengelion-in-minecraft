scoreboard players set #ok angel_world 0
execute if loaded 2160 0 160 if loaded 2383 0 160 if loaded 2160 0 383 if loaded 2383 0 383 if loaded 2271 0 271 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p123
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p122 2t
