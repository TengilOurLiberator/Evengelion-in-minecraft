# 6.08 BASE (4.24s) Nerve links open. Language base set. All primary connections clear.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 89
scoreboard players set #line angel.story 608
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_08 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Nerve links open. Language base set. All primary connections clear.", "color": "gray"}
