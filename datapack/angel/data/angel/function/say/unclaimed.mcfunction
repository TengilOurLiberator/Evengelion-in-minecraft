scoreboard players add #cue_wait angel.story 1
execute if score #live angel.story matches 1 unless score #bridge_hb angel.story matches 1.. run function angel:say/fallback
execute if score #live angel.story matches 1 if score #cue_wait angel.story matches 14.. run function angel:say/fallback
