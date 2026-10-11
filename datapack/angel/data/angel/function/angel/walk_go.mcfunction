# starts (or re-tunes) walking toward the angel.target marker; speed/stop come from storage angel:mon walk
execute unless entity @e[type=minecraft:marker,tag=angel.root] run return 0
execute store result score #spd angel.mon run data get storage angel:mon walk.speed 1000
execute if score #spd angel.mon matches ..20 run scoreboard players set #spd angel.mon 20
# blocks the body travels per step / speed per tick = ticks per step
scoreboard players operation #T angel.mon = #S angel.mon
scoreboard players operation #T angel.mon /= #spd angel.mon
execute if score #T angel.mon matches ..13 run scoreboard players set #T angel.mon 14
execute if score #T angel.mon matches 161.. run scoreboard players set #T angel.mon 160
# movement per update (2 ticks) and the arrival distance as macro args
scoreboard players operation #stp angel.mon = #spd angel.mon
scoreboard players operation #stp angel.mon *= #2 angel.mon
execute store result storage angel:mon walk.step double 0.001 run scoreboard players get #stp angel.mon
scoreboard players add #stp angel.mon 100
execute store result storage angel:mon walk.arr double 0.001 run scoreboard players get #stp angel.mon
execute if data storage angel:mon {walk:{stop:0.0d}} run data modify storage angel:mon walk.stopd set from storage angel:mon walk.arr
execute unless data storage angel:mon {walk:{stop:0.0d}} run data modify storage angel:mon walk.stopd set from storage angel:mon walk.stop
scoreboard players set #arrived angel.walk 0
execute if score #walking angel.mon matches 1 run return 0
scoreboard players set #walking angel.mon 1
scoreboard players set #step angel.mon 0
scoreboard players set #foot angel.mon 1
scoreboard players set #landed angel.mon 0
schedule function angel:angel/walk_tick 1t
