scoreboard players set #ok angel_world 0
execute if loaded 936 32 -64 if loaded 1151 32 -64 if loaded 936 32 159 if loaded 1151 32 159 if loaded 1043 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p69
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p68 2t
