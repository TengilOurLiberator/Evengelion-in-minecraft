execute if score #locked angel.fight matches 0 if score #odd angel.fight matches 0 run function angel:fight/aim_track
scoreboard players operation #lk angel.fight = #bt angel.fight
scoreboard players remove #lk angel.fight 12
execute if score #t angel.fight >= #lk angel.fight if score #locked angel.fight matches 0 run function angel:fight/aim_lock
execute if score #locked angel.fight matches 1 run function angel:fight/aim_warn
# charging fx: sparks gather at the eyes, a rising note
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^25.36 ^5.35 run particle minecraft:end_rod ~ ~ ~ 1.6 1.6 1.6 0.12 4 force
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] positioned ^ ^25.36 ^5.35 run particle minecraft:electric_spark ~ ~ ~ 1.2 1.2 1.2 0.3 3 force
execute if score #t angel.fight >= #bt angel.fight run function angel:fight/beam_fire
