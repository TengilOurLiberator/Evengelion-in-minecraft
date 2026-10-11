scoreboard players set #ok angel_world 0
execute if loaded 2176 0 272 if loaded 2269 0 272 if loaded 2176 0 331 if loaded 2269 0 331 if loaded 2222 0 301 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p93
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p92 2t
