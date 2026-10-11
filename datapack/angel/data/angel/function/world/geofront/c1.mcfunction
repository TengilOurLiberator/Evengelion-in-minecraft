scoreboard players set #ok angel_world 0
execute if loaded 1984 0 -16 if loaded 2111 0 -16 if loaded 1984 0 111 if loaded 2111 0 111 if loaded 2047 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/c2
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/c1 2t
