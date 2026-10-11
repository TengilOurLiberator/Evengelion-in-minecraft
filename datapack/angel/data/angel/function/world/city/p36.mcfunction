scoreboard players set #ok angel_world 0
execute if loaded 1176 32 -16 if loaded 1303 32 -16 if loaded 1176 32 111 if loaded 1303 32 111 if loaded 1239 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p37
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p36 2t
