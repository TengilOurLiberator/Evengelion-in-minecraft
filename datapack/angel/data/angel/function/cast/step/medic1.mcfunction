execute if score #walk_medic1 angel.cast matches 2 run return run function angel:cast/settle/medic1
scoreboard players add #t_medic1 angel.cast 1
execute if score #t_medic1 angel.cast > #tmax_medic1 angel.cast run return run function angel:cast/force/medic1
execute store result entity @s Motion[0] double 0.00001 run scoreboard players get #mx_medic1 angel.cast
execute store result entity @s Motion[2] double 0.00001 run scoreboard players get #mz_medic1 angel.cast
execute store result score #cx angel.cast run data get entity @s Pos[0] 100
execute store result score #cz angel.cast run data get entity @s Pos[2] 100
scoreboard players operation #dx angel.cast = #tx_medic1 angel.cast
scoreboard players operation #dz angel.cast = #tz_medic1 angel.cast
scoreboard players operation #dx angel.cast -= #cx angel.cast
scoreboard players operation #dz angel.cast -= #cz angel.cast
scoreboard players set #near angel.cast 0
execute if score #dx angel.cast matches -3000..3000 if score #dz angel.cast matches -3000..3000 run scoreboard players set #near angel.cast 1
execute if score #near angel.cast matches 1 run scoreboard players operation #dx angel.cast *= #dx angel.cast
execute if score #near angel.cast matches 1 run scoreboard players operation #dz angel.cast *= #dz angel.cast
execute if score #near angel.cast matches 1 run scoreboard players operation #dx angel.cast += #dz angel.cast
scoreboard players operation #rr angel.cast = #sp_medic1 angel.cast
scoreboard players add #rr angel.cast 2
scoreboard players operation #rr angel.cast *= #rr angel.cast
execute if score #near angel.cast matches 1 if score #dx angel.cast <= #rr angel.cast run function angel:cast/arrive/medic1
