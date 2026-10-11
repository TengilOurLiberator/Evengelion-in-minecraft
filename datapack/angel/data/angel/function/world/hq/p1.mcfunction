scoreboard players set #ok angel_world 0
execute if loaded 2984 0 -16 if loaded 3111 0 -16 if loaded 2984 0 111 if loaded 3111 0 111 if loaded 3047 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p2
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p1 2t
