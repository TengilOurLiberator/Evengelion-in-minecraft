scoreboard players set #force angel.story 0
execute as @e[tag=angel.lstat] run data merge entity @s {text:[{"text": "LOCK BOLTS", "color": "green", "bold": true}, {"text": "\n"}, {"text": "RELEASED", "color": "gray"}]}
scoreboard players set #step angel.story 89
function angel:story/s6/e89
