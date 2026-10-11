execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.note_block.bell hostile @a ~ ~ ~ 8 0.7
execute if score #wt angel.fight matches ..100 at @e[type=minecraft:marker,tag=angel.root,limit=1] run playsound minecraft:block.note_block.bell hostile @a ~ ~ ~ 8 1.6
execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run particle minecraft:flash{color:[1.0,0.2,0.1,1.0]} ~ ~12 ~ 0 0 0 0 1 force
