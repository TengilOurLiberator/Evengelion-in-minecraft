scoreboard players set #placed angel.story 1
execute unless entity @e[tag=angel.prompt,limit=1] run function angel:story/prompt/spawn
execute if entity @e[tag=angel.prompt,limit=1] run tp @e[tag=angel.prompt,limit=1] ~ ~ ~
