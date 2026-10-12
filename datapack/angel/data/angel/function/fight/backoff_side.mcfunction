# no room to retreat: to the other side of the avenue (the monster is on the east half -> west, and the reverse)
execute if score #rx angel.fight matches 11600.. run scoreboard players set #tx angel.fight 11530
execute unless score #rx angel.fight matches 11600.. run scoreboard players set #tx angel.fight 11670
