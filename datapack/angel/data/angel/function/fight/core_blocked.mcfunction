# beyond arm's length: the hit stops on the wall of light
execute if score #blocked1 angel.fight matches 0 run function angel:fight/first_blocked
scoreboard players set #wallt angel.fight 30
execute positioned ~ 2.25 ~ facing entity @e[tag=angel.giant,limit=1] eyes positioned ^ ^ ^6 run function angel:fight/wall_flash
