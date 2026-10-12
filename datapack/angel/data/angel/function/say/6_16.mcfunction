# 6.16 MISATO (3.79s) Understood. Commander. Do I have your word?
scoreboard players set #line angel.story 616
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 140
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 1
execute if score #live angel.story matches 0 run function angel:say/file/6_16
