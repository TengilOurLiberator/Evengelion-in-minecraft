execute if score #ride angel.story matches 1 run function angel:story/prompt/place
scoreboard players operation #t5 angel.story = #tick angel.story
scoreboard players operation #t5 angel.story %= #c5 angel.story
execute if score #ride angel.story matches 0 if score #t5 angel.story matches 0 run function angel:story/prompt/place
scoreboard players operation #t20 angel.story = #tick angel.story
scoreboard players operation #t20 angel.story %= #c20 angel.story
execute if score #t20 angel.story matches 0 if score #placed angel.story matches 0 run function angel:story/prompt/bar
