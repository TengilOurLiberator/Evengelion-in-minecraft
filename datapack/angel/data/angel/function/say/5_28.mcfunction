# 5.28 REI (1.06s) Yes.
scoreboard players set #line angel.story 528
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 85
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 4
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 4
execute if score #live angel.story matches 0 run function angel:say/file/5_28
