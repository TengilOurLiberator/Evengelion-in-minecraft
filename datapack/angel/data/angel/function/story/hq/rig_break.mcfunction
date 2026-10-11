function angel:story/hq/rig_break_hop
schedule function angel:story/hq/rig_break_down 7t
particle minecraft:block{block_state:"minecraft:iron_block"} 3096.5 65.0 78.5 2.2 0.4 2.2 0.25 90 force
particle minecraft:block{block_state:"minecraft:copper_block"} 3096.5 65.0 78.5 2.0 0.4 2.0 0.2 50 force
particle minecraft:electric_spark 3096.5 65.0 78.5 2.5 0.6 2.5 0.3 80 force
particle minecraft:explosion 3096.5 65.5 78.5 1.5 0.2 1.5 0 3 force
particle minecraft:large_smoke 3096.5 65.5 78.5 2.5 0.5 2.5 0.03 30 force
playsound angel:sfx.rig_crash master @a 3096.5 66.0 78.5 3.0 0.9 0.9
