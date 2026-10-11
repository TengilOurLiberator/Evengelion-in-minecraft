scoreboard players set #ok angel_world 0
execute if loaded 3080 0 -16 if loaded 3207 0 -16 if loaded 3080 0 111 if loaded 3207 0 111 if loaded 3143 0 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/hq/c34
execute unless score #ok angel_world matches 1 run schedule function angel:world/hq/c33 2t
