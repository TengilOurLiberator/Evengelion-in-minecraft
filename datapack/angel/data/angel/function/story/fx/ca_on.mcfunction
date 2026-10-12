execute as @e[tag=angel.calamp] run data merge entity @s {block_state:"minecraft:orange_concrete",brightness:{sky:15,block:15}}
scoreboard players add #f.cn angel.story 1
execute if score #f.cn angel.story matches ..32 run schedule function angel:story/fx/ca_off 5t
execute if score #f.cn angel.story matches 33.. run kill @e[tag=angel.calamp]
