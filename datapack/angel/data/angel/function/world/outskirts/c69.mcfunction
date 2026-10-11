scoreboard players set #ok angel_world 0
execute if loaded 80 32 176 if loaded 207 32 176 if loaded 80 32 271 if loaded 207 32 271 if loaded 143 32 223 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/c70
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/c69 2t
