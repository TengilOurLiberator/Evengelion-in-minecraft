scoreboard players set #ok angel_world 0
execute if loaded 2080 0 80 if loaded 2207 0 80 if loaded 2080 0 207 if loaded 2207 0 207 if loaded 2143 0 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c66
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c65 2t
