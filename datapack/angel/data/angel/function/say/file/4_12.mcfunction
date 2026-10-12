# 4.12 BASE (7.28s) All personnel, first stage alert. Prepare for ground interception. Repeat: prepare for ground interception.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 150
scoreboard players set #line angel.story 412
scoreboard players set #live angel.story 0
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.4_12 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> All personnel, first stage alert. Prepare for ground interception. Repeat: prepare for ground interception.", "color": "gray"}
