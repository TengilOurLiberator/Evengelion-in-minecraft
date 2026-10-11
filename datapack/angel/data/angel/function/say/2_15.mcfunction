# 2.15 BASE (6.36s) All stations. United Nations forces have withdrawn. Command of this operation passes to NERV, effective now.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 131
scoreboard players set #line angel.story 215
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.2_15 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> All stations. United Nations forces have withdrawn. Command of this operation passes to NERV, effective now.", "color": "gray"}
