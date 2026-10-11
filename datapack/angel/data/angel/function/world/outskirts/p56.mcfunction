scoreboard players set #ok angel_world 0
execute if loaded 176 32 -16 if loaded 271 32 -16 if loaded 176 32 111 if loaded 271 32 111 if loaded 223 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p57
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p56 2t
