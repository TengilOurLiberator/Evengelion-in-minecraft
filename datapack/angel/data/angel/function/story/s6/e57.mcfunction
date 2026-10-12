scoreboard players set #force angel.story 0
execute as @e[tag=angel.lstat] run data merge entity @s {text:[{"text": "NERVE LINKS", "color": "gold", "bold": true}, {"text": "\n"}, {"text": "OPEN", "color": "gray"}]}
scoreboard players set #step angel.story 58
function angel:story/s6/e58
