# 6.07 BASE (3.46s) Main power connected. Beginning first contact.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 73
scoreboard players set #line angel.story 607
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_07 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Main power connected. Beginning first contact.", "color": "gray"}
