execute as @e[type=minecraft:mannequin,tag=angel.gendo] run function angel:cast/vanish
kill @e[type=minecraft:armor_stand,tag=angel.autoseat_gendo]
summon minecraft:mannequin ~ ~ ~ {Tags:["angel.cast","angel.char","angel.gendo"],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,profile:{texture:"angel:entity/cast/gendo",model:"wide"},attributes:[{id:"minecraft:step_height",base:1.0d}]}
tp @e[type=minecraft:mannequin,tag=angel.gendo] ~ ~ ~ ~ 0
team join angel.cast @e[type=minecraft:mannequin,tag=angel.gendo]
scoreboard players set #on_gendo angel.cast 1
scoreboard players set #walk_gendo angel.cast 0
scoreboard players set #look_gendo angel.cast 1
scoreboard players set #arrived_gendo angel.cast 0
scoreboard players set #np_gendo angel.cast 0
scoreboard players set #active angel.cast 1
