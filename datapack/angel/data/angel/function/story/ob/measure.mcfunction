scoreboard players set #ob.b angel.story 99
execute if entity @e[tag=angel.ob_target,limit=1] as @a[limit=1] at @s run function angel:story/ob/band
execute store result score #ob.px angel.story as @a[limit=1] run data get entity @s Pos[0] 4
execute store result score #ob.pz angel.story as @a[limit=1] run data get entity @s Pos[2] 4
scoreboard players operation #ob.dx angel.story = #ob.px angel.story
scoreboard players operation #ob.dx angel.story -= #ob.px0 angel.story
scoreboard players operation #ob.dz angel.story = #ob.pz angel.story
scoreboard players operation #ob.dz angel.story -= #ob.pz0 angel.story
scoreboard players set #ob.mv angel.story 0
execute unless score #ob.dx angel.story matches -3..3 run scoreboard players set #ob.mv angel.story 1
execute unless score #ob.dz angel.story matches -3..3 run scoreboard players set #ob.mv angel.story 1
execute if score #ob.mv angel.story matches 1 run scoreboard players set #ob.sn angel.story 0
execute if score #ob.mv angel.story matches 1 run scoreboard players operation #ob.px0 angel.story = #ob.px angel.story
execute if score #ob.mv angel.story matches 1 run scoreboard players operation #ob.pz0 angel.story = #ob.pz angel.story
execute if score #ob.mv angel.story matches 0 run scoreboard players add #ob.sn angel.story 5
