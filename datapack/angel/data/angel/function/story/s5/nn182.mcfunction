scoreboard players operation #nk angel.story = #nagi angel.story
execute if score #nk angel.story matches 0 run scoreboard players set #nagi angel.story 1
execute if score #nk angel.story matches 1 run scoreboard players set #nagi angel.story 2
execute if score #nk angel.story matches 2 run scoreboard players set #nagi angel.story 1
execute if score #nk angel.story matches 0 run function angel:story/s5/nb182_0
execute if score #nk angel.story matches 1 run function angel:story/s5/nb182_1
execute if score #nk angel.story matches 2 run function angel:story/s5/nb182_2
scoreboard players set #nagt angel.story -40
