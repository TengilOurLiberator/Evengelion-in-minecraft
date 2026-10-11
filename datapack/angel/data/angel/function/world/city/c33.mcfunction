scoreboard players set #ok angel_world 0
execute if loaded 984 32 176 if loaded 1111 32 176 if loaded 984 32 303 if loaded 1111 32 303 if loaded 1047 32 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/c34
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/c33 2t
