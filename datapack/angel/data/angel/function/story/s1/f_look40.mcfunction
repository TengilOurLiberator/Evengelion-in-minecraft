scoreboard players set #looking angel.story 0
execute unless entity @e[tag=angel.gaze,limit=1] at @a[limit=1] run summon minecraft:marker ~ ~ ~ {Tags:["angel.gaze","angel.story"]}
execute as @a[limit=1] at @s anchored eyes positioned ^ ^ ^1 run tp @e[tag=angel.gaze,limit=1] ~ ~ ~
execute as @a[limit=1] at @s anchored eyes facing entity @e[tag=angel.look_target,limit=1] eyes positioned ^ ^ ^1 if entity @e[tag=angel.gaze,distance=..0.68] run scoreboard players set #looking angel.story 1
