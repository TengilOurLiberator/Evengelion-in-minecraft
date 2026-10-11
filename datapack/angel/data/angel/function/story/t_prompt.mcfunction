scoreboard players set #pw angel.story 0
execute if score #wait angel.story matches 1.. if score #talking angel.story matches 0 unless score #bridge_speaking angel.story matches 1.. run scoreboard players set #pw angel.story 1
execute if score #pw angel.story matches 1 unless entity @e[tag=angel.prompt,limit=1] run function angel:story/prompt/show
execute if score #pw angel.story matches 1 if entity @e[tag=angel.prompt,limit=1] run function angel:story/prompt/keep
execute if score #pw angel.story matches 0 if entity @e[tag=angel.prompt,limit=1] run function angel:story/prompt/hide
