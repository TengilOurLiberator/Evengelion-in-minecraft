execute if score #hq.dirty angel.story matches 1 run function angel:story/hq/reset_all
function angel:story/halt
scoreboard players set #running angel.story 0
scoreboard players set #scene angel.story 0
scoreboard players set #step angel.story -1
stopsound @a voice
effect clear @a minecraft:blindness
tellraw @a {"text": "[angel] story stopped", "color": "gray"}
