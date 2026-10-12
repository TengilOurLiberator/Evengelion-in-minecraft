# 6.04 BASE (1.29s) Flooding the plug.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 30
scoreboard players set #line angel.story 604
scoreboard players set #live angel.story 0
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_04 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Flooding the plug.", "color": "gray"}
