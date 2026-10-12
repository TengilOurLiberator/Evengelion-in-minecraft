execute at @e[tag=angel.rigpos,limit=1] run function angel:story/hq/rig2_spawn
execute at @e[tag=angel.rigpos,limit=1] run playsound angel:sfx.rig_tear master @a ~ ~ ~ 5.0 1.0 1.0
execute at @e[tag=angel.rigpos,limit=1] run particle minecraft:flash{color:[1.0,0.85,0.5,1.0]} ~ ~32.0 ~ 0 0 0 0 1 force
execute if score #rg.near angel.story matches 1 as @a[limit=1] at @s rotated ~ 0 positioned ^ ^4.5 ^1.2 run function angel:story/hq/rig2_bits_spawn
schedule function angel:story/hq/rig2_bits_fall 2t
schedule function angel:story/hq/rig2_bits_kill 30t
function angel:story/hq/rig2_k0
schedule function angel:story/hq/rig2_k1 6t
schedule function angel:story/hq/rig2_k2 20t
schedule function angel:story/hq/rig2_k3 34t
function angel:story/hq/rig2_rain_a
schedule function angel:story/hq/rig2_rain_b 8t
schedule function angel:story/hq/rig2_rain_b2 16t
schedule function angel:story/hq/rig2_rain_b3 24t
schedule function angel:story/hq/rig2_rain_b4 32t
schedule function angel:story/hq/rig2_bits_spawn2 14t
schedule function angel:story/hq/rig2_bits_fall2 16t
schedule function angel:story/hq/rig2_bits_kill2 40t
schedule function angel:story/hq/rig2_fall 44t
