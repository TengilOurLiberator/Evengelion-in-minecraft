# 5.21 BASE (5.93s) Impact, surface level. The Angel is directly above headquarters.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 123
scoreboard players set #line angel.story 521
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.5_21 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Impact, surface level. The Angel is directly above headquarters.", "color": "gray"}
