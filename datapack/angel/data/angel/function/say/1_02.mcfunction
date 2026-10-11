# 1.02 BASE (4.61s) Residents are to go to their assigned shelter at once. This message will repeat.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 96
scoreboard players set #line angel.story 102
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.1_02 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Residents are to go to their assigned shelter at once. This message will repeat.", "color": "gray"}
