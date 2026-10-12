scoreboard players set #ok angel_world 0
execute if loaded 1988 0 176 if loaded 2111 0 176 if loaded 1988 0 303 if loaded 2111 0 303 if loaded 2049 0 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p21
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p20 2t
