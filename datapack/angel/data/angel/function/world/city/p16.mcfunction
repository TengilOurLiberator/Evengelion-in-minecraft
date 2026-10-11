scoreboard players set #ok angel_world 0
execute if loaded 984 32 272 if loaded 1111 32 272 if loaded 984 32 335 if loaded 1111 32 335 if loaded 1047 32 303 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p17
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p16 2t
