scoreboard players set #ok angel_world 0
execute if loaded 3080 0 80 if loaded 3207 0 80 if loaded 3080 0 207 if loaded 3207 0 207 if loaded 3143 0 143 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/c50
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/c49 2t
