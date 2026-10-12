scoreboard players set #force angel.story 0
scoreboard players set #fx.air angel.story 0
scoreboard players set #fx.wreck angel.story 0
kill @e[tag=angel.wreck]
execute as @e[tag=angel.rig_ac1,tag=angel.rpart] run data merge entity @s {teleport_duration:59}
execute as @e[tag=angel.rig_ac1,tag=angel.pt_fuselage,limit=1] at @s run tp @e[tag=angel.rig_ac1,tag=angel.rpart] ^ ^28 ^90
execute as @e[tag=angel.rig_ac2,tag=angel.rpart] run data merge entity @s {teleport_duration:59}
execute as @e[tag=angel.rig_ac2,tag=angel.pt_fuselage,limit=1] at @s run tp @e[tag=angel.rig_ac2,tag=angel.rpart] ^ ^28 ^90
execute as @e[tag=angel.rig_ac3,tag=angel.rpart] run data merge entity @s {teleport_duration:59}
execute as @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] at @s run tp @e[tag=angel.rig_ac3,tag=angel.rpart] ^ ^28 ^90
execute as @e[tag=angel.rig_ac4,tag=angel.rpart] run data merge entity @s {teleport_duration:59}
execute as @e[tag=angel.rig_ac4,tag=angel.pt_fuselage,limit=1] at @s run tp @e[tag=angel.rig_ac4,tag=angel.rpart] ^ ^28 ^90
execute as @e[tag=angel.rig_ac5,tag=angel.rpart] run data merge entity @s {teleport_duration:59}
execute as @e[tag=angel.rig_ac5,tag=angel.pt_fuselage,limit=1] at @s run tp @e[tag=angel.rig_ac5,tag=angel.rpart] ^ ^28 ^90
schedule function angel:story/s2/f_cleanup_air 140t
scoreboard players set #step angel.story 33
function angel:story/s2/e33
