scoreboard players set #st angel.fight 0
scoreboard players set #t angel.fight 0
scoreboard players set #nav angel.fight 99
scoreboard players set #dur angel.mon 20
function angel:angel/pose_idle
execute if score #cd angel.fight matches 41.. run scoreboard players set #cd angel.fight 40
execute unless score #cd angel.fight matches 31.. run scoreboard players set #cd angel.fight 30
