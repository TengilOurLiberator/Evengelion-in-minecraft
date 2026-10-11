scoreboard players set #ok angel_world 0
execute if loaded 1984 0 176 if loaded 2111 0 176 if loaded 1984 0 303 if loaded 2111 0 303 if loaded 2047 0 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c30
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c29 2t
