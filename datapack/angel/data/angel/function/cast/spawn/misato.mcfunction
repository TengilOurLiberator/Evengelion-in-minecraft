execute as @e[type=minecraft:mannequin,tag=angel.misato] run function angel:cast/vanish
kill @e[type=minecraft:armor_stand,tag=angel.autoseat_misato]
summon minecraft:mannequin ~ ~ ~ {Tags:["angel.cast","angel.char","angel.misato"],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,profile:{texture:"angel:entity/cast/misato",model:"slim"},attributes:[{id:"minecraft:step_height",base:1.0d}]}
tp @e[type=minecraft:mannequin,tag=angel.misato] ~ ~ ~ ~ 0
team join angel.cast @e[type=minecraft:mannequin,tag=angel.misato]
scoreboard players set #on_misato angel.cast 1
scoreboard players set #walk_misato angel.cast 0
scoreboard players set #look_misato angel.cast 1
scoreboard players set #arrived_misato angel.cast 0
scoreboard players set #np_misato angel.cast 0
scoreboard players set #active angel.cast 1
