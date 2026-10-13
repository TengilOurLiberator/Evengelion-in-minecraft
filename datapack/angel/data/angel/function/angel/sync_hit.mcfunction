# keeps the two hit boxes at their offsets from the root (macro args: cx cy cz bx by bz, left/up/forward)
$execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run tp @e[type=minecraft:interaction,tag=angel.core,limit=1] ^$(cx) ^$(cy) ^$(cz)
$execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run tp @e[type=minecraft:interaction,tag=angel.body,limit=1] ^$(bx) ^$(by) ^$(bz)
$execute at @e[type=minecraft:marker,tag=angel.root,limit=1] run tp @e[type=minecraft:interaction,tag=angel.nearbox,limit=1] ^$(nx) ^$(ny) ^$(nz)
