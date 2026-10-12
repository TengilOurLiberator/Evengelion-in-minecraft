scoreboard players add #wwait angel.fight 1
execute if score #began_7_14 angel.barks matches 1 run scoreboard players set #wgo angel.fight 1
execute if score #wwait angel.fight matches 100.. run scoreboard players set #wgo angel.fight 1
execute if score #wwait angel.fight matches 30 run function angel:fight/wrap_flare
execute if score #wwait angel.fight matches 60 run function angel:fight/wrap_flare
