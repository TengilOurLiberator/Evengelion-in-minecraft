scoreboard players set #ok angel_world 0
execute if loaded 2272 0 176 if loaded 2331 0 176 if loaded 2272 0 269 if loaded 2331 0 269 if loaded 2301 0 222 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p106
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p105 2t
