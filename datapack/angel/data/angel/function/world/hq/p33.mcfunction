scoreboard players set #ok angel_world 0
execute if loaded 2936 0 160 if loaded 3151 0 160 if loaded 2936 0 255 if loaded 3151 0 255 if loaded 3043 0 207 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p34
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p33 2t
