# 6.20 BASE (3.66s) Unit Zero-One on the surface. Final restraints released.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 77
scoreboard players set #line angel.story 620
scoreboard players set #played angel.story 0
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.base.6_20 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<NERV> Unit Zero-One on the surface. Final restraints released.", "color": "gray"}
