# 5.20 GENDO (11.36s) Then choose quickly. Sit in it, or go back where you came from. Standing there you are only in the way.
scoreboard players set #line angel.story 520
function angel:say/live_try
execute if score #live angel.story matches 1 run scoreboard players set #talking angel.story 1
execute if score #live angel.story matches 1 run scoreboard players set #line_left angel.story 291
execute if score #live angel.story matches 1 run scoreboard players set #lastspoke angel.story 3
execute if score #live angel.story matches 1 run scoreboard players set #speaker angel.story 3
execute if score #live angel.story matches 0 run function angel:say/file/5_20
