scoreboard players set #ok angel_world 0
execute if loaded 160 32 160 if loaded 319 32 160 if loaded 160 32 319 if loaded 319 32 319 if loaded 239 32 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p91
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p90 2t
