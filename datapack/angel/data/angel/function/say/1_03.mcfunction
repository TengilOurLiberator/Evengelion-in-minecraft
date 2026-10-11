# 1.03 BASE (8.52s) Attention. A hostile object has come ashore and is moving inland. Anyone still above ground, get below. Now.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 174
scoreboard players set #line angel.story 103
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.1_03 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Attention. A hostile object has come ashore and is moving inland. Anyone still above ground, get below. Now.", "color": "gray"}
