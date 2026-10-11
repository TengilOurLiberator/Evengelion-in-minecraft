$execute at @e[type=minecraft:marker,tag=angel.target,limit=1] if entity @e[type=minecraft:marker,tag=angel.root,distance=..$(stopd)] run function angel:angel/walk_arrive
