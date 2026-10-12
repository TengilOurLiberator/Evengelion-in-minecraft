execute if score #bridge_hb angel.story matches 1.. run scoreboard players remove #bridge_hb angel.story 1
execute if score #talking angel.story matches 1 run scoreboard players remove #line_left angel.story 1
execute if score #talking angel.story matches 1 if score #line_left angel.story matches ..0 run scoreboard players set #talking angel.story 0
execute if score #talking angel.story matches 1 if score #live angel.story matches 1 unless score #cue_ack angel.story = #cue_n angel.story run function angel:say/unclaimed
