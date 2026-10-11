scoreboard players set #ok angel_world 0
execute if loaded 2984 0 80 if loaded 3111 0 80 if loaded 2984 0 207 if loaded 3111 0 207 if loaded 3047 0 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/c18
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/c17 2t
