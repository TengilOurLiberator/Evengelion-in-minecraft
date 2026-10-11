kill @e[type=minecraft:mannequin,tag=angel.rei_uniform]
kill @e[type=minecraft:armor_stand,tag=angel.autoseat_rei_uniform]
summon minecraft:mannequin ~ ~ ~ {Tags:["angel.cast","angel.char","angel.rei_uniform"],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,profile:{texture:"angel:entity/cast/rei_uniform",model:"slim"},attributes:[{id:"minecraft:step_height",base:1.0d}]}
tp @e[type=minecraft:mannequin,tag=angel.rei_uniform] ~ ~ ~ ~ 0
team join angel.cast @e[type=minecraft:mannequin,tag=angel.rei_uniform]
scoreboard players set #on_rei_uniform angel.cast 1
scoreboard players set #walk_rei_uniform angel.cast 0
scoreboard players set #look_rei_uniform angel.cast 1
scoreboard players set #arrived_rei_uniform angel.cast 0
scoreboard players set #active angel.cast 1
