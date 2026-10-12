scoreboard players set #st angel.fight 0
scoreboard players set #t angel.fight 0
scoreboard players set #nav angel.fight 99
execute if score #phase angel.fight matches 1 run scoreboard players set #cd angel.fight 150
execute if score #phase angel.fight matches 2.. run scoreboard players set #cd angel.fight 105
execute if score #hold angel.fight matches 1 run function angel:fight/bo_release
