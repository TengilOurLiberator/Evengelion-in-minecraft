# 6.09 BASE (2.34s) Synchronization at forty-one point three percent.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 51
scoreboard players set #line angel.story 609
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_09 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Synchronization at forty-one point three percent.", "color": "gray"}
