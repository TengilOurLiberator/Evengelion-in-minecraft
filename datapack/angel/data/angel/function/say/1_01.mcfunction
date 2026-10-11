# 1.01 BASE (7.81s) This is an automated notice. A state of emergency has been declared for the entire Tokai region. All civilian lines are closed until further notice.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 160
scoreboard players set #line angel.story 101
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.1_01 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> This is an automated notice. A state of emergency has been declared for the entire Tokai region. All civilian lines are closed until further notice.", "color": "gray"}
