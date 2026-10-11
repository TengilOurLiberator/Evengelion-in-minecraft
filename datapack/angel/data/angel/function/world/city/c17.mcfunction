scoreboard players set #ok angel_world 0
execute if loaded 984 32 80 if loaded 1111 32 80 if loaded 984 32 207 if loaded 1111 32 207 if loaded 1047 32 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/c18
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/c17 2t
