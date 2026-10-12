scoreboard players set #seated angel.story 0
execute if score #ride angel.story matches 1 as @a[limit=1] on vehicle if entity @s[tag=angel.seat_passenger] run scoreboard players set #seated angel.story 1
execute if score #ride angel.story matches 1 if score #seated angel.story matches 0 if entity @e[tag=angel.seat_passenger,limit=1] as @a[limit=1] run function angel:story/reseat
execute if score #ride angel.story matches 1 as @a[limit=1] on vehicle unless entity @s[tag=angel.rd_seen] run function angel:story/ride_new
execute if score #rd angel.story matches 1.. run title @a actionbar {"text":""}
execute if score #rd angel.story matches 1.. run scoreboard players remove #rd angel.story 1
