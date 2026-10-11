execute at @a[limit=1] run particle minecraft:dust_plume ~ ~0.5 ~ 5 1 5 0.03 80 force
execute at @a[limit=1] run particle minecraft:falling_dust{block_state:"minecraft:dirt"} ~ ~5 ~ 6 2 6 0.0 60 force
playsound minecraft:entity.generic.explode master @a 194.0 85.5 56.0 6.0 0.35 0.8
