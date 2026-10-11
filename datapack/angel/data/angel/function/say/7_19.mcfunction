# 7.19 BASE (3.57s) Unit Zero-One silent. Pilot status unknown.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 75
scoreboard players set #line angel.story 719
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.7_19 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Unit Zero-One silent. Pilot status unknown.", "color": "gray"}
