# 7.10 BASE (3.58s) Warning. Head armor damaged. Pilot vital signs unstable.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 76
scoreboard players set #line angel.story 710
scoreboard players set #live angel.story 0
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.7_10 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Warning. Head armor damaged. Pilot vital signs unstable.", "color": "gray"}
