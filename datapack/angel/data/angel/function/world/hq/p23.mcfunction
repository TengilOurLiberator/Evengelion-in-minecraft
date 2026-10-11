scoreboard players set #ok angel_world 0
execute if loaded 3080 0 80 if loaded 3201 0 80 if loaded 3080 0 203 if loaded 3201 0 203 if loaded 3140 0 141 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p24
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p23 2t
