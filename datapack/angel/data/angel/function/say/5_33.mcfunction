# 5.33 RITSUKO (3.63s) It moved? It can't have. The plug isn't even in!
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 77
scoreboard players set #line angel.story 533
scoreboard players set #lastspoke angel.story 2
scoreboard players set #speaker angel.story 2
scoreboard players set #played angel.story 0
execute if score #present_ritsuko angel.story matches 1 as @e[tag=angel.ritsuko,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.ritsuko.5_33 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.ritsuko.5_33 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Ritsuko> It moved? It can't have. The plug isn't even in!", "color": "aqua"}
