scoreboard players set #ok angel_world 0
execute if loaded 2160 0 -64 if loaded 2383 0 -64 if loaded 2160 0 159 if loaded 2383 0 159 if loaded 2271 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p120
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p119 2t
