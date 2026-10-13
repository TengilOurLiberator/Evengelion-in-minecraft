scoreboard players set #force angel.story 0
function angel:cast/remove {id:"ritsuko"}
function angel:cast/remove {id:"misato"}
tp @a[limit=1] 3006.1 54.0 160.5
execute positioned 3004.5 54.0 159.5 rotated -90.0 0 run function angel:cast/summon {id:"ritsuko"}
execute positioned 3004.5 54.0 161.5 rotated -90.0 0 run function angel:cast/summon {id:"misato"}
function angel:cast/look {id:"ritsuko",mode:"ahead"}
function angel:cast/look {id:"misato",mode:"ahead"}
scoreboard players set #step angel.story 132
function angel:story/s4/e132
