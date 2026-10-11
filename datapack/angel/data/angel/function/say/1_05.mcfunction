# 1.05 MISATO (2.78s) Sorry. I meant to be here before that was.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 60
scoreboard players set #line angel.story 105
scoreboard players set #lastspoke angel.story 1
scoreboard players set #speaker angel.story 1
scoreboard players set #played angel.story 0
execute if score #present_misato angel.story matches 1 as @e[tag=angel.misato,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.misato.1_05 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.misato.1_05 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Misato> Sorry. I meant to be here before that was.", "color": "gold"}
