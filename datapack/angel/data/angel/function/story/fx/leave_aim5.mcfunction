summon minecraft:marker ~ ~ ~ {Tags:["angel.story","angel.lvtmp"]}
execute facing -66.379 384.0 995.666 run tp @e[tag=angel.lvtmp,limit=1] ~ ~ ~ ~ ~
execute store result score #fx.tg angel.story run data get entity @e[tag=angel.lvtmp,limit=1] Rotation[0] 100
execute store result score #fx.cur angel.story run data get entity @s Rotation[0] 100
scoreboard players operation #fx.tg angel.story -= #fx.cur angel.story
scoreboard players operation #fx.tg angel.story %= #k36000 angel.story
execute if score #fx.tg angel.story matches 18001.. run scoreboard players remove #fx.tg angel.story 36000
scoreboard players operation #fx.d5 angel.story = #fx.tg angel.story
kill @e[tag=angel.lvtmp]
