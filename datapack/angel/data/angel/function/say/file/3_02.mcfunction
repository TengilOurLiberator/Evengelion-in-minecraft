# 3.02 MISATO (4.51s) Did your father send you a pass? A card, with your face on it?
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 94
scoreboard players set #line angel.story 302
scoreboard players set #live angel.story 0
scoreboard players set #lastspoke angel.story 1
scoreboard players set #speaker angel.story 1
scoreboard players set #played angel.story 0
execute if score #present_misato angel.story matches 1 as @e[tag=angel.misato,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.misato.3_02 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.misato.3_02 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Misato> Did your father send you a pass? A card, with your face on it?", "color": "gold"}
