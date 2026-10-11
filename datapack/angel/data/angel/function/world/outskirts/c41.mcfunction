scoreboard players set #ok angel_world 0
execute if loaded 80 32 -16 if loaded 207 32 -16 if loaded 80 32 111 if loaded 207 32 111 if loaded 143 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/outskirts/c42
execute unless score #ok angel_world matches 1 run schedule function angel:world/outskirts/c41 2t
