kill @e[tag=angel.ia_car,limit=1]
ride @a[limit=1] mount @e[tag=angel.seat_passenger,limit=1]
scoreboard players set #ride angel.story 1
function angel:story/ob/end
scoreboard players set #step angel.story 84
function angel:story/s1/e84
