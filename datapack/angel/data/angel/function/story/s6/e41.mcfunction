scoreboard players set #force angel.story 0
execute at @a[limit=1] run playsound angel:sfx.contact master @a ~ ~ ~ 1.0 1.0 1.0
execute as @e[tag=angel.lstat] run data merge entity @s {text:[{"text": "POWER", "color": "green", "bold": true}, {"text": "\n"}, {"text": "CONNECTED", "color": "gray"}]}
scoreboard players set #step angel.story 42
function angel:story/s6/e42
