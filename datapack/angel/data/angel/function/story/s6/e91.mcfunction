scoreboard players set #force angel.story 0
execute as @e[tag=angel.lstat] run data merge entity @s {text:[{"text": "SAFETIES OFF", "color": "green", "bold": true}, {"text": "\n"}, {"text": "BATTERIES FULL", "color": "gray"}]}
scoreboard players set #step angel.story 92
function angel:story/s6/e92
