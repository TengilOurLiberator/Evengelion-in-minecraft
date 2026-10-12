scoreboard players set #ok angel_world 0
execute if loaded 1272 32 -16 if loaded 1335 32 -16 if loaded 1272 32 111 if loaded 1335 32 111 if loaded 1303 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p57
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p56 2t
