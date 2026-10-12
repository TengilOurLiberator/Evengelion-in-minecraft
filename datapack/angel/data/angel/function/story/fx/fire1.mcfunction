execute as @e[tag=angel.rig_ac1,tag=angel.pt_fuselage,limit=1] at @s facing entity @e[tag=angel.cmark,limit=1] feet run function angel:story/fx/tr_spawn
schedule function angel:story/fx/fire1b 3t append
schedule function angel:story/fx/fire1c 6t append
