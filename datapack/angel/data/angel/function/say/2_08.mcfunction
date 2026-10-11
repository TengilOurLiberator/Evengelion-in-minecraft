# 2.08 MISATO (5.98s) Me too. Mouthful of sand, that's all. Come on. Back against the roof, and push when I say.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 124
scoreboard players set #line angel.story 208
scoreboard players set #lastspoke angel.story 1
scoreboard players set #speaker angel.story 1
scoreboard players set #played angel.story 0
execute if score #present_misato angel.story matches 1 as @e[tag=angel.misato,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.misato.2_08 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.misato.2_08 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Misato> Me too. Mouthful of sand, that's all. Come on. Back against the roof, and push when I say.", "color": "gold"}
