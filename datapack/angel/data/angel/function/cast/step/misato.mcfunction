execute if score #walk_misato angel.cast matches 2 run return run function angel:cast/settle/misato
scoreboard players add #t_misato angel.cast 1
execute if score #t_misato angel.cast > #tmax_misato angel.cast run return run function angel:cast/force/misato
execute store result entity @s Motion[0] double 0.00001 run scoreboard players get #mx_misato angel.cast
execute store result entity @s Motion[2] double 0.00001 run scoreboard players get #mz_misato angel.cast
execute store result score #cx angel.cast run data get entity @s Pos[0] 100
execute store result score #cz angel.cast run data get entity @s Pos[2] 100
scoreboard players operation #dx angel.cast = #tx_misato angel.cast
scoreboard players operation #dz angel.cast = #tz_misato angel.cast
scoreboard players operation #dx angel.cast -= #cx angel.cast
scoreboard players operation #dz angel.cast -= #cz angel.cast
scoreboard players set #near angel.cast 0
execute if score #dx angel.cast matches -3000..3000 if score #dz angel.cast matches -3000..3000 run scoreboard players set #near angel.cast 1
execute if score #near angel.cast matches 1 run scoreboard players operation #dx angel.cast *= #dx angel.cast
execute if score #near angel.cast matches 1 run scoreboard players operation #dz angel.cast *= #dz angel.cast
execute if score #near angel.cast matches 1 run scoreboard players operation #dx angel.cast += #dz angel.cast
scoreboard players operation #rr angel.cast = #sp_misato angel.cast
scoreboard players add #rr angel.cast 2
scoreboard players operation #rr angel.cast *= #rr angel.cast
execute if score #near angel.cast matches 1 if score #dx angel.cast <= #rr angel.cast run function angel:cast/arrive/misato
