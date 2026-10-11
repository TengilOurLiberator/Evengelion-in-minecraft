# moves every part and both hit boxes to the root
execute as @e[type=minecraft:block_display,tag=angel.part] run tp @s @e[type=minecraft:marker,tag=angel.root,limit=1]
function angel:angel/sync_hit with storage angel:mon off
