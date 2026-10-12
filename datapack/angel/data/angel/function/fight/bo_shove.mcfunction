# thrown back toward the retreat point (along the avenue, away from the giant), a little each tick, so that it has separated from the giant
# before the arms are flung out and it turns its back (the parts teleport with teleport_duration 2: the slide is smooth)
execute as @e[type=minecraft:marker,tag=angel.root,limit=1] at @s facing entity @e[type=minecraft:marker,tag=angel.target,limit=1] feet run tp @s ^ ^ ^0.8
function angel:angel/sync
