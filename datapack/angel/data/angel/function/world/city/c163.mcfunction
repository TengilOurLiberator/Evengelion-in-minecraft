scoreboard players set #ok angel_world 0
execute if loaded 1176 32 272 if loaded 1303 32 272 if loaded 1176 32 335 if loaded 1303 32 335 if loaded 1239 32 303 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/c164
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/c163 2t
