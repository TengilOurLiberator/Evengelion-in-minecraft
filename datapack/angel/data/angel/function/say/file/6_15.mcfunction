# 6.15 BASE (3.19s) Unit Zero-One to launch pad. Route clear. All green.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 68
scoreboard players set #line angel.story 615
scoreboard players set #live angel.story 0
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_15 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Unit Zero-One to launch pad. Route clear. All green.", "color": "gray"}
