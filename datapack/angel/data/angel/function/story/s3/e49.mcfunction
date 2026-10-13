scoreboard players set #force angel.story 0
effect give @a minecraft:blindness 4 0 true
execute at @a[limit=1] run playsound angel:sfx.train_start master @a ~ ~ ~ 1.0 1.0 1.0
scoreboard players set #step angel.story 50
function angel:story/s3/e50
