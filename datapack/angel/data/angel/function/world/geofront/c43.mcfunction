scoreboard players set #ok angel_world 0
execute if loaded 1984 0 272 if loaded 2111 0 272 if loaded 1984 0 335 if loaded 2111 0 335 if loaded 2047 0 303 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c44
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c43 2t
