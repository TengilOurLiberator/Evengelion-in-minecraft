execute as @e[type=minecraft:mannequin,tag=angel.rei] run function angel:cast/vanish
kill @e[type=minecraft:armor_stand,tag=angel.autoseat_rei]
summon minecraft:mannequin ~ ~ ~ {Tags:["angel.cast","angel.char","angel.rei"],Invulnerable:1b,Silent:1b,NoGravity:1b,immovable:1b,hide_description:1b,profile:{texture:"angel:entity/cast/rei",model:"slim"},attributes:[{id:"minecraft:step_height",base:1.0d}]}
tp @e[type=minecraft:mannequin,tag=angel.rei] ~ ~ ~ ~ 0
team join angel.cast @e[type=minecraft:mannequin,tag=angel.rei]
scoreboard players set #on_rei angel.cast 1
scoreboard players set #walk_rei angel.cast 0
scoreboard players set #look_rei angel.cast 1
scoreboard players set #arrived_rei angel.cast 0
scoreboard players set #np_rei angel.cast 0
scoreboard players set #active angel.cast 1
