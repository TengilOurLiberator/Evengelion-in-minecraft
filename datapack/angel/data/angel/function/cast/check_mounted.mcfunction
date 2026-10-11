scoreboard players set #rid angel.cast 0
execute on vehicle run scoreboard players set #rid angel.cast 1
execute if score #rid angel.cast matches 0 run tag @s remove angel.mounted
execute if score #rid angel.cast matches 0 run tag @s remove angel.sitting
