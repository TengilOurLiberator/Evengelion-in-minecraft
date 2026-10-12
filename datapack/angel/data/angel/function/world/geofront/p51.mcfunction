scoreboard players set #ok angel_world 0
execute if loaded 2080 0 176 if loaded 2207 0 176 if loaded 2080 0 303 if loaded 2207 0 303 if loaded 2143 0 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/geofront/p52
execute unless score #ok angel_world matches 1 run schedule function angel:world/geofront/p51 2t
