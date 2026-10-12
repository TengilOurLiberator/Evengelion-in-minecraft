kill @e[tag=angel.rigpos]
summon minecraft:marker 3096.5 76.0 78.0 {Tags:["angel.story","angel.rigpos"]}
scoreboard players set #rg.near angel.story 0
execute positioned 3096.5 54.0 78.5 if entity @a[limit=1,distance=..11] run scoreboard players set #rg.near angel.story 1
execute if score #rg.near angel.story matches 1 as @a[limit=1] at @s rotated ~ 0 positioned ^ ^ ^2.5 run tp @e[tag=angel.rigpos,limit=1] ~ 76.0 ~
execute store result score #rg.x angel.story run data get entity @e[tag=angel.rigpos,limit=1] Pos[0] 100
execute store result score #rg.z angel.story run data get entity @e[tag=angel.rigpos,limit=1] Pos[2] 100
execute store result score #rg.pz angel.story run data get entity @a[limit=1] Pos[2] 100
scoreboard players set #rg.xl angel.story 309360
scoreboard players set #rg.xh angel.story 309940
scoreboard players set #rg.zl angel.story 7500
scoreboard players set #rg.zh angel.story 7960
scoreboard players operation #rg.x angel.story > #rg.xl angel.story
scoreboard players operation #rg.x angel.story < #rg.xh angel.story
scoreboard players operation #rg.z angel.story > #rg.zl angel.story
scoreboard players operation #rg.z angel.story < #rg.zh angel.story
execute store result entity @e[tag=angel.rigpos,limit=1] Pos[0] double 0.01 run scoreboard players get #rg.x angel.story
execute store result entity @e[tag=angel.rigpos,limit=1] Pos[2] double 0.01 run scoreboard players get #rg.z angel.story
scoreboard players set #rg.sgn angel.story 1
execute if score #rg.pz angel.story > #rg.z angel.story run scoreboard players set #rg.sgn angel.story -1
