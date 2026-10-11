scoreboard players set #ok angel_world 0
execute if loaded -16 32 -16 if loaded 111 32 -16 if loaded -16 32 111 if loaded 111 32 111 if loaded 47 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p2
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p1 2t
