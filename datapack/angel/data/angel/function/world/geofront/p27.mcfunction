scoreboard players set #ok angel_world 0
execute if loaded 2050 0 272 if loaded 2111 0 272 if loaded 2050 0 321 if loaded 2111 0 321 if loaded 2080 0 296 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p28
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p27 2t
