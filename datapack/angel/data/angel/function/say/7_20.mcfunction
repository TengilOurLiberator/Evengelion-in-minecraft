# 7.20 MISATO (5.55s) Shinji! Answer me! Pull him back. Pull him back, and send him up again.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 115
scoreboard players set #line angel.story 720
scoreboard players set #lastspoke angel.story 1
scoreboard players set #speaker angel.story 1
scoreboard players set #played angel.story 0
execute if score #present_misato angel.story matches 1 as @e[tag=angel.misato,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.misato.7_20 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.misato.7_20 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Misato> Shinji! Answer me! Pull him back. Pull him back, and send him up again.", "color": "gold"}
