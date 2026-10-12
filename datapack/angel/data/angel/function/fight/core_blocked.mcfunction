# beyond arm's length (or the barrier is raised): the hit stops on the wall of light.  Rate-limited so that flailing is not a wall of noise
execute if score #blockcd angel.fight matches 1.. run return 0
scoreboard players set #blockcd angel.fight 6
execute if score #blocked1 angel.fight matches 0 run function angel:fight/first_blocked
scoreboard players set #wallt angel.fight 30
execute positioned ~ 2.25 ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_flash
