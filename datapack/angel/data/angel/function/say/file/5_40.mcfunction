# 5.40 BASE (5.65s) Armor layer eighteen breached. Estimated time to headquarters: nine minutes.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 117
scoreboard players set #line angel.story 540
scoreboard players set #live angel.story 0
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.5_40 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Armor layer eighteen breached. Estimated time to headquarters: nine minutes.", "color": "gray"}
