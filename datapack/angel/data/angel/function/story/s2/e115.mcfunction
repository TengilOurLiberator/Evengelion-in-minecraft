scoreboard players set #force angel.story 0
execute as @e[type=minecraft:block_display,tag=angel.mon] run data merge entity @s {Glowing:0b}
scoreboard players set #fx.crater angel.story 0
function angel:story/snd/stop_music
scoreboard players set #fx.wreck angel.story 0
kill @e[tag=angel.wreck]
scoreboard players set #fx.air angel.story 0
kill @e[tag=angel.cmark]
kill @e[tag=angel.rig_ac1]
kill @e[tag=angel.rig_ac2]
kill @e[tag=angel.rig_ac3]
kill @e[tag=angel.rig_ac4]
kill @e[tag=angel.rig_ac5]
kill @e[tag=angel.rig_ac3d]
kill @e[tag=angel.trc]
kill @e[tag=angel.flash]
kill @e[tag=angel.lvtmp]
scoreboard players set #fx.leave angel.story 0
kill @e[tag=angel.cloud]
kill @e[tag=angel.ia_push]
kill @e[tag=angel.ia_car]
kill @e[tag=angel.mwhite]
kill @e[tag=angel.mblack]
scoreboard players set #step angel.story 116
function angel:story/s2/e116
