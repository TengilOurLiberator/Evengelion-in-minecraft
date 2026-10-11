scoreboard players set #ok angel_world 0
execute if loaded -16 32 80 if loaded 111 32 80 if loaded -16 32 207 if loaded 111 32 207 if loaded 47 32 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/p12
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/p11 2t
