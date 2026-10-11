scoreboard players set #ok angel_world 0
execute if loaded 1998 0 -2 if loaded 2111 0 -2 if loaded 1998 0 111 if loaded 2111 0 111 if loaded 2054 0 54 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p2
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p1 2t
