scoreboard players set #ok angel_world 0
execute if loaded 1272 32 176 if loaded 1335 32 176 if loaded 1272 32 303 if loaded 1335 32 303 if loaded 1303 32 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p63
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p62 2t
