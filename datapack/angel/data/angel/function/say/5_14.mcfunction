# 5.14 RITSUKO (5.79s) Nobody is asking him to fight well. We need someone in that seat whom the unit will accept.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 120
scoreboard players set #line angel.story 514
scoreboard players set #lastspoke angel.story 2
scoreboard players set #speaker angel.story 2
scoreboard players set #played angel.story 0
execute if score #present_ritsuko angel.story matches 1 as @e[tag=angel.ritsuko,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.ritsuko.5_14 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.ritsuko.5_14 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Ritsuko> Nobody is asking him to fight well. We need someone in that seat whom the unit will accept.", "color": "aqua"}
