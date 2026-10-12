# 5.27 GENDO (6.86s) Rei. The replacement has refused. It falls to you again.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 141
scoreboard players set #line angel.story 527
scoreboard players set #live angel.story 0
scoreboard players set #lastspoke angel.story 3
scoreboard players set #speaker angel.story 3
scoreboard players set #played angel.story 0
execute if score #present_gendo angel.story matches 1 as @e[tag=angel.gendo,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.gendo.5_27 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.gendo.5_27 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Gendo> Rei. The replacement has refused. It falls to you again.", "color": "red"}
