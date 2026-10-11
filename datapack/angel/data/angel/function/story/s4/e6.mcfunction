scoreboard players set #force angel.story 0
scoreboard players set #beat angel.story 40
scoreboard players set #present_misato angel.story 1
scoreboard players set #present_ritsuko angel.story 0
scoreboard players set #present_gendo angel.story 0
scoreboard players set #present_rei angel.story 0
execute positioned 3178.5 131.0 160.5 rotated 90.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/look {id:"misato",mode:"ahead"}
execute positioned 3005.5 107.0 160.5 rotated -90.0 0 run function angel:cast/summon {id:"ritsuko"}
function angel:cast/look {id:"ritsuko",mode:"ahead"}
scoreboard players set #step angel.story 7
function angel:story/s4/e7
