# 6.17 GENDO (6.75s) You have it. If the Angel is not stopped, there is nothing after today.
scoreboard players set #line angel.story 617
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 199
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 3
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 3
execute if score #live angel.story matches 0 run function angel:say/file/6_17
