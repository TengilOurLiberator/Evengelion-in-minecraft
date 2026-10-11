# simulates a player's left click on the core box
data modify entity @e[type=minecraft:interaction,tag=angel.core,limit=1] attack set value {player:[I;1,2,3,4],timestamp:1L}
