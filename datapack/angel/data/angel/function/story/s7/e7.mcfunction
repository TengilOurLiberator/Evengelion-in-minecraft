scoreboard players set #force angel.story 0
function angel:world/sky_city
execute as @a[limit=1] run function angel:fight/become_giant
scoreboard players set #present_misato angel.story 2
scoreboard players set #present_ritsuko angel.story 2
scoreboard players set #present_gendo angel.story 2
scoreboard players set #present_rei angel.story 0
scoreboard players set #beat angel.story 70
gamemode adventure @a
scoreboard players set #step angel.story 8
function angel:story/s7/e8
