scoreboard players add #fx.t angel.story 1
execute if score #fx.t angel.story matches ..361 as @e[tag=angel.cmark,limit=1] at @s run tp @s ~-0.15 ~ ~ ~1.1 ~
execute if score #fx.t angel.story matches 362.. as @e[tag=angel.cmark,limit=1] at @s run tp @s ~ ~ ~ ~1.1 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~0.0 ~ positioned ^ ^-34.0 ^50.0 run tp @e[tag=angel.rig_ac1,tag=angel.rpart] ~ ~ ~ ~90 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~72.0 ~ positioned ^ ^-12.0 ^58.0 run tp @e[tag=angel.rig_ac2,tag=angel.rpart] ~ ~ ~ ~90 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~144.0 ~ positioned ^ ^6.0 ^54.0 run tp @e[tag=angel.rig_ac3,tag=angel.rpart] ~ ~ ~ ~90 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~216.0 ~ positioned ^ ^22.0 ^62.0 run tp @e[tag=angel.rig_ac4,tag=angel.rpart] ~ ~ ~ ~90 ~
execute as @e[tag=angel.cmark,limit=1] at @s rotated ~288.0 ~ positioned ^ ^-22.0 ^48.0 run tp @e[tag=angel.rig_ac5,tag=angel.rpart] ~ ~ ~ ~90 ~
scoreboard players operation #fx.m angel.story = #fx.t angel.story
scoreboard players operation #fx.m angel.story %= #c36 angel.story
execute if score #fx.m angel.story matches 4 if entity @e[tag=angel.rig_ac1,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire1
execute if score #fx.m angel.story matches 11 if entity @e[tag=angel.rig_ac2,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire2
execute if score #fx.m angel.story matches 18 if entity @e[tag=angel.rig_ac3,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire3
execute if score #fx.m angel.story matches 25 if entity @e[tag=angel.rig_ac4,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire4
execute if score #fx.m angel.story matches 32 if entity @e[tag=angel.rig_ac5,tag=angel.pt_fuselage,limit=1] run function angel:story/fx/fire5
function angel:story/fx/tr_tick
function angel:story/fx/flash_tick
execute if score #fx.t angel.story matches 142 run function angel:story/fx/ac3_hit
execute if score #fx.t angel.story matches 161 run function angel:story/fx/ac3_fall
