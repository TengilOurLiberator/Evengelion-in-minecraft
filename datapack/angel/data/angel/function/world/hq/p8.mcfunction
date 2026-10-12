scoreboard players set #ok angel_world 0
execute if loaded 2984 0 80 if loaded 3111 0 80 if loaded 2984 0 204 if loaded 3111 0 204 if loaded 3047 0 142 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p9
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p8 2t
