scoreboard players set #ok angel_world 0
execute if loaded 1080 32 80 if loaded 1207 32 80 if loaded 1080 32 207 if loaded 1207 32 207 if loaded 1143 32 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p25
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p24 2t
