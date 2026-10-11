scoreboard players set #ok angel_world 0
execute if loaded 1272 32 80 if loaded 1335 32 80 if loaded 1272 32 207 if loaded 1335 32 207 if loaded 1303 32 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/c182
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/c181 2t
