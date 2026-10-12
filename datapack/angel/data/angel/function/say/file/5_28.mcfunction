# 5.28 REI (1.06s) Yes.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 25
scoreboard players set #line angel.story 528
scoreboard players set #live angel.story 0
scoreboard players set #lastspoke angel.story 4
scoreboard players set #speaker angel.story 4
scoreboard players set #played angel.story 0
execute if score #present_rei angel.story matches 1 as @e[tag=angel.rei,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.rei.5_28 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.rei.5_28 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Rei> Yes.", "color": "light_purple"}
