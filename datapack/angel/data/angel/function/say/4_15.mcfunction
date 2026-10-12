# 4.15 MISATO (3.66s) Does it actually run? It has never once started.
scoreboard players set #line angel.story 415
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 137
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 1
execute if score #live angel.story matches 0 run function angel:say/file/4_15
