# 2.01 MISATO (8.38s) Misato Katsuragi. Captain, on paper, but if you call me that I'll put you out at the next corner. Misato.
scoreboard players set #line angel.story 201
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 232
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 1
execute if score #live angel.story matches 0 run function angel:say/file/2_01
