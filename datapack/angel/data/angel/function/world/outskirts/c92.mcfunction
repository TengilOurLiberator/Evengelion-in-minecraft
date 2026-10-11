scoreboard players set #ok angel_world 0
execute if loaded 176 32 80 if loaded 271 32 80 if loaded 176 32 207 if loaded 271 32 207 if loaded 223 32 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/c93
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/c92 2t
