execute if entity @e[tag=angel.ob_target,limit=1] run tp @e[tag=angel.ob_wp] @e[tag=angel.ob_target,limit=1]
execute unless score #ob.b angel.story = #ob.bl angel.story if entity @e[tag=angel.ob_label,limit=1] run function angel:story/ob/band_apply
execute at @e[tag=angel.ob_target,limit=1] run particle minecraft:end_rod ~ ~1.0 ~ 0.12 0.9 0.12 0.004 1 force
