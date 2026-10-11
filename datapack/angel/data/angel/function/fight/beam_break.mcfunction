summon minecraft:marker ~ ~ ~ {Tags:["angel.fight","angel.imp"]}
execute if entity @e[type=minecraft:marker,tag=angel.imp,y=70,dy=300] run fill ~-1 ~-1 ~-1 ~1 ~1 ~1 minecraft:air
kill @e[type=minecraft:marker,tag=angel.imp]
