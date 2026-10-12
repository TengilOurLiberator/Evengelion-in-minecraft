execute as @e[tag=angel.calamp] run data merge entity @s {block_state:"minecraft:gray_concrete",brightness:{sky:0,block:0}}
scoreboard players add #f.cn angel.story 1
execute if score #f.cn angel.story matches ..32 run schedule function angel:story/fx/ca_on 5t
execute if score #f.cn angel.story matches 33.. run kill @e[tag=angel.calamp]
