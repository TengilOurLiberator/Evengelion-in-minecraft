scoreboard players set #fx.smoke angel.story 1
execute at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run particle minecraft:explosion_emitter ~ ~ ~ 0 0 0 0 1 force
execute at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run particle minecraft:flash{color:[1.0,0.8,0.4,1.0]} ~ ~1 ~ 0 0 0 0 1 force
execute at @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run particle minecraft:lava ~ ~ ~ 3 1 3 0.1 40 force
playsound angel:sfx.explosion_far master @a 150.0 100.0 128.0 1.5 1.1 0.0
