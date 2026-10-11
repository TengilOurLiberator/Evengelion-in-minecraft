scoreboard players set #force angel.story 0
scoreboard players set #beat angel.story 41
scoreboard players set #present_misato angel.story 1
scoreboard players set #present_ritsuko angel.story 1
scoreboard players set #present_gendo angel.story 0
scoreboard players set #present_rei angel.story 0
execute positioned 3096.5 54.0 143.2 rotated 180.0 0 run function angel:cast/summon {id:"ritsuko"}
execute positioned 3095.4 54.0 146.8 rotated 180.0 0 run function angel:cast/summon {id:"misato"}
scoreboard players set #step angel.story 7
function angel:story/s5/e7
