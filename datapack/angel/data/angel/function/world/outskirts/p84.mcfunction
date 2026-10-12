scoreboard players set #ok angel_world 0
execute if loaded -64 32 160 if loaded 159 32 160 if loaded -64 32 319 if loaded 159 32 319 if loaded 47 32 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p85
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p84 2t
