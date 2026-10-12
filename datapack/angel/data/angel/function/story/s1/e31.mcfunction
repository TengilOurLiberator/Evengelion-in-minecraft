scoreboard players set #force angel.story 0
execute at @a[limit=1] run playsound angel:sfx.jolt master @a ~ ~ ~ 1.0 1.0 0
execute at @a[limit=1] run particle minecraft:block{block_state:"minecraft:dirt"} ~ ~0.1 ~ 3 0.1 3 0.15 40 force
execute at @a[limit=1] run particle minecraft:dust_plume ~ ~0.5 ~ 4 0.5 4 0.03 60 force
execute at @a[limit=1] run particle minecraft:falling_dust{block_state:"minecraft:stone"} ~ ~4 ~ 5 1.5 5 0.0 50 force
schedule function angel:story/fx/jolt2 14t
playsound angel:sfx.car_alarms_far master @a 112.0 66.0 168.0 2.0 1.0 0.0
scoreboard players set #step angel.story 32
function angel:story/s1/e32
