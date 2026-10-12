# 2.12 MISATO (7.39s) Ritsuko, it's me. I have him. Yes, in one piece, what do you take me for? Have a car train waiting. The fast one.
scoreboard players set #line angel.story 212
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 212
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 1
execute if score #live angel.story matches 0 run function angel:say/file/2_12
