# turns the root toward the angel.target marker, at most 8 degrees per call (calls come every 2 ticks)
tp @e[type=minecraft:marker,tag=angel.aim,limit=1] @e[type=minecraft:marker,tag=angel.root,limit=1]
rotate @e[type=minecraft:marker,tag=angel.aim,limit=1] facing entity @e[type=minecraft:marker,tag=angel.target,limit=1] feet
execute store result score #ya angel.mon run data get entity @e[type=minecraft:marker,tag=angel.aim,limit=1] Rotation[0] 10
execute store result score #yr angel.mon run data get entity @e[type=minecraft:marker,tag=angel.root,limit=1] Rotation[0] 10
scoreboard players operation #dy angel.mon = #ya angel.mon
scoreboard players operation #dy angel.mon -= #yr angel.mon
execute if score #dy angel.mon matches 1801.. run scoreboard players remove #dy angel.mon 3600
execute if score #dy angel.mon matches ..-1801 run scoreboard players add #dy angel.mon 3600
execute if score #dy angel.mon matches 80.. as @e[type=minecraft:marker,tag=angel.root,limit=1] run rotate @s ~8 ~
execute if score #dy angel.mon matches ..-80 as @e[type=minecraft:marker,tag=angel.root,limit=1] run rotate @s ~-8 ~
execute if score #dy angel.mon matches -79..79 run tp @e[type=minecraft:marker,tag=angel.root,limit=1] @e[type=minecraft:marker,tag=angel.aim,limit=1]
