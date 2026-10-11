kill @e[type=minecraft:mannequin,tag=angel.medic2]
kill @e[type=minecraft:armor_stand,tag=angel.autoseat_medic2]
summon minecraft:mannequin ~ ~ ~ {Tags:["angel.cast","angel.medic","angel.medic2"],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,profile:{texture:"angel:entity/cast/medic2",model:"slim"},attributes:[{id:"minecraft:step_height",base:1.0d}]}
tp @e[type=minecraft:mannequin,tag=angel.medic2] ~ ~ ~ ~ 0
team join angel.cast @e[type=minecraft:mannequin,tag=angel.medic2]
scoreboard players set #on_medic2 angel.cast 1
scoreboard players set #walk_medic2 angel.cast 0
scoreboard players set #look_medic2 angel.cast 1
scoreboard players set #arrived_medic2 angel.cast 0
scoreboard players set #active angel.cast 1
