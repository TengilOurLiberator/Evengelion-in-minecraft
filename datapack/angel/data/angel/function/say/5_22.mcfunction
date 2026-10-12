# 5.22 GENDO (2.66s) It has found us.
scoreboard players set #line angel.story 522
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 117
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 3
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 3
execute if score #live angel.story matches 0 run function angel:say/file/5_22
