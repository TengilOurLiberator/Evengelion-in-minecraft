# keeps the monster 8 blocks from the giant, on the side it came from
execute at @e[tag=angel.giant,limit=1] facing entity @e[type=minecraft:marker,tag=angel.root,limit=1] feet run tp @e[type=minecraft:marker,tag=angel.root,limit=1] ^ ^ ^8
tp @e[type=minecraft:marker,tag=angel.target,limit=1] @e[tag=angel.giant,limit=1]
rotate @e[type=minecraft:marker,tag=angel.root,limit=1] facing entity @e[tag=angel.giant,limit=1] feet
function angel:angel/sync
