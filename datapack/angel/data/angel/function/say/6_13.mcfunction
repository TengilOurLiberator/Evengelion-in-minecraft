# 6.13 BASE (4.18s) First lock bolts released. Bridge moving clear. Second lock bolts released.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 88
scoreboard players set #line angel.story 613
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_13 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> First lock bolts released. Bridge moving clear. Second lock bolts released.", "color": "gray"}
