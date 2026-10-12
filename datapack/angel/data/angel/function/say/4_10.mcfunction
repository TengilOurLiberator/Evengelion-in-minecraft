# 4.10 RITSUKO (6.57s) Ritsuko Akagi. I run the Evangelion project. I'm glad you came, Shinji.
scoreboard players set #line angel.story 410
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 195
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 2
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 2
execute if score #live angel.story matches 0 run function angel:say/file/4_10
