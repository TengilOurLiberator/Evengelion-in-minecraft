scoreboard players set #force angel.story 0
effect give @a minecraft:blindness 7 0 true
function angel:story/snd/stop_bed
execute at @a[limit=1] run playsound minecraft:block.beacon.ambient master @a ~ ~ ~ 0.9 0.5 1.0
scoreboard players set #step angel.story 131
function angel:story/s4/e131
