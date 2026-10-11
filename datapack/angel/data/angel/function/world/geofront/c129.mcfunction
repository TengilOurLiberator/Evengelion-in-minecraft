scoreboard players set #ok angel_world 0
execute if loaded 2176 0 176 if loaded 2303 0 176 if loaded 2176 0 303 if loaded 2303 0 303 if loaded 2239 0 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c130
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c129 2t
