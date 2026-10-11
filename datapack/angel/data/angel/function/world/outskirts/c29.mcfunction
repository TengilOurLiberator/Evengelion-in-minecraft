scoreboard players set #ok angel_world 0
execute if loaded -16 32 176 if loaded 111 32 176 if loaded -16 32 271 if loaded 111 32 271 if loaded 47 32 223 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/c30
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/c29 2t
