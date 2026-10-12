# 4.18 RITSUKO (6.55s) It's a number I say when I mean "we have nothing else." Mind your step. It's dark through here.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 135
scoreboard players set #line angel.story 418
scoreboard players set #live angel.story 0
scoreboard players set #lastspoke angel.story 2
scoreboard players set #speaker angel.story 2
scoreboard players set #played angel.story 0
execute if score #present_ritsuko angel.story matches 1 as @e[tag=angel.ritsuko,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.ritsuko.4_18 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.ritsuko.4_18 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Ritsuko> It's a number I say when I mean \"we have nothing else.\" Mind your step. It's dark through here.", "color": "aqua"}
