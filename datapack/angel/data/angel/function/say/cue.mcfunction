scoreboard players set #live angel.story 1
scoreboard players set #cue_fb angel.story 0
scoreboard players set #cue_wait angel.story 0
scoreboard players set #cue_ack angel.story -1
scoreboard players add #cue_n angel.story 1
execute if score #cue_n angel.story matches 1000000.. run scoreboard players set #cue_n angel.story 1
scoreboard players operation #cue angel.story = #cue_n angel.story
scoreboard players operation #cue angel.story *= #c1000 angel.story
scoreboard players operation #cue angel.story += #line angel.story
scoreboard players operation #cue_t angel.story = #tick angel.story
