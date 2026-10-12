scoreboard players set #ok angel_world 0
execute if loaded 160 32 -64 if loaded 319 32 -64 if loaded 160 32 159 if loaded 319 32 159 if loaded 239 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p88
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p87 2t
