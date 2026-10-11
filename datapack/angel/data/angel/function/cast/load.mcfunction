scoreboard objectives add angel.cast dummy
team add angel.cast
team modify angel.cast collisionRule never
team modify angel.cast nametagVisibility never
team modify angel.cast friendlyFire false
scoreboard players set #k36000 angel.cast 36000
scoreboard players set #k1000 angel.cast 1000
scoreboard players set #k2 angel.cast 2
scoreboard players set #km1 angel.cast -1
execute unless score #active angel.cast matches 0.. run scoreboard players set #active angel.cast 0
execute unless score #gmove angel.cast matches 0.. run scoreboard players set #gmove angel.cast 0
