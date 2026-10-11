scoreboard players add #fx.t angel.story 1
execute if score #fx.t angel.story matches ..361 as @e[tag=angel.cmark,limit=1] at @s run tp @s ~-0.15 ~ ~ ~0.9 ~
execute if score #fx.t angel.story matches 362.. as @e[tag=angel.cmark,limit=1] at @s run tp @s ~ ~ ~ ~0.9 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~0.0 ~ positioned ^ ^6.0 ^52.0 run tp @e[tag=angel.rig_ac1,tag=angel.part] ~ ~ ~ ~90 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~90.0 ~ positioned ^ ^15.0 ^58.0 run tp @e[tag=angel.rig_ac2,tag=angel.part] ~ ~ ~ ~90 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~180.0 ~ positioned ^ ^-3.0 ^50.0 run tp @e[tag=angel.rig_ac3,tag=angel.part] ~ ~ ~ ~90 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~270.0 ~ positioned ^ ^10.0 ^56.0 run tp @e[tag=angel.rig_ac4,tag=angel.part] ~ ~ ~ ~90 ~
scoreboard players operation #fx.m angel.story = #fx.t angel.story
scoreboard players operation #fx.m angel.story %= #c36 angel.story
execute if score #fx.m angel.story matches 6 if entity @e[tag=angel.rig_ac1,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire1
execute if score #fx.m angel.story matches 15 if entity @e[tag=angel.rig_ac2,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire2
execute if score #fx.m angel.story matches 24 if entity @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire3
execute if score #fx.m angel.story matches 33 if entity @e[tag=angel.rig_ac4,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire4
execute if score #fx.t angel.story matches 190 run function angel:story/fx/ac3_hit
execute if score #fx.t angel.story matches 215 run function angel:story/fx/ac3_fall
