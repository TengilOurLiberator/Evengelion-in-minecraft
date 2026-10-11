# 6.02 BASE (2.69s) Entry plug inserted. Plug locked.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 58
scoreboard players set #line angel.story 602
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_02 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Entry plug inserted. Plug locked.", "color": "gray"}
