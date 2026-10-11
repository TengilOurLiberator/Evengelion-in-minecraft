scoreboard players set #ok angel_world 0
execute if loaded 176 32 -16 if loaded 271 32 -16 if loaded 176 32 111 if loaded 271 32 111 if loaded 223 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/c82
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/c81 2t
