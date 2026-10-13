# simulates a click on the larger 'near miss' box round the core
data modify entity @e[type=minecraft:interaction,tag=angel.nearbox,limit=1] attack set value {player:[I;1,2,3,4],timestamp:1L}
