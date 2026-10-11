# 7.15 BASE (3.90s) Target silent. Pattern blue is gone. The Angel is destroyed.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 82
scoreboard players set #line angel.story 715
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.7_15 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Target silent. Pattern blue is gone. The Angel is destroyed.", "color": "gray"}
