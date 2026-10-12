# 7.17 RITSUKO (1.53s) One in a billion.
scoreboard players set #line angel.story 717
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 95
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 2
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 2
execute if score #live angel.story matches 0 run function angel:say/file/7_17
