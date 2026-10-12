scoreboard players set #ok angel_world 0
execute if loaded 3080 0 4 if loaded 3148 0 4 if loaded 3080 0 111 if loaded 3148 0 111 if loaded 3114 0 57 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p18
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p17 2t
