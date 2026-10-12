execute if score #rg.sgn angel.story matches 1 run function angel:story/hq/rig2_break_p
execute if score #rg.sgn angel.story matches -1 run function angel:story/hq/rig2_break_n
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:block{block_state:"minecraft:iron_block"} ~ 65.0 ~ 2.2 0.4 2.2 0.25 90 force
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:block{block_state:"minecraft:copper_block"} ~ 65.0 ~ 2.0 0.4 2.0 0.2 50 force
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:electric_spark ~ 65.0 ~ 2.5 0.6 2.5 0.3 80 force
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:explosion ~ 65.5 ~ 1.5 0.2 1.5 0 3 force
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:large_smoke ~ 65.5 ~ 2.5 0.5 2.5 0.03 30 force
execute at @e[tag=angel.rigpos,limit=1] run playsound angel:sfx.rig_crash master @a ~ 66.0 ~ 4.0 0.95 1.0
kill @e[tag=angel.rigshadow]
