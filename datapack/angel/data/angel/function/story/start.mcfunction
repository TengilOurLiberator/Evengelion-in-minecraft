function angel:story/load
execute if score #hq.dirty angel.story matches 1 run function angel:story/hq/reset_all
function angel:story/halt
stopsound @a voice
effect clear @a minecraft:blindness
scoreboard players set #running angel.story 1
scoreboard players set #consent angel.story 0
gamemode adventure @a
clear @a minecraft:written_book
clear @a minecraft:paper
function angel:story/scene {n:1}
