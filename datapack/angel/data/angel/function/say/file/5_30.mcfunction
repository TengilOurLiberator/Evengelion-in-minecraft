# 5.30 BASE (5.48s) Current operation halted. Beginning system restart, Unit Zero-One.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 114
scoreboard players set #line angel.story 530
scoreboard players set #live angel.story 0
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.5_30 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Current operation halted. Beginning system restart, Unit Zero-One.", "color": "gray"}
