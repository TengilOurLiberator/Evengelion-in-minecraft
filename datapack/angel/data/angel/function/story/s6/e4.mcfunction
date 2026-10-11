scoreboard players set #force angel.story 0
time of angel:day set 18000
time of angel:day pause
execute in minecraft:overworld run weather clear
scoreboard players set #ride angel.story 0
ride @a[limit=1] dismount
kill @e[tag=angel.lseat]
summon minecraft:item_display 3030.5 12.6 11.5 {Tags:["angel.seat","angel.seat_passenger","angel.story","angel.launch","angel.lseat"],teleport_duration:0,item_display:"none"}
tp @a[limit=1] 3030.5 12.0 11.5
ride @a[limit=1] mount @e[tag=angel.lseat,limit=1]
scoreboard players set #ride angel.story 1
gamemode adventure @a
scoreboard players set #present_misato angel.story 0
scoreboard players set #present_ritsuko angel.story 0
scoreboard players set #present_gendo angel.story 0
scoreboard players set #present_rei angel.story 0
scoreboard players set #beat angel.story 54
scoreboard players set #step angel.story 5
function angel:story/s6/e5
