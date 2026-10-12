# 5.26 GENDO (4.50s) She is not dead. She will serve.
scoreboard players set #line angel.story 526
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 154
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 3
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 3
execute if score #live angel.story matches 0 run function angel:say/file/5_26
