scoreboard players set #ok angel_world 0
execute if loaded 176 32 176 if loaded 271 32 176 if loaded 176 32 271 if loaded 271 32 271 if loaded 223 32 223 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/c104
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/c103 2t
