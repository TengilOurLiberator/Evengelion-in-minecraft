# 5.03 RITSUKO (9.99s) Evangelion. This is the first of the true series, Unit Zero-One. It was built here, in secret, and it is the last card we hold.
scoreboard players set #line angel.story 503
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 264
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 2
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 2
execute if score #live angel.story matches 0 run function angel:say/file/5_03
