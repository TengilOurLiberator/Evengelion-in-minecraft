kill @e[tag=angel.mwhite]
execute at @a[limit=1] anchored eyes positioned ^ ^ ^ run function angel:story/s2/blackout
execute at @a[limit=1] run particle minecraft:dust_plume ~ ~0.5 ~ 5 1 5 0.03 80 force
execute at @a[limit=1] run particle minecraft:falling_dust{block_state:"minecraft:dirt"} ~ ~5 ~ 6 2 6 0.0 60 force
