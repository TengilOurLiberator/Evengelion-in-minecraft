# a swing that hit the larger 'near miss' box round the core is a swing at the core (the core box lies inside it, so this box is hit first)
data remove entity @s attack
execute as @e[type=minecraft:interaction,tag=angel.core,limit=1] at @s run function angel:fight/core_hit
