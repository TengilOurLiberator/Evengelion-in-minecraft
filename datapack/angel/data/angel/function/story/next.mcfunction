function angel:story/skip
scoreboard players set #talking angel.story 0
scoreboard players set #line_left angel.story 0
scoreboard players set #live angel.story 0
stopsound @a voice
scoreboard players set #force angel.story 1
tellraw @a {"text": "[angel] step skipped", "color": "gray"}
