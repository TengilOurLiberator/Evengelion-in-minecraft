# 6.14 BASE (4.42s) All safeties off. Internal batteries charged. External power steady.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 92
scoreboard players set #line angel.story 614
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_14 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> All safeties off. Internal batteries charged. External power steady.", "color": "gray"}
