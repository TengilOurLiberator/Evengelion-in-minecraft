$tp @e[tag=angel.gurney] ~ ~ ~ facing $(x) ~ $(z)
execute at @s run function angel:cast/gm_followers
execute store result score #gtx angel.cast run data get storage angel:cast gm.x 100
execute store result score #gtz angel.cast run data get storage angel:cast gm.z 100
execute store result score #gty angel.cast run data get storage angel:cast gm.y 100
execute store result score #gsp angel.cast run data get storage angel:cast gm.speed 100
execute if score #gsp angel.cast matches ..0 run scoreboard players set #gsp angel.cast 1
execute store result score #cx angel.cast run data get entity @s Pos[0] 100
execute store result score #cy angel.cast run data get entity @s Pos[1] 100
execute store result score #cz angel.cast run data get entity @s Pos[2] 100
scoreboard players operation #dx angel.cast = #gtx angel.cast
scoreboard players operation #dz angel.cast = #gtz angel.cast
scoreboard players operation #gdy angel.cast = #gty angel.cast
scoreboard players operation #dx angel.cast -= #cx angel.cast
scoreboard players operation #dz angel.cast -= #cz angel.cast
scoreboard players operation #gdy angel.cast -= #cy angel.cast
scoreboard players operation #n angel.cast = #dx angel.cast
scoreboard players operation #n angel.cast *= #dx angel.cast
scoreboard players operation #dz angel.cast *= #dz angel.cast
scoreboard players operation #n angel.cast += #dz angel.cast
function angel:cast/isqrt
scoreboard players operation #gn angel.cast = #s angel.cast
scoreboard players operation #gn angel.cast /= #gsp angel.cast
execute if score #gn angel.cast matches ..0 run scoreboard players set #gn angel.cast 1
scoreboard players operation #gdy angel.cast *= #k1000 angel.cast
scoreboard players operation #gdy angel.cast /= #gn angel.cast
execute if score #gdy angel.cast matches -199..199 run scoreboard players set #gdy angel.cast 0
execute store result storage angel:cast gm.dy double 0.00001 run scoreboard players get #gdy angel.cast
scoreboard players set #look_medic1 angel.cast 0
scoreboard players set #look_medic2 angel.cast 0
execute as @e[tag=angel.seat_gurney] on passengers run function angel:cast/align_yaw
scoreboard players set #arrived_gurney angel.cast 0
scoreboard players set #gmove angel.cast 1
scoreboard players set #active angel.cast 1
