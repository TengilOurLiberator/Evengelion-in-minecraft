scoreboard players set #ok angel_world 0
execute if loaded 2936 0 -64 if loaded 3151 0 -64 if loaded 2936 0 159 if loaded 3151 0 159 if loaded 3043 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/p31
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/p30 2t
