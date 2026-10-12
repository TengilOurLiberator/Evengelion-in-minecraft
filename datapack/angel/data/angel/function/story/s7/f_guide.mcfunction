execute if score #phase angel.fight matches 3.. unless score #fg angel.story matches 9 run function angel:story/s7/f_g_wrap
execute if score #phase angel.fight matches 3.. run return 0
execute if score #fg angel.story matches 9 run function angel:story/s7/f_g_rearm
execute if score #ch angel.fight matches ..57 unless score #fg angel.story matches 4 unless score #fg.c angel.story matches 1.. run function angel:story/s7/f_g_end
execute if score #ch angel.fight matches 58..59 if score #fg angel.story matches 0..2 run function angel:story/s7/f_g_keep
execute if score #fg.c angel.story matches 1.. run scoreboard players remove #fg.c angel.story 1
execute if score #fg.c angel.story matches 0 run function angel:story/s7/f_g_restore
execute if score #fg.c angel.story matches 1.. run return 0
execute if score #fg angel.story matches 0 if score #ch angel.fight matches 60.. run function angel:story/s7/f_g_walk
execute if score #fg angel.story matches 1 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~-19.75 ~ if entity @a[limit=1,distance=..24] run function angel:story/s7/f_g_hit
execute if score #fg angel.story matches 2 as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s positioned ~ ~-19.75 ~ if entity @a[limit=1,distance=..12.5] run scoreboard players add #fg.hit angel.story 1
execute if score #fg.hit angel.story matches 400.. run function angel:story/s7/f_g_again
execute if score #st angel.fight matches 1 if score #fg.beam angel.story matches 0 run function angel:story/s7/f_g_cover
execute unless score #hold angel.fight matches 1 run scoreboard players set #fg.dflag angel.story 0
execute if score #hold angel.fight matches 1 if score #fg.dflag angel.story matches 0 if score #fg.bo angel.story matches ..2 if score #fg angel.story matches 3..4 run function angel:story/s7/f_g_close
