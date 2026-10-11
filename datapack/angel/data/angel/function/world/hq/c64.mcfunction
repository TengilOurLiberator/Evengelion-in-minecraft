forceload remove 2984 -16 3111 111
forceload remove 2984 80 3111 207
forceload remove 3080 -16 3207 111
forceload remove 3080 80 3207 207
say [angel] cleared hq
scoreboard players operation #go angel_world = #rebuild angel_world
scoreboard players set #rebuild angel_world 0
execute if score #go angel_world matches 1 run function angel:world/hq/p0
