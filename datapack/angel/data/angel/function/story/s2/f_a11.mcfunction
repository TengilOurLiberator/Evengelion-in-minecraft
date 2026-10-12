particle minecraft:dust_plume 179.934 83.6 54.038 3.4 0.4 3.4 0.02 70 force
particle minecraft:block{block_state:"minecraft:dirt"} 179.934 83.6 54.038 3.4 0.2 3.4 0.2 35 force
execute at @a[limit=1] run particle minecraft:dust_plume ~ ~1.0 ~ 4 1.5 4 0.02 50 force
execute at @a[limit=1] run particle minecraft:falling_dust{block_state:"minecraft:dirt"} ~ ~4 ~ 4 1.5 4 0 30 force
