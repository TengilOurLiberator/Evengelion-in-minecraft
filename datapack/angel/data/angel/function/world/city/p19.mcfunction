scoreboard players set #ok angel_world 0
execute if loaded 1080 32 -16 if loaded 1207 32 -16 if loaded 1080 32 111 if loaded 1207 32 111 if loaded 1143 32 47 run scoreboard players set #ok angel_world 1
execute if score #ok angel_world matches 1 run function angel:world/city/p20
execute unless score #ok angel_world matches 1 run schedule function angel:world/city/p19 2t
