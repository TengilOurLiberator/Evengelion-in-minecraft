# 5.18 GENDO (7.55s) You were sent for because I have a use for you. There is no other reason.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 155
scoreboard players set #line angel.story 518
scoreboard players set #live angel.story 0
scoreboard players set #lastspoke angel.story 3
scoreboard players set #speaker angel.story 3
scoreboard players set #played angel.story 0
execute if score #present_gendo angel.story matches 1 as @e[tag=angel.gendo,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.gendo.5_18 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.gendo.5_18 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Gendo> You were sent for because I have a use for you. There is no other reason.", "color": "red"}
