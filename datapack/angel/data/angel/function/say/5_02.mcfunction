# 5.02 RITSUKO (8.02s) This is what people built when they ran out of other answers. Not a robot. A made human being, the height of a tower.
scoreboard players set #talking angel.story 1
scoreboard players set #line_left angel.story 164
scoreboard players set #line angel.story 502
scoreboard players set #lastspoke angel.story 2
scoreboard players set #speaker angel.story 2
scoreboard players set #played angel.story 0
execute if score #present_ritsuko angel.story matches 1 as @e[tag=angel.ritsuko,tag=angel.char,limit=1] at @s store success score #played angel.story run playsound angel:line.ritsuko.5_02 voice @a ~ ~1.6 ~ 2.5 1 0.7
execute if score #played angel.story matches 0 at @a[limit=1] run playsound angel:line.ritsuko.5_02 voice @a ~ ~ ~ 1 1 1
execute if score #subtitles angel.story matches 1 run tellraw @a {"text": "<Ritsuko> This is what people built when they ran out of other answers. Not a robot. A made human being, the height of a tower.", "color": "aqua"}
