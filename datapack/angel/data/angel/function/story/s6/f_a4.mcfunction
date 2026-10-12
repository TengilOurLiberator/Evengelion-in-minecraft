function angel:cast/remove_all
function angel:cast/gurney_remove
execute positioned 3094.5 54.0 76.5 rotated 180.0 0 run function angel:cast/summon {id:"misato"}
execute positioned 3098.5 54.0 76.5 rotated 180.0 0 run function angel:cast/summon {id:"ritsuko"}
execute positioned 3110.5 63.0 57.5 rotated 43.0 0 run function angel:cast/summon {id:"gendo"}
function angel:cast/look {id:"misato",mode:"player"}
function angel:cast/look {id:"ritsuko",mode:"player"}
function angel:cast/look {id:"gendo",mode:"player"}
function angel:story/launch/cage_lights_on
