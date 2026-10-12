scoreboard players set #force angel.story 0
scoreboard players set #fx.air angel.story 0
scoreboard players set #fx.lt angel.story 0
scoreboard players set #fx.leave angel.story 1
scoreboard players set #k36000 angel.story 36000
scoreboard players set #fx.smoke angel.story 0
schedule clear angel:story/fx/fire1b
schedule clear angel:story/fx/fire1c
schedule clear angel:story/fx/fire2b
schedule clear angel:story/fx/fire2c
schedule clear angel:story/fx/fire3b
schedule clear angel:story/fx/fire3c
schedule clear angel:story/fx/fire4b
schedule clear angel:story/fx/fire4c
schedule clear angel:story/fx/fire5b
schedule clear angel:story/fx/fire5c
kill @e[tag=angel.trc]
kill @e[tag=angel.flash]
execute as @e[tag=angel.rig_ac1,tag=angel.pt_fuselage,limit=1] at @s run function angel:story/fx/leave_aim1
execute as @e[tag=angel.rig_ac2,tag=angel.pt_fuselage,limit=1] at @s run function angel:story/fx/leave_aim2
execute as @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] at @s run function angel:story/fx/leave_aim3
execute as @e[tag=angel.rig_ac4,tag=angel.pt_fuselage,limit=1] at @s run function angel:story/fx/leave_aim4
execute as @e[tag=angel.rig_ac5,tag=angel.pt_fuselage,limit=1] at @s run function angel:story/fx/leave_aim5
playsound angel:sfx.jet_pass master @a 174.5 164.0 128.5 4.0 1.0 0.3
scoreboard players set #step angel.story 33
function angel:story/s2/e33
