scoreboard players set #ok angel_world 0
execute if loaded 936 32 160 if loaded 1151 32 160 if loaded 936 32 383 if loaded 1151 32 383 if loaded 1043 32 271 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p72
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p71 2t
