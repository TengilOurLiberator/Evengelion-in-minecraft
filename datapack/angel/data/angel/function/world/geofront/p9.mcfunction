scoreboard players set #ok angel_world 0
execute if loaded 1985 0 80 if loaded 2111 0 80 if loaded 1985 0 207 if loaded 2111 0 207 if loaded 2048 0 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p10
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p9 2t
