scoreboard players set #ob.dir angel.story -1
execute unless entity @e[tag=angel.ob_target,limit=1] run return 0
kill @e[tag=angel.ob_tmp]
execute as @a[limit=1] at @s run summon minecraft:marker ~ ~ ~ {Tags:["angel.story","angel.objective","angel.ob_tmp"]}
execute as @e[tag=angel.ob_tmp,limit=1] at @s facing entity @e[tag=angel.ob_target,limit=1] feet run rotate @s ~ ~
execute store result score #ob.ty angel.story run data get entity @e[tag=angel.ob_tmp,limit=1] Rotation[0] 10
execute as @a[limit=1] store result score #ob.py angel.story run data get entity @s Rotation[0] 10
scoreboard players operation #ob.ty angel.story -= #ob.py angel.story
scoreboard players operation #ob.ty angel.story %= #c3600 angel.story
execute if score #ob.ty angel.story matches 1801.. run scoreboard players remove #ob.ty angel.story 3600
kill @e[tag=angel.ob_tmp]
execute if score #ob.ty angel.story matches -300..300 run scoreboard players set #ob.dir angel.story 0
execute if score #ob.ty angel.story matches 301..1350 run scoreboard players set #ob.dir angel.story 1
execute if score #ob.ty angel.story matches -1350..-301 run scoreboard players set #ob.dir angel.story 2
execute if score #ob.ty angel.story matches 1351.. run scoreboard players set #ob.dir angel.story 3
execute if score #ob.ty angel.story matches ..-1351 run scoreboard players set #ob.dir angel.story 3
