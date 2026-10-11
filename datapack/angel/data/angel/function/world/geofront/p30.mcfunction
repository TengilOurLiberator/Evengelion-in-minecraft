scoreboard players set #ok angel_world 0
execute if loaded 2080 0 -15 if loaded 2207 0 -15 if loaded 2080 0 111 if loaded 2207 0 111 if loaded 2143 0 48 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p31
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p30 2t
