# snap the requested height to the nearest generated one (geometric midpoints)
execute store result score #hin angel.mon run data get storage angel:mon in.height 1
execute if score #hin angel.mon matches 0..24 run scoreboard players set #h angel.mon 20
execute if score #hin angel.mon matches 25..34 run scoreboard players set #h angel.mon 30
execute if score #hin angel.mon matches 35..44 run scoreboard players set #h angel.mon 40
execute if score #hin angel.mon matches 45..54 run scoreboard players set #h angel.mon 50
execute if score #hin angel.mon matches 55..69 run scoreboard players set #h angel.mon 60
execute if score #hin angel.mon matches 70..89 run scoreboard players set #h angel.mon 80
execute if score #hin angel.mon matches 90..122 run scoreboard players set #h angel.mon 100
execute if score #hin angel.mon matches 123..1000000 run scoreboard players set #h angel.mon 150
