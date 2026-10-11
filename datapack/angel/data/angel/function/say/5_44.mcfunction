# 5.44 REI (0.81s) Why?
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 20
scoreboard players set #line angel.story 544
scoreboard players set #lastspoke angel.story 4
scoreboard players set #speaker angel.story 4
scoreboard players set #played angel.story 0
execute if score #present_rei angel.story matches 1 as @e[tag=angel.rei,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.rei.5_44 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.rei.5_44 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Rei> Why?", "color": "light_purple"}
