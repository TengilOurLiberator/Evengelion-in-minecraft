execute as @e[type=minecraft:mannequin,tag=angel.medic1] run function angel:cast/vanish
kill @e[type=minecraft:armor_stand,tag=angel.autoseat_medic1]
summon minecraft:mannequin ~ ~ ~ {Tags:["angel.cast","angel.medic","angel.medic1"],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,profile:{texture:"angel:entity/cast/medic1",model:"wide"},attributes:[{id:"minecraft:step_height",base:1.0d}]}
tp @e[type=minecraft:mannequin,tag=angel.medic1] ~ ~ ~ ~ 0
team join angel.cast @e[type=minecraft:mannequin,tag=angel.medic1]
scoreboard players set #on_medic1 angel.cast 1
scoreboard players set #walk_medic1 angel.cast 0
scoreboard players set #look_medic1 angel.cast 1
scoreboard players set #arrived_medic1 angel.cast 0
scoreboard players set #np_medic1 angel.cast 0
scoreboard players set #active angel.cast 1
