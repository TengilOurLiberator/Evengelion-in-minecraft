# 6.01 BASE (4.12s) Cooling complete. Cage set to launch position.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 86
scoreboard players set #line angel.story 601
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_01 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Cooling complete. Cage set to launch position.", "color": "gray"}
