scoreboard players set #force angel.story 0
playsound minecraft:entity.generic.explode master @a 200.0 64.0 128.0 8.0 0.45 0.9
playsound minecraft:entity.warden.emerge master @a 200.0 64.0 128.0 8.0 0.5 0.8
execute at @a[limit=1] run particle minecraft:block{block_state:"minecraft:dirt"} ~ ~0.1 ~ 3 0.1 3 0.15 40 force
execute at @a[limit=1] run particle minecraft:dust_plume ~ ~0.5 ~ 4 0.5 4 0.03 60 force
execute at @a[limit=1] run particle minecraft:falling_dust{block_state:"minecraft:stone"} ~ ~4 ~ 5 1.5 5 0.0 50 force
schedule function angel:story/fx/jolt2 14t
scoreboard players set #step angel.story 20
function angel:story/s1/e20
