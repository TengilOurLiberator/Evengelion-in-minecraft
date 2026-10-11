scoreboard players set #ok angel_world 0
execute if loaded 1080 32 176 if loaded 1207 32 176 if loaded 1080 32 303 if loaded 1207 32 303 if loaded 1143 32 239 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/c91
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/c90 2t
