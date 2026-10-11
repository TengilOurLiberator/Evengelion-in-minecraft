# 3.01 BASE (5.74s) Gate closing. Car train departing for headquarters. Please remain in your vehicle.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 119
scoreboard players set #line angel.story 301
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.3_01 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Gate closing. Car train departing for headquarters. Please remain in your vehicle.", "color": "gray"}
