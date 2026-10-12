# 7.05 RITSUKO (8.16s) The pain comes back through the link. It is real to you and nothing of yours is broken. Keep moving.
scoreboard players set #line angel.story 705
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 227
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 2
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 2
execute if score #live angel.story matches 0 run function angel:say/file/7_05
