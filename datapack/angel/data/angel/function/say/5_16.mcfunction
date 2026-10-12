# 5.16 RITSUKO (8.64s) The Angel is what matters today. If someone has any chance of linking with an Eva, we use them. You would give the same order, Captain.
scoreboard players set #line angel.story 516
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 237
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 2
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 2
execute if score #live angel.story matches 0 run function angel:say/file/5_16
