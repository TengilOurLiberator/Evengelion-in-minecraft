playsound minecraft:entity.generic.explode master @a 190.0 64.0 128.0 6.0 0.35 0.8
execute at @a[limit=1] run particle minecraft:dust_plume ~ ~0.5 ~ 4 0.5 4 0.03 40 force
execute at @a[limit=1] run particle minecraft:falling_dust{block_state:"minecraft:stone"} ~ ~4 ~ 5 1.5 5 0.0 30 force
