execute as @e[type=minecraft:mannequin,tag=angel.ritsuko] run function angel:cast/vanish
kill @e[type=minecraft:armor_stand,tag=angel.autoseat_ritsuko]
summon minecraft:mannequin ~ ~ ~ {Tags:["angel.cast","angel.char","angel.ritsuko"],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,profile:{texture:"angel:entity/cast/ritsuko",model:"slim"},attributes:[{id:"minecraft:step_height",base:1.0d}]}
tp @e[type=minecraft:mannequin,tag=angel.ritsuko] ~ ~ ~ ~ 0
team join angel.cast @e[type=minecraft:mannequin,tag=angel.ritsuko]
scoreboard players set #on_ritsuko angel.cast 1
scoreboard players set #walk_ritsuko angel.cast 0
scoreboard players set #look_ritsuko angel.cast 1
scoreboard players set #arrived_ritsuko angel.cast 0
scoreboard players set #np_ritsuko angel.cast 0
scoreboard players set #active angel.cast 1
