scoreboard players set #ok angel_world 0
execute if loaded 80 32 80 if loaded 207 32 80 if loaded 80 32 207 if loaded 207 32 207 if loaded 143 32 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p40
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p39 2t
