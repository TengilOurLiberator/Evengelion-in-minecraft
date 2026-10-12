# 5.43 RITSUKO (5.84s) Good. Come with me. I'll tell you only what you need; there is no time for the rest.
scoreboard players set #line angel.story 543
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 181
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 2
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 2
execute if score #live angel.story matches 0 run function angel:say/file/5_43
