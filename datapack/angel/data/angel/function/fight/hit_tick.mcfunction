execute as @e[type=minecraft:interaction,tag=angel.core] if data entity @s attack at @s run function angel:fight/core_hit
execute as @e[type=minecraft:interaction,tag=angel.body] if data entity @s attack at @s run function angel:fight/body_hit
execute as @e[type=minecraft:interaction,tag=angel.nearbox] if data entity @s attack run function angel:fight/near_hit
