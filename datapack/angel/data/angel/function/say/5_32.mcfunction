# 5.32 BASE (6.48s) Warning. Unit Zero-One, right arm in motion. Restraints broken. No pilot aboard.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 134
scoreboard players set #line angel.story 532
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.5_32 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Warning. Unit Zero-One, right arm in motion. Restraints broken. No pilot aboard.", "color": "gray"}
