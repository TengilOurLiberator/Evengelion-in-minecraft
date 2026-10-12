# 3.04 MISATO (9.34s) There isn't a test. NERV. A special agency under the United Nations, answering to nobody you'll ever get to vote for. Your father runs it.
scoreboard players set #line angel.story 304
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 251
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 1
execute if score #live angel.story matches 0 run function angel:say/file/3_04
