scoreboard players set #force angel.story 0
data merge entity @e[type=minecraft:mannequin,tag=angel.misato,limit=1] {immovable:1b,NoGravity:1b}
ride @e[type=minecraft:mannequin,tag=angel.misato,limit=1] mount @e[tag=angel.seat_driver,limit=1]
tag @e[type=minecraft:mannequin,tag=angel.misato,limit=1] add angel.mounted
function angel:cast/look {id:"misato",mode:"ahead"}
execute if entity @e[tag=angel.misato,tag=angel.char,limit=1] as @e[tag=angel.rig_car,tag=angel.seat_driver,limit=1] at @s run rotate @e[tag=angel.misato,tag=angel.char,limit=1] facing ^ ^-0.6 ^8
scoreboard players set #step angel.story 90
function angel:story/s2/e90
