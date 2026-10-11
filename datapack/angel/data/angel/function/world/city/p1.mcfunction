scoreboard players set #ok angel_world 0
execute if loaded 984 32 -16 if loaded 1111 32 -16 if loaded 984 32 111 if loaded 1111 32 111 if loaded 1047 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p2
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p1 2t
